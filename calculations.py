# calculations.py
"""
Provides functions for calculating conduit and cable properties,
including cross-sectional areas, conduit fill percentages, and
checking compliance with simplified AS/NZS 3000 standards.
"""
import math
from enum import Enum # Assuming CableType Enum will be accessible or redefined here
from config import CORE_RADIUS, SHEATH_THICKNESS, MARGIN, CableType # Import necessary constants and Enum

# AS/NZS 3000 General Conduit Fill Limits (Simplified for this simulation)
# These are common interpretations/examples and may not reflect all specific scenarios
# or the latest revisions of the standard. For precise engineering compliance,
# the full AS/NZS 3000 standard, including all relevant amendments and clauses,
# must be consulted.
AS_NZS_MAX_FILL_ONE_CABLE = 53.0  # % Max fill for a single cable.
AS_NZS_MAX_FILL_TWO_CABLES = 31.0  # % Max total fill for two cables.
AS_NZS_MAX_FILL_THREE_OR_MORE_CABLES = 40.0  # % Max total fill for three or more cables.

def calculate_conduit_cross_sectional_area(conduit_radius: float) -> float:
    """
    Calculates the internal cross-sectional area of a circular conduit.

    Args:
        conduit_radius (float): The internal radius of the conduit.

    Returns:
        float: The cross-sectional area of the conduit.
    """
    return math.pi * (conduit_radius ** 2)

def _get_effective_cable_radius(cable_type: CableType, core_radius: float, sheath_thickness: float, margin: float) -> float:
    """
    Calculates the effective radius of a cable, including its cores, sheath, and an additional margin.
    This effective radius represents the overall space the cable is considered to occupy within the conduit.
    The calculation logic is derived from how cable dimensions are determined in `cable.py` 
    (specifically, the `calculate_cable_radius` function there, which determines the bounding circle).

    Args:
        cable_type (CableType): The type of the cable (e.g., SINGLE, THREE_CORE).
        core_radius (float): The radius of a single core within the cable.
        sheath_thickness (float): The thickness of the cable's outer sheath.
        margin (float): An additional margin around the cable for spacing or clearance.

    Returns:
        float: The effective radius of the cable.

    Raises:
        ValueError: If an unknown cable_type is provided.
    """
    if cable_type == CableType.SINGLE:
        # For a single core cable, radius is core + sheath + margin.
        return core_radius + sheath_thickness + margin
    elif cable_type == CableType.THREE_CORE:
        # For three cores arranged in a trefoil (triangular) formation,
        # the distance from the cable's geometric center to the center of each core is calculated.
        # This calculation is based on the geometry of an equilateral triangle formed by the core centers.
        # The term (2 * core_radius) / math.sqrt(3) is equivalent to core_radius / (math.sqrt(3)/2),
        # which is core_radius / sin(60deg), representing the circumradius of the triangle of cores if they were points.
        # Or, more accurately, it's the distance from the center to one core's center.
        core_center_distance = (2 * core_radius) / math.sqrt(3) # Distance from cable center to each core's center
        return core_center_distance + core_radius + sheath_thickness + margin
    elif cable_type == CableType.FOUR_CORE:
        # For four cores, typically arranged in a square or quad formation,
        # the distance from the cable's geometric center to the center of each core is calculated.
        # This assumes cores are at the corners of a square centered at the origin.
        # The distance to each core center is core_radius * sqrt(2).
        core_center_distance = math.sqrt(2) * core_radius # Distance from cable center to each core's center
        return core_center_distance + core_radius + sheath_thickness + margin
    else:
        raise ValueError(f"Unknown cable type: {cable_type}")

def calculate_cable_cross_sectional_area(cable_type: CableType, core_radius: float, sheath_thickness: float, margin: float) -> float:
    """
    Calculates the effective cross-sectional area of a single cable, based on its type,
    dimensions, and the defined margin. This area represents the space the cable
    is considered to occupy within the conduit.

    Args:
        cable_type (CableType): The type of the cable.
        core_radius (float): The radius of a single core.
        sheath_thickness (float): The thickness of the cable's outer sheath.
        margin (float): An additional margin for spacing.

    Returns:
        float: The effective cross-sectional area of the cable.
    """
    effective_radius = _get_effective_cable_radius(cable_type, core_radius, sheath_thickness, margin)
    return math.pi * (effective_radius ** 2)

