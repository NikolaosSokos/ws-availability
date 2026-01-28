"""Test mergegaps parameter validation"""

import unittest
from apps.models import QueryParameters
from pydantic import ValidationError


class TestMergegapsValidation(unittest.TestCase):
    
    def test_mergegaps_zero_is_valid(self):
        """Test that mergegaps=0.0 is accepted"""
        qp = QueryParameters(mergegaps=0.0)
        self.assertEqual(qp.mergegaps, 0.0)
    
    def test_mergegaps_positive_is_valid(self):
        """Test that positive mergegaps values are accepted"""
        qp = QueryParameters(mergegaps=1.5)
        self.assertEqual(qp.mergegaps, 1.5)
    
    def test_mergegaps_negative_is_invalid(self):
        """Test that negative mergegaps values are rejected"""
        with self.assertRaises(ValidationError) as context:
            QueryParameters(mergegaps=-1.0)
        
        self.assertIn("mergegaps must be non-negative", str(context.exception))
    
    def test_mergegaps_none_is_valid(self):
        """Test that mergegaps=None (not specified) is valid"""
        qp = QueryParameters()
        self.assertIsNone(qp.mergegaps)


if __name__ == '__main__':
    unittest.main()
