"""Tests for apps/parameters.py (the legacy default-parameters dict)."""
import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.parameters import Parameters


class TestParameters(unittest.TestCase):
    def test_defaults_match_expected_wildcards(self):
        p = Parameters().todict()
        self.assertEqual(p["net"], "*")
        self.assertEqual(p["sta"], "*")
        self.assertEqual(p["loc"], "*")
        self.assertEqual(p["cha"], "*")
        self.assertEqual(p["quality"], "*")
        self.assertEqual(p["format"], "text")
        self.assertEqual(p["nodata"], "204")
        self.assertEqual(p["includerestricted"], "false")
        self.assertIsNone(p["start"])
        self.assertIsNone(p["end"])

    def test_constraints_define_known_aliases(self):
        p = Parameters().todict()
        alias_keys = {pair[0] for pair in p["constraints"]["alias"]}
        self.assertEqual(
            alias_keys,
            {"network", "station", "location", "channel", "starttime", "endtime"},
        )
        self.assertIn("includerestricted", p["constraints"]["booleans"])

    def test_todict_returns_full_dict_with_all_fields(self):
        p = Parameters().todict()
        for required in ["net", "sta", "loc", "cha", "start", "end",
                         "quality", "merge", "orderby", "limit",
                         "includerestricted", "format", "nodata", "constraints"]:
            self.assertIn(required, p)


if __name__ == "__main__":
    unittest.main()