def calculate_total_cable_area(cables_data: list[tuple[CableType, float, float, float]]) -> float:
    """
    Calculates the total effective cross-sectional area of all cables intended for a conduit.

    Args:
        cables_data (list[tuple[CableType, float, float, float]]): A list where each tuple
            contains the data for a single cable:
            - cable_type (CableType): The type of the cable.
            - core_radius (float): The radius of a single core for that cable.
            - sheath_thickness (float): The sheath thickness for that cable.
            - margin (float): The margin for that cable.
            Example: [(CableType.SINGLE, 1.0, 0.5, 0.1), (CableType.THREE_CORE, 1.0, 0.5, 0.1)]

    Returns:
        float: The sum of the effective cross-sectional areas of all provided cables.
    """
    total_area = 0.0
    for cable_type, cr, st, m in cables_data:
        total_area += calculate_cable_cross_sectional_area(cable_type, cr, st, m)
    return total_area

def calculate_conduit_fill_percentage(total_cable_area: float, conduit_area: float) -> float:
    """
    Calculates the percentage of the conduit's cross-sectional area that is
    filled by cables.

    Args:
        total_cable_area (float): The total effective cross-sectional area of all cables.
        conduit_area (float): The internal cross-sectional area of the conduit.

    Returns:
        float: The conduit fill percentage. Returns 0.0 if conduit_area is zero
               to prevent division by zero errors.
    """
    if conduit_area == 0:
        return 0.0  # Avoid division by zero if conduit area is effectively non-existent
    return (total_cable_area / conduit_area) * 100

def get_as_nzs_max_fill_percentage(number_of_cables: int) -> float:
    """
    Determines the maximum allowable conduit fill percentage based on a simplified
    interpretation of AS/NZS 3000 standards.

    Note: These rules are simplified for simulation purposes and may not cover all
    specifics or nuances of the standard. Always consult the full standard for
    official compliance.

    Args:
        number_of_cables (int): The number of cables in the conduit.

    Returns:
        float: The maximum allowable fill percentage (e.g., 40.0 for 40%).
               Returns 100.0 if number_of_cables is zero or negative, implying no restriction.
    """
    if number_of_cables <= 0:
        # For zero cables, effectively no fill limit applies from a cable perspective.
        # Can also be interpreted as 100% available space.
        return 100.0
    elif number_of_cables == 1:
        return AS_NZS_MAX_FILL_ONE_CABLE
    elif number_of_cables == 2:
        return AS_NZS_MAX_FILL_TWO_CABLES
    else: # 3 or more cables
        return AS_NZS_MAX_FILL_THREE_OR_MORE_CABLES

def check_as_nzs_compliance(calculated_fill_percentage: float, number_of_cables: int) -> tuple[bool, float]:
    """
    Checks if the calculated conduit fill percentage is compliant with the simplified
    AS/NZS standards used in this simulation.

    Args:
        calculated_fill_percentage (float): The actual calculated fill percentage of the conduit.
        number_of_cables (int): The number of cables for which the fill percentage was calculated.

    Returns:
        tuple[bool, float]: A tuple containing:
            - is_compliant (bool): True if the fill percentage is within the allowable limit, False otherwise.
            - max_allowable_fill_percentage (float): The maximum fill percentage allowed for the given number of cables.
    """
    max_allowable_fill = get_as_nzs_max_fill_percentage(number_of_cables)
    is_compliant = calculated_fill_percentage <= max_allowable_fill
    return is_compliant, max_allowable_fill

