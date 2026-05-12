"""Tests for the Sentry event-scrubbing logic in apps/sentry.py.

before_send() is a pure dict transformation, so it can be tested without
initializing the actual Sentry SDK. These tests lock down the GDPR/PII
guarantees so future edits cannot silently regress them.
"""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.sentry import before_send, init_sentry


class TestBeforeSendScrubbing(unittest.TestCase):
    def test_scrubs_password_in_request_data(self):
        event = {"request": {"data": {"password": "hunter2", "user": "alice"}}}
        result = before_send(event, hint={})
        self.assertEqual(result["request"]["data"]["password"], "[Filtered]")
        self.assertEqual(result["request"]["data"]["user"], "alice")

    def test_scrubs_nested_sensitive_keys(self):
        event = {"extra": {"config": {"api_key": "abc123", "host": "localhost"}}}
        result = before_send(event, hint={})
        self.assertEqual(result["extra"]["config"]["api_key"], "[Filtered]")
        self.assertEqual(result["extra"]["config"]["host"], "localhost")

    def test_scrubs_sensitive_keys_inside_lists(self):
        event = {"extra": {"items": [{"token": "tok-1"}, {"name": "x"}]}}
        result = before_send(event, hint={})
        self.assertEqual(result["extra"]["items"][0]["token"], "[Filtered]")
        self.assertEqual(result["extra"]["items"][1]["name"], "x")

    def test_scrubs_ip_headers(self):
        event = {"request": {"headers": {
            "X-Forwarded-For": "1.2.3.4",
            "x-real-ip": "5.6.7.8",
            "User-Agent": "pytest",
        }}}
        result = before_send(event, hint={})
        headers = result["request"]["headers"]
        self.assertEqual(headers["X-Forwarded-For"], "[Filtered]")
        self.assertEqual(headers["x-real-ip"], "[Filtered]")
        self.assertEqual(headers["User-Agent"], "pytest")

    def test_scrubs_remote_addr_from_env(self):
        event = {"request": {"env": {"REMOTE_ADDR": "1.2.3.4", "SERVER_NAME": "x"}}}
        result = before_send(event, hint={})
        self.assertEqual(result["request"]["env"]["REMOTE_ADDR"], "[Filtered]")
        self.assertEqual(result["request"]["env"]["SERVER_NAME"], "x")

    def test_user_ip_is_zeroed_even_if_user_missing(self):
        result = before_send({}, hint={})
        self.assertEqual(result["user"]["ip_address"], "0.0.0.0")

    def test_user_ip_is_zeroed_even_if_already_set(self):
        event = {"user": {"ip_address": "9.9.9.9", "id": "42"}}
        result = before_send(event, hint={})
        self.assertEqual(result["user"]["ip_address"], "0.0.0.0")
        self.assertEqual(result["user"]["id"], "42")

    def test_scrubs_breadcrumbs(self):
        event = {"breadcrumbs": {"values": [{"data": {"authorization": "Bearer x"}}]}}
        result = before_send(event, hint={})
        self.assertEqual(
            result["breadcrumbs"]["values"][0]["data"]["authorization"],
            "[Filtered]",
        )

    def test_scrubs_stacktrace_local_vars(self):
        event = {"exception": {"values": [{"stacktrace": {"frames": [
            {"vars": {"password": "secret", "x": 1}}
        ]}}]}}
        result = before_send(event, hint={})
        frame_vars = result["exception"]["values"][0]["stacktrace"]["frames"][0]["vars"]
        self.assertEqual(frame_vars["password"], "[Filtered]")
        self.assertEqual(frame_vars["x"], 1)


class TestInitSentry(unittest.TestCase):
    def test_no_init_when_dsn_empty(self):
        with patch("apps.sentry.Config") as mock_config, \
             patch("apps.sentry.sentry_sdk.init") as mock_init:
            mock_config.SENTRY_DSN = ""
            init_sentry()
            mock_init.assert_not_called()

    def test_init_passes_environment_when_set(self):
        with patch("apps.sentry.Config") as mock_config, \
             patch("apps.sentry.sentry_sdk.init") as mock_init:
            mock_config.SENTRY_DSN = "https://example@sentry.io/1"
            mock_config.SENTRY_TRACES_SAMPLE_RATE = 0.5
            mock_config.SENTRY_ENVIRONMENT = "noa"
            init_sentry()
            mock_init.assert_called_once()
            kwargs = mock_init.call_args.kwargs
            self.assertEqual(kwargs["environment"], "noa")
            self.assertEqual(kwargs["traces_sample_rate"], 0.5)
            self.assertFalse(kwargs["send_default_pii"])
            self.assertTrue(kwargs["enable_tracing"])

    def test_init_tolerates_missing_environment_attr(self):
        """Old configs without SENTRY_ENVIRONMENT should not crash init."""
        class _LegacyConfig:
            SENTRY_DSN = "https://example@sentry.io/1"
            SENTRY_TRACES_SAMPLE_RATE = 1.0
            # SENTRY_ENVIRONMENT intentionally absent

        with patch("apps.sentry.Config", _LegacyConfig), \
             patch("apps.sentry.sentry_sdk.init") as mock_init:
            init_sentry()
            mock_init.assert_called_once()
            self.assertIsNone(mock_init.call_args.kwargs["environment"])


if __name__ == "__main__":
    unittest.main()
