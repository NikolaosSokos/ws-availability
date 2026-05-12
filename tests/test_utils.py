"""Tests for apps/utils.py — validators and helpers."""
import os
import sys
import unittest
from datetime import datetime

from flask import Flask

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps import utils
from apps.parameters import Parameters


class TestSimpleValidators(unittest.TestCase):
    def test_is_valid_integer_bounds(self):
        self.assertTrue(utils.is_valid_integer("5"))
        self.assertTrue(utils.is_valid_integer(5, mini=1, maxi=10))
        self.assertFalse(utils.is_valid_integer("notanint"))
        self.assertFalse(utils.is_valid_integer(-1))
        self.assertFalse(utils.is_valid_integer(11, maxi=10))

    def test_is_valid_float_bounds(self):
        self.assertTrue(utils.is_valid_float("1.5"))
        self.assertFalse(utils.is_valid_float("nan-no-no"))
        self.assertFalse(utils.is_valid_float(-1.0))

    def test_is_valid_datetime_formats(self):
        self.assertIsNotNone(utils.is_valid_datetime("2023-01-01"))
        self.assertIsNotNone(utils.is_valid_datetime("2023-01-01T00:00:00"))
        self.assertIsNotNone(utils.is_valid_datetime("2023-01-01T00:00:00.000"))
        self.assertIsNotNone(utils.is_valid_datetime("2023-01-01T00:00:00Z"))
        self.assertIsNone(utils.is_valid_datetime("not-a-date"))

    def test_is_valid_starttime_accepts_currentutcday(self):
        self.assertTrue(utils.is_valid_starttime("currentutcday"))
        self.assertTrue(utils.is_valid_starttime("2023-01-01"))
        self.assertFalse(utils.is_valid_starttime("bad"))

    def test_is_valid_endtime_accepts_integer_offset(self):
        self.assertTrue(utils.is_valid_endtime("3600"))
        self.assertTrue(utils.is_valid_endtime("currentutcday"))

    def test_is_valid_network_station_location_channel(self):
        self.assertTrue(utils.is_valid_network("NL"))
        self.assertFalse(utils.is_valid_network("TOOLONG"))
        self.assertTrue(utils.is_valid_station("HGN"))
        self.assertFalse(utils.is_valid_station(""))
        self.assertTrue(utils.is_valid_location("--"))
        self.assertTrue(utils.is_valid_channel("BHZ"))
        self.assertFalse(utils.is_valid_channel("TOOLONG"))

    def test_is_valid_bool_string(self):
        self.assertTrue(utils.is_valid_bool_string("true"))
        self.assertTrue(utils.is_valid_bool_string("FALSE"))
        self.assertFalse(utils.is_valid_bool_string(None))
        self.assertFalse(utils.is_valid_bool_string("maybe"))

    def test_is_valid_output_quality_orderby_show_merge_nodata(self):
        self.assertTrue(utils.is_valid_output("json"))
        self.assertFalse(utils.is_valid_output("xml"))
        self.assertTrue(utils.is_valid_quality("D"))
        self.assertFalse(utils.is_valid_quality("X"))
        self.assertTrue(utils.is_valid_merge("quality"))
        self.assertFalse(utils.is_valid_merge("bogus"))
        self.assertTrue(utils.is_valid_nodata("204"))
        self.assertFalse(utils.is_valid_nodata("500"))

    def test_currentutcday_is_midnight(self):
        dt = utils.currentutcday()
        self.assertEqual(dt.hour, 0)
        self.assertEqual(dt.minute, 0)
        self.assertEqual(dt.second, 0)

    def test_tictac_returns_elapsed_seconds(self):
        import time
        tic = time.time()
        elapsed = utils.tictac(tic)
        self.assertIsInstance(elapsed, float)
        self.assertGreaterEqual(elapsed, 0.0)


class TestCheckBaseParameters(unittest.TestCase):
    def _base(self, **overrides):
        # check_base_parameters reads params["network"|"station"|"location"|"channel"]
        # which are None by default — in production check_request() aliases them
        # from net/sta/loc/cha. For unit-testing the validator alone we pre-seed
        # them with wildcards so the helper exercises the validation, not None-handling.
        params = Parameters().todict()
        params["network"] = "*"
        params["station"] = "*"
        params["location"] = "*"
        params["channel"] = "*"
        params.update(overrides)
        return params

    def test_accepts_valid_params(self):
        params = self._base(network="NL", station="HGN", channel="BHZ")
        _, result = utils.check_base_parameters(params)
        self.assertEqual(result["code"], 200)

    def test_rejects_invalid_network(self):
        params = self._base(network="TOOLONG", station="HGN", channel="BHZ")
        _, result = utils.check_base_parameters(params)
        self.assertEqual(result["code"], 400)

    def test_rejects_start_after_end(self):
        params = self._base(
            network="NL", station="HGN", channel="BHZ",
            start="2023-02-01", end="2023-01-01",
        )
        _, result = utils.check_base_parameters(params)
        self.assertEqual(result["code"], 400)

    def test_rejects_empty_selection(self):
        params = self._base()  # all wildcards
        _, result = utils.check_base_parameters(params)
        self.assertEqual(result["code"], 400)

    def test_rejects_duration_exceeding_max_days(self):
        params = self._base(
            network="NL", station="HGN", channel="BHZ",
            start="2023-01-01", end="2023-12-31",
        )
        _, result = utils.check_base_parameters(params, max_days=30)
        self.assertEqual(result["code"], 400)

    def test_temporary_network_expands_to_wildcards(self):
        params = self._base(network="temporary", station="HGN", channel="BHZ")
        params, result = utils.check_base_parameters(params)
        self.assertEqual(result["code"], 200)
        self.assertIn("0?", params["network"])

    def test_rejects_invalid_bool_string(self):
        params = self._base(network="NL", station="HGN", channel="BHZ",
                            includerestricted="maybe")
        _, result = utils.check_base_parameters(params)
        self.assertEqual(result["code"], 400)


class TestErrorResponses(unittest.TestCase):
    """error_request needs a Flask request context to access request.full_path."""

    def setUp(self):
        self.app = Flask(__name__)
        self.ctx = self.app.test_request_context("/query?foo=bar")
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_error_request_returns_response_with_status(self):
        resp = utils.error_request(msg="Bad", details="details", code=400)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Bad", resp.get_data(as_text=True))

    def test_overflow_error_returns_413(self):
        resp = utils.overflow_error("too big")
        self.assertEqual(resp.status_code, 413)

    def test_error_500_returns_500(self):
        resp = utils.error_500("boom")
        self.assertEqual(resp.status_code, 500)


if __name__ == "__main__":
    unittest.main()
