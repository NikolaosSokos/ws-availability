"""Tests for the in-app scheduler jobs in apps/scheduler.py.

The @sentry_sdk.monitor decorator and APScheduler wiring are integration
concerns; here we only verify the job bodies themselves: they call the
right collaborators, log on success, and re-raise on failure (so Sentry
Cron monitors register an ERROR check-in).
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps import scheduler


class TestRunInventoryCache(unittest.TestCase):
    def test_builds_cache_on_happy_path(self):
        with patch("apps.scheduler.Cache") as mock_cache_cls:
            mock_cache = mock_cache_cls.return_value
            scheduler.run_inventory_cache()
            mock_cache.build_cache.assert_called_once()

    def test_reraises_and_reports_on_failure(self):
        with patch("apps.scheduler.Cache") as mock_cache_cls, \
             patch("apps.scheduler.sentry_sdk.capture_exception") as mock_capture:
            mock_cache_cls.return_value.build_cache.side_effect = RuntimeError("boom")

            with self.assertRaises(RuntimeError):
                scheduler.run_inventory_cache()

            mock_capture.assert_called_once()


class TestRunMaterializedViewUpdate(unittest.TestCase):
    def test_runs_updater_on_happy_path(self):
        with patch("apps.scheduler.get_db_client") as mock_get_client, \
             patch("apps.scheduler.AvailabilityUpdater") as mock_updater_cls, \
             patch.dict(os.environ, {"MONGODB_NAME": "wfrepo"}, clear=False):
            mock_db = MagicMock()
            mock_get_client.return_value.get_database.return_value = mock_db
            mock_updater = mock_updater_cls.return_value

            scheduler.run_materialized_view_update()

            mock_get_client.return_value.get_database.assert_called_once_with("wfrepo")
            mock_updater_cls.assert_called_once_with(mock_db)
            mock_updater.run_updates.assert_called_once()

    def test_reraises_and_reports_on_failure(self):
        with patch("apps.scheduler.get_db_client") as mock_get_client, \
             patch("apps.scheduler.AvailabilityUpdater") as mock_updater_cls, \
             patch("apps.scheduler.sentry_sdk.capture_exception") as mock_capture:
            mock_get_client.return_value.get_database.return_value = MagicMock()
            mock_updater_cls.return_value.run_updates.side_effect = RuntimeError("kaboom")

            with self.assertRaises(RuntimeError):
                scheduler.run_materialized_view_update()

            mock_capture.assert_called_once()


if __name__ == "__main__":
    unittest.main()
