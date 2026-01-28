"""
Test for segment fragmentation issue.

This test simulates the scenario where multiple overlapping/adjacent segments
are returned for the same channel without merge parameters.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps import data_access_layer as dal

class TestSegmentFragmentation(unittest.TestCase):
    
    def setUp(self):
        self.base_params = {
            "format": "text",
            "merge": "",
            "mergegaps": None,
            "extent": False,
            "showlastupdate": False,
            "orderby": "nslc_time_quality_samplerate",
            "start": None,
            "end": None,
            "limit": 1000
        }
        self.now = datetime.utcnow()
    
    def test_overlapping_segments_without_merge(self):
        """
        Test that overlapping segments are returned as-is when no merge parameter is specified.
        This simulates the ORFEUS output issue.
        """
        params = self.base_params.copy()
        
        # Create 6 overlapping/adjacent segments like in the ORFEUS example
        # NL.BHAR..HGN with overlapping time ranges
        t1 = datetime(2020, 6, 5, 0, 0, 0)
        t2 = datetime(2020, 6, 5, 17, 26, 59, 5000)
        t3 = datetime(2020, 6, 5, 17, 26, 59, 0)  # Overlaps with t2
        t4 = datetime(2020, 6, 5, 17, 32, 9, 5000)
        t5 = datetime(2020, 6, 5, 17, 32, 9, 0)  # Overlaps with t4
        t6 = datetime(2020, 6, 5, 18, 1, 58, 990000)
        t7 = datetime(2020, 6, 5, 18, 1, 59, 0)  # Adjacent to t6
        t8 = datetime(2020, 6, 6, 0, 0, 0)
        t9 = datetime(2020, 6, 6, 0, 0, 0)  # Continuous
        t10 = datetime(2020, 6, 7, 0, 0, 0)
        t11 = datetime(2020, 6, 7, 0, 0, 0)  # Continuous
        t12 = datetime(2020, 6, 7, 0, 2, 0)
        
        # Create 6 segments
        segments = [
            ["NL", "BHAR", "", "HGN", "D", 200.0, t1, t2, self.now, "OPEN", 100],
            ["NL", "BHAR", "", "HGN", "D", 200.0, t3, t4, self.now, "OPEN", 100],
            ["NL", "BHAR", "", "HGN", "D", 200.0, t5, t6, self.now, "OPEN", 100],
            ["NL", "BHAR", "", "HGN", "D", 200.0, t7, t8, self.now, "OPEN", 100],
            ["NL", "BHAR", "", "HGN", "D", 200.0, t9, t10, self.now, "OPEN", 100],
            ["NL", "BHAR", "", "HGN", "D", 200.0, t11, t12, self.now, "OPEN", 100],
        ]
        
        # Without merge, all 6 segments should be returned
        indexes = [0, 1, 2, 3, 4, 5]  # NSLC + Quality + SampleRate
        
        # Convert to string format (simulating select_columns)
        data_str = []
        for row in segments:
            str_row = [
                row[0], row[1], row[2], row[3], row[4], str(row[5]),
                row[6].isoformat(timespec="microseconds") + "Z",
                row[7].isoformat(timespec="microseconds") + "Z"
            ]
            data_str.append(str_row)
        
        # Generate text output
        text_output = dal.records_to_text(params, data_str)
        
        print("\n" + "="*80)
        print("OUTPUT WITHOUT MERGE PARAMETER:")
        print("="*80)
        print(text_output)
        print("="*80)
        
        # Count number of data rows (excluding header)
        lines = text_output.strip().split('\n')
        data_lines = [l for l in lines if not l.startswith('#')]
        
        print(f"\nNumber of segments returned: {len(data_lines)}")
        print(f"Expected: 6 segments (no merging without merge parameter)")
        
        # Without merge parameter, all 6 segments should be present
        self.assertEqual(len(data_lines), 6, 
                        "Without merge parameter, all segments should be returned as-is")
    
    def test_overlapping_segments_with_merge_overlap(self):
        """
        Test that overlapping segments ARE merged when merge=overlap is specified.
        """
        params = self.base_params.copy()
        params["merge"] = "overlap"
        
        # Same segments as above
        t1 = datetime(2020, 6, 5, 0, 0, 0)
        t2 = datetime(2020, 6, 5, 17, 26, 59, 5000)
        t3 = datetime(2020, 6, 5, 17, 26, 59, 0)
        t4 = datetime(2020, 6, 5, 17, 32, 9, 5000)
        t5 = datetime(2020, 6, 5, 17, 32, 9, 0)
        t6 = datetime(2020, 6, 5, 18, 1, 58, 990000)
        t7 = datetime(2020, 6, 5, 18, 1, 59, 0)
        t8 = datetime(2020, 6, 6, 0, 0, 0)
        t9 = datetime(2020, 6, 6, 0, 0, 0)
        t10 = datetime(2020, 6, 7, 0, 0, 0)
        t11 = datetime(2020, 6, 7, 0, 0, 0)
        t12 = datetime(2020, 6, 7, 0, 2, 0)
        
        segments = [
            ["NL", "BHAR", "", "HGN", "D", 200.0, t1, t2, self.now, "OPEN", 100],
            ["NL", "BHAR", "", "HGN", "D", 200.0, t3, t4, self.now, "OPEN", 100],
            ["NL", "BHAR", "", "HGN", "D", 200.0, t5, t6, self.now, "OPEN", 100],
            ["NL", "BHAR", "", "HGN", "D", 200.0, t7, t8, self.now, "OPEN", 100],
            ["NL", "BHAR", "", "HGN", "D", 200.0, t9, t10, self.now, "OPEN", 100],
            ["NL", "BHAR", "", "HGN", "D", 200.0, t11, t12, self.now, "OPEN", 100],
        ]
        
        indexes = [0, 1, 2, 3, 4, 5]
        
        # Apply fusion (merge)
        merged = dal.fusion(params, segments, indexes)
        
        print("\n" + "="*80)
        print("OUTPUT WITH merge=overlap:")
        print("="*80)
        print(f"Original segments: {len(segments)}")
        print(f"Merged segments: {len(merged)}")
        print("="*80)
        
        # With merge=overlap, overlapping segments should be combined
        # Expected: significantly fewer than 6 segments
        self.assertLess(len(merged), 6, 
                       "With merge=overlap, overlapping segments should be merged")
        
        # Ideally should be 1 segment covering the entire time range
        if len(merged) == 1:
            print("✅ All segments merged into 1 continuous span")
            self.assertEqual(merged[0][6], t1, "Start time should be earliest")
            self.assertEqual(merged[0][7], t12, "End time should be latest")
        else:
            print(f"⚠️  Merged into {len(merged)} segments (expected 1)")


if __name__ == '__main__':
    unittest.main(verbosity=2)
