# Tests/test_calculations.py
import unittest
import math
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from calculations import (
    calculate_conduit_cross_sectional_area,
    _get_effective_cable_radius, # Can test this helper if needed
    calculate_cable_cross_sectional_area,
    calculate_total_cable_area,
    calculate_conduit_fill_percentage,
    get_as_nzs_max_fill_percentage,
    check_as_nzs_compliance,
    AS_NZS_MAX_FILL_ONE_CABLE, # Import constants for verifying limits
    AS_NZS_MAX_FILL_TWO_CABLES,
    AS_NZS_MAX_FILL_THREE_OR_MORE_CABLES
)
from config import CableType, CORE_RADIUS, SHEATH_THICKNESS, MARGIN # Assuming these are needed

class TestCalculations(unittest.TestCase):
    def test_conduit_area(self):
        self.assertAlmostEqual(calculate_conduit_cross_sectional_area(50), math.pi * 50**2)

    def test_single_core_effective_radius(self):
        # Using example values directly for clarity
        cr, st, m = 10, 2, 1 
        expected_radius = cr + st + m
        self.assertAlmostEqual(_get_effective_cable_radius(CableType.SINGLE, cr, st, m), expected_radius)

    def test_single_core_area(self):
        cr, st, m = CORE_RADIUS, SHEATH_THICKNESS, MARGIN # Use config values
        eff_radius = _get_effective_cable_radius(CableType.SINGLE, cr, st, m)
        self.assertAlmostEqual(calculate_cable_cross_sectional_area(CableType.SINGLE, cr, st, m), math.pi * eff_radius**2)
        
    # Add similar detailed tests for THREE_CORE and FOUR_CORE effective radius and area
    # Example for THREE_CORE effective radius:
    def test_three_core_effective_radius(self):
        cr, st, m = 10, 2, 1
        core_center_dist = (2 * cr) / math.sqrt(3)
        expected_radius = core_center_dist + cr + st + m
        self.assertAlmostEqual(_get_effective_cable_radius(CableType.THREE_CORE, cr, st, m), expected_radius)

    def test_four_core_effective_radius(self):
        cr, st, m = 10, 2, 1
        core_center_dist = math.sqrt(2) * cr
        expected_radius = core_center_dist + cr + st + m
        self.assertAlmostEqual(_get_effective_cable_radius(CableType.FOUR_CORE, cr, st, m), expected_radius)

    def test_three_core_area(self):
        cr, st, m = CORE_RADIUS, SHEATH_THICKNESS, MARGIN
        eff_radius = _get_effective_cable_radius(CableType.THREE_CORE, cr, st, m)
        self.assertAlmostEqual(calculate_cable_cross_sectional_area(CableType.THREE_CORE, cr, st, m), math.pi * eff_radius**2)

    def test_four_core_area(self):
        cr, st, m = CORE_RADIUS, SHEATH_THICKNESS, MARGIN
        eff_radius = _get_effective_cable_radius(CableType.FOUR_CORE, cr, st, m)
        self.assertAlmostEqual(calculate_cable_cross_sectional_area(CableType.FOUR_CORE, cr, st, m), math.pi * eff_radius**2)


    def test_total_cable_area(self):
        cr, st, m = CORE_RADIUS, SHEATH_THICKNESS, MARGIN
        cables = [
            (CableType.SINGLE, cr, st, m),
            (CableType.THREE_CORE, cr, st, m)
        ]
        area1 = calculate_cable_cross_sectional_area(CableType.SINGLE, cr, st, m)
        area2 = calculate_cable_cross_sectional_area(CableType.THREE_CORE, cr, st, m)
        self.assertAlmostEqual(calculate_total_cable_area(cables), area1 + area2)

    def test_fill_percentage(self):
        self.assertAlmostEqual(calculate_conduit_fill_percentage(100, 1000), 10.0)
        self.assertAlmostEqual(calculate_conduit_fill_percentage(0, 1000), 0.0)
        self.assertAlmostEqual(calculate_conduit_fill_percentage(100, 0), 0.0) # Avoid division by zero

    def test_get_as_nzs_limits(self):
        self.assertEqual(get_as_nzs_max_fill_percentage(0), 100.0) # Or other defined behavior for 0 cables
        self.assertEqual(get_as_nzs_max_fill_percentage(1), AS_NZS_MAX_FILL_ONE_CABLE)
        self.assertEqual(get_as_nzs_max_fill_percentage(2), AS_NZS_MAX_FILL_TWO_CABLES)
        self.assertEqual(get_as_nzs_max_fill_percentage(3), AS_NZS_MAX_FILL_THREE_OR_MORE_CABLES)
        self.assertEqual(get_as_nzs_max_fill_percentage(10), AS_NZS_MAX_FILL_THREE_OR_MORE_CABLES)

    def test_check_as_nzs_compliance(self):
        # Compliant scenarios
        self.assertTrue(check_as_nzs_compliance(20.0, 1)[0]) # 20% < 53%
        self.assertTrue(check_as_nzs_compliance(20.0, 2)[0]) # 20% < 31%
        self.assertTrue(check_as_nzs_compliance(30.0, 3)[0]) # 30% < 40%
        
        # Non-compliant scenarios
        self.assertFalse(check_as_nzs_compliance(60.0, 1)[0]) # 60% > 53%
        self.assertFalse(check_as_nzs_compliance(35.0, 2)[0]) # 35% > 31%
        self.assertFalse(check_as_nzs_compliance(45.0, 3)[0]) # 45% > 40%

        # Check returned limit value
        self.assertEqual(check_as_nzs_compliance(20.0, 1)[1], AS_NZS_MAX_FILL_ONE_CABLE)

if __name__ == '__main__':
    unittest.main()
