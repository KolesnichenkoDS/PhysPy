from unittest import TestCase

import physpy

class TestNamedValue(TestCase):
    def test_one_value_approx(self):
        '''calculate an approximate value for one measurement'''
        x = physpy.value('x', [42], 0)
        self.assertEqual(x.approx(), 42)
        
    def test_ten_values_approx(self):
        '''calculate an approximate value for ten measurements'''
        x = physpy.value('x', [
            3, 4, 3, 4, 3, 4, 3, 4, 3, 4
        ], 0)
        self.assertEqual(x.approx(), 3.5)