# Example usage (primarily for testing and demonstration purposes)
if __name__ == '__main__':
    print("--- Calculations Module Test ---")
    # Assuming a conduit and some cables
    example_conduit_radius = 50  # Example conduit radius in mm
    
    # Using global parameters from config.py for consistency in tests
    default_core_radius = CORE_RADIUS
    default_sheath_thickness = SHEATH_THICKNESS
    default_margin = MARGIN

    conduit_area = calculate_conduit_cross_sectional_area(example_conduit_radius)
    print(f"Conduit Internal Radius: {example_conduit_radius} mm")
    print(f"Conduit Internal Area: {conduit_area:.2f} mm^2")

    # Define some example cables using the structure expected by calculate_total_cable_area
    # Each tuple: (CableType, core_radius, sheath_thickness, margin)
    example_cables_data = [
        (CableType.SINGLE, default_core_radius, default_sheath_thickness, default_margin),
        (CableType.THREE_CORE, default_core_radius, default_sheath_thickness, default_margin),
        (CableType.FOUR_CORE, default_core_radius, default_sheath_thickness, default_margin)
    ]

    print(f"\nUsing Default Cable Parameters: Core Radius={default_core_radius}, Sheath={default_sheath_thickness}, Margin={default_margin}")

    for c_type, cr_val, st_val, m_val in example_cables_data:
        area = calculate_cable_cross_sectional_area(c_type, cr_val, st_val, m_val)
        eff_radius = _get_effective_cable_radius(c_type, cr_val, st_val, m_val)
        print(f"  - {c_type.name} cable: Effective Radius = {eff_radius:.2f} mm, Area = {area:.2f} mm^2")

    total_calculated_cable_area = calculate_total_cable_area(example_cables_data)
    print(f"Total Area for {len(example_cables_data)} Example Cables: {total_calculated_cable_area:.2f} mm^2")

    current_fill_percentage = calculate_conduit_fill_percentage(total_calculated_cable_area, conduit_area)
    print(f"Conduit Fill Percentage for Example Cables: {current_fill_percentage:.2f}%")

    # Test with an empty conduit scenario
    empty_cables_data = []
    total_area_empty_cables = calculate_total_cable_area(empty_cables_data)
    fill_percentage_empty_conduit = calculate_conduit_fill_percentage(total_area_empty_cables, conduit_area)
    print(f"Conduit Fill Percentage (No Cables): {fill_percentage_empty_conduit:.2f}%")

    print("\n--- AS/NZS Compliance Check Examples ---")
    # Test cases for compliance: (number_of_cables, fill_percentage_to_test)
    compliance_test_cases = [
        (0, 25.0), # No cables
        (1, 25.0), (1, 50.0), (1, AS_NZS_MAX_FILL_ONE_CABLE), (1, 60.0), # Single cable scenarios
        (2, 25.0), (2, AS_NZS_MAX_FILL_TWO_CABLES), (2, 35.0),          # Two cables scenarios
        (3, 35.0), (3, AS_NZS_MAX_FILL_THREE_OR_MORE_CABLES), (3, 45.0), # Three cables
        (5, 35.0), (5, AS_NZS_MAX_FILL_THREE_OR_MORE_CABLES), (5, 45.0)  # More than three cables
    ]

    for num_c, fill_perc_test in compliance_test_cases:
        is_compliant_test, limit_test = check_as_nzs_compliance(fill_perc_test, num_c)
        status_str = "Compliant" if is_compliant_test else "Non-Compliant"
        print(f"Test - Cables: {num_c}, Fill: {fill_perc_test}%, Limit: {limit_test}%, Status: {status_str}")
    
    # Example with current example_cables_data from above
    num_example_cables = len(example_cables_data)
    compliant_status_sim, actual_limit_sim = check_as_nzs_compliance(current_fill_percentage, num_example_cables)
    status_sim_str = "Compliant" if compliant_status_sim else "Non-Compliant"
    print(f"\nCompliance for the {num_example_cables} example cables (fill: {current_fill_percentage:.2f}%):")
    print(f"  Max Allowable Fill: {actual_limit_sim}%, Status: {status_sim_str}")
