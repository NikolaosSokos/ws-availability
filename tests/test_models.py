"""Tests for apps/models.py — Pydantic QueryParameters validation."""
import os
import sys
import unittest
from datetime import datetime

from pydantic import ValidationError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.models import QueryParameters


class TestQueryParametersValidation(unittest.TestCase):
    def test_accepts_minimal_input_with_defaults(self):
        qp = QueryParameters(network="NL", station="HGN", channel="BHZ")
        self.assertEqual(qp.network, "NL")
        self.assertEqual(qp.quality, "*")
        self.assertEqual(qp.format, "text")
        self.assertEqual(qp.nodata, "204")
        self.assertFalse(qp.includerestricted)

    def test_accepts_alias_short_names(self):
        qp = QueryParameters(net="NL", sta="HGN")
        self.assertEqual(qp.network, "NL")
        self.assertEqual(qp.station, "HGN")

    def test_rejects_invalid_network_code(self):
        with self.assertRaises(ValidationError):
            QueryParameters(network="TOO_LONG")

    def test_rejects_invalid_station_code(self):
        with self.assertRaises(ValidationError):
            QueryParameters(station="TOOLONGSTATION")

    def test_rejects_invalid_channel_code(self):
        with self.assertRaises(ValidationError):
            QueryParameters(channel="TOOLONG")

    def test_rejects_invalid_quality_code(self):
        with self.assertRaises(ValidationError):
            QueryParameters(quality="X")

    def test_accepts_comma_separated_networks(self):
        qp = QueryParameters(network="NL,BE,GR")
        self.assertEqual(qp.network, "NL,BE,GR")

    def test_includerestricted_accepts_string_true(self):
        qp = QueryParameters(includerestricted="true")
        self.assertTrue(qp.includerestricted)

    def test_includerestricted_accepts_string_false(self):
        qp = QueryParameters(includerestricted="false")
        self.assertFalse(qp.includerestricted)

    def test_includerestricted_rejects_garbage(self):
        with self.assertRaises(ValidationError):
            QueryParameters(includerestricted="maybe")

    def test_format_normalizes_to_lowercase(self):
        qp = QueryParameters(format="JSON")
        self.assertEqual(qp.format, "json")

    def test_format_rejects_unknown(self):
        with self.assertRaises(ValidationError):
            QueryParameters(format="xml")

    def test_nodata_rejects_unknown_code(self):
        with self.assertRaises(ValidationError):
            QueryParameters(nodata="500")

    def test_merge_accepts_known_values(self):
        qp = QueryParameters(merge="quality,samplerate")
        self.assertEqual(qp.merge, "quality,samplerate")

    def test_merge_rejects_unknown_value(self):
        with self.assertRaises(ValidationError):
            QueryParameters(merge="bogus")

    def test_orderby_rejects_unknown(self):
        with self.assertRaises(ValidationError):
            QueryParameters(orderby="not_a_field")

    def test_limit_rejects_negative(self):
        with self.assertRaises(ValidationError):
            QueryParameters(limit=-1)

    def test_starttime_accepts_iso_format(self):
        qp = QueryParameters(starttime="2023-01-01T00:00:00")
        self.assertEqual(qp.starttime, "2023-01-01T00:00:00")

    def test_starttime_accepts_currentutcday(self):
        qp = QueryParameters(starttime="currentutcday")
        self.assertEqual(qp.starttime, "currentutcday")

    def test_starttime_accepts_datetime_instance(self):
        dt = datetime(2023, 1, 1)
        qp = QueryParameters(starttime=dt)
        self.assertEqual(qp.starttime, dt)

    def test_starttime_rejects_garbage_string(self):
        with self.assertRaises(ValidationError):
            QueryParameters(starttime="not-a-date")

    def test_mergegaps_accepts_positive(self):
        qp = QueryParameters(mergegaps=10.0)
        self.assertEqual(qp.mergegaps, 10.0)

    def test_mergegaps_rejects_zero_or_negative(self):
        with self.assertRaises(ValidationError):
            QueryParameters(mergegaps=0.0)


if __name__ == "__main__":
    unittest.main()
