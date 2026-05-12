"""Tests for apps/root.py — Flask request handlers and parameter orchestration."""
import importlib.metadata
import os
import sys
import unittest
from unittest.mock import patch

import werkzeug
# Flask 2.3.x test_client reads werkzeug.__version__; werkzeug>=3.1 removed it.
# Restore the attribute so test_client() works without pinning either dep.
if not hasattr(werkzeug, "__version__"):
    werkzeug.__version__ = importlib.metadata.version("werkzeug")

from flask import Flask

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps import root
from apps.parameters import Parameters


def _make_app():
    """Minimal Flask app wired to root.output() at the two production routes."""
    app = Flask(__name__)
    app.add_url_rule("/query", view_func=root.output, methods=["GET", "POST"])
    app.add_url_rule("/extent", view_func=root.output, methods=["GET", "POST"])
    return app


class TestCheckParameters(unittest.TestCase):
    """check_parameters() is the validation core — no Flask context needed
    because check_base_parameters reads params dict, not request.args."""

    def _base(self, **overrides):
        # In production check_request() aliases net→network etc. before
        # check_parameters() runs; the validator itself requires non-None values.
        params = Parameters().todict()
        params["network"] = "*"
        params["station"] = "*"
        params["location"] = "*"
        params["channel"] = "*"
        params["base_url"] = "http://localhost/query"
        params.update(overrides)
        return params

    def test_accepts_valid_params_and_normalizes(self):
        params = self._base(network="NL", station="HGN", channel="BHZ",
                            start="2023-01-01", end="2023-01-02")
        out, result = root.check_parameters(params)
        self.assertEqual(result["code"], 200)
        # merge is normalized from "" to []
        self.assertEqual(out["merge"], [])
        # limit defaults to settings.max_data_rows when not set
        self.assertIsNotNone(out["limit"])

    def test_extent_flag_set_for_extent_url(self):
        params = self._base(network="NL", station="HGN", channel="BHZ")
        params["base_url"] = "http://localhost/extent"
        out, result = root.check_parameters(params)
        self.assertEqual(result["code"], 200)
        self.assertTrue(out["extent"])
        self.assertTrue(out["showlastupdate"])

    def test_invalid_network_returns_400(self):
        params = self._base(network="TOOLONG", station="HGN", channel="BHZ")
        _, result = root.check_parameters(params)
        self.assertEqual(result["code"], 400)

    def test_mergegaps_with_extent_is_rejected(self):
        params = self._base(network="NL", station="HGN", channel="BHZ",
                            mergegaps=10.0)
        params["base_url"] = "http://localhost/extent"
        _, result = root.check_parameters(params)
        self.assertEqual(result["code"], 400)

    def test_merge_string_is_split_to_list(self):
        params = self._base(network="NL", station="HGN", channel="BHZ",
                            merge="quality,samplerate")
        out, result = root.check_parameters(params)
        self.assertEqual(result["code"], 200)
        self.assertEqual(out["merge"], ["quality", "samplerate"])

    def test_show_latestupdate_sets_showlastupdate_flag(self):
        params = self._base(network="NL", station="HGN", channel="BHZ",
                            show="latestupdate")
        out, result = root.check_parameters(params)
        self.assertEqual(result["code"], 200)
        self.assertTrue(out["showlastupdate"])


class TestGetEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.client = self.app.test_client()

    def test_get_returns_400_on_bad_params(self):
        # Empty selection: all wildcards
        resp = self.client.get("/query")
        self.assertEqual(resp.status_code, 400)

    def test_get_with_unknown_param_returns_400(self):
        resp = self.client.get("/query?network=NL&station=HGN&channel=BHZ&bogus=1")
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"bogus", resp.data)

    def test_get_with_valid_params_calls_get_output(self):
        with patch("apps.root.get_output") as mock_get_output:
            mock_get_output.return_value = "OK-RESPONSE"
            resp = self.client.get(
                "/query?network=NL&station=HGN&channel=BHZ"
                "&start=2023-01-01&end=2023-01-02"
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.get_data(as_text=True), "OK-RESPONSE")
            mock_get_output.assert_called_once()

    def test_get_returns_500_when_get_output_raises(self):
        with patch("apps.root.get_output", side_effect=RuntimeError("boom")):
            resp = self.client.get(
                "/query?network=NL&station=HGN&channel=BHZ"
                "&start=2023-01-01&end=2023-01-02"
            )
            self.assertEqual(resp.status_code, 500)

    def test_get_returns_500_when_get_output_returns_falsy(self):
        with patch("apps.root.get_output", return_value=None):
            resp = self.client.get(
                "/query?network=NL&station=HGN&channel=BHZ"
                "&start=2023-01-01&end=2023-01-02"
            )
            self.assertEqual(resp.status_code, 500)


class TestPostEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = _make_app()
        self.client = self.app.test_client()

    def test_post_parses_body_and_calls_get_output(self):
        body = "NL HGN -- BHZ 2023-01-01T00:00:00 2023-01-02T00:00:00\n"
        with patch("apps.root.get_output") as mock_get_output:
            mock_get_output.return_value = "OK"
            resp = self.client.post("/query", data=body, content_type="text/plain")
            self.assertEqual(resp.status_code, 200)
            mock_get_output.assert_called_once()
            paramslist = mock_get_output.call_args[0][0]
            # Body was parsed and at least one valid paramset reached get_output
            self.assertEqual(len(paramslist), 1)
            self.assertIn("start", paramslist[0])
            self.assertIn("end", paramslist[0])

    def test_post_with_key_value_pairs_picks_them_up(self):
        body = (
            "format=json\n"
            "NL HGN -- BHZ 2023-01-01T00:00:00 2023-01-02T00:00:00\n"
        )
        with patch("apps.root.get_output") as mock_get_output:
            mock_get_output.return_value = "OK"
            resp = self.client.post("/query", data=body, content_type="text/plain")
            self.assertEqual(resp.status_code, 200)
            paramslist = mock_get_output.call_args[0][0]
            self.assertEqual(paramslist[0]["format"], "json")

    def test_post_with_empty_body_returns_400(self):
        resp = self.client.post("/query", data="", content_type="text/plain")
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
