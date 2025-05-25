# cable.py
"""
Handles the creation, physics properties, drawing, and collision of cables.
Cables can be single-core, three-core, or four-core, each with specific
geometric arrangements for their cores.
"""
import math
from config import * # Imports global configurations like CORE_RADIUS, SHEATH_THICKNESS, colors, etc.
import pymunk # For physics object creation (Body, Circle)

def cable_collision_handler(arbiter: pymunk.Arbiter, space: pymunk.Space, data: dict) -> bool:
    """
    A simple collision handler for cable-to-cable interactions.
    This is a basic placeholder and applies a small repulsive impulse.
    For more realistic behavior, this would need significant refinement
    based on material properties and desired interaction effects.

    Args:
        arbiter (pymunk.Arbiter): Contains information about the collision pair.
        space (pymunk.Space): The physics space where the collision occurred.
        data (dict): User-defined data passed to the handler (not used here).

    Returns:
        bool: True to continue processing the collision normally.
    """
    cable_a, cable_b = arbiter.shapes
    normal = arbiter.normal # Normal vector of the collision
    points = arbiter.contact_point_set.points # Contact points

    # Apply a small, somewhat arbitrary impulse to simulate a soft repulsion.
    # This is a very simplistic model of cable interaction.
    for point in points:
        impulse_magnitude = 5.0 # Arbitrary impulse strength
        # Apply impulse to body_a at the contact point relative to body_a's center
        cable_a.body.apply_impulse_at_world_point(
            normal * impulse_magnitude, point.point_a
        )
        # Apply opposite impulse to body_b
        cable_b.body.apply_impulse_at_world_point(
            -normal * impulse_magnitude, point.point_b
        )
    return True # Standard collision processing should continue

def calculate_cable_radius(outer_diameter: float) -> float:
    """
    Calculates the radius of a cable based on its outer diameter.

    Args:
        outer_diameter (float): The outer diameter of the cable.

    Returns:
        float: The calculated radius of the cable (outer_diameter / 2).
    """
    return outer_diameter / 2

def get_core_positions(cable_type: CableType, cable_radius: float) -> list[tuple[float, float]]:
    """
    Calculates the relative (x, y) positions of the centers of the cores within a cable,
    based on the cable type. These positions are relative to the cable's body center.

    - Single-core: One core at the center (0,0).
    - Three-core (Trefoil): Three cores arranged symmetrically around the center.
      The `core_center_distance` is the same as in `calculate_cable_radius`.
      Cores are placed at 0, 120 (2pi/3), and 240 (4pi/3) degrees.
    - Four-core (Quad): Four cores, typically assumed to be in a square or diamond formation.
      Here, they are placed along the axes at `core_center_distance`.
      (Note: This might be simplified; a true quad often has a central filler or slight offsets).

    Args:
        cable_type (CableType): The type of cable.
        cable_radius (float): The overall radius of the cable (not directly used in current logic
                              but could be relevant for more complex core positioning).

    Returns:
        list[tuple[float, float]]: A list of (x, y) tuples for each core's center,
                                   relative to the cable's center.
    """
    if cable_type == CableType.SINGLE:
        return [(0, 0)] # Single core at the center
    elif cable_type == CableType.THREE_CORE:
        core_center_distance = (2 * CORE_RADIUS) / math.sqrt(3) # Distance from cable center to core center
        angles = [0, 2 * math.pi / 3, 4 * math.pi / 3] # Angles for three cores (0, 120, 240 degrees)
        return [
            (math.cos(angle) * core_center_distance, math.sin(angle) * core_center_distance)
            for angle in angles
        ]
    else:  # FOUR_CORE
        # Simplified square/diamond formation for four cores
        core_center_distance = math.sqrt(2) * CORE_RADIUS # Distance from cable center to core center
        # Positions: (0, -d), (d, 0), (0, d), (-d, 0)
        # This forms a diamond shape if axes are standard.
        return [
            (0, -core_center_distance), # Top (or bottom depending on y-axis direction)
            (core_center_distance, 0),  # Right
            (0, core_center_distance),  # Bottom (or top)
            (-core_center_distance, 0), # Left
        ]

def create_cable(position: tuple[float, float], cable_type: CableType, outer_diameter: float) -> tuple[pymunk.Body, pymunk.Circle, CableType, float]:
    """
    Creates a Pymunk physics body and shape for a cable.

    Args:
        position (tuple[float, float]): The initial (x, y) world coordinates for the cable's center.
        cable_type (CableType): The type of cable to create.
        outer_diameter (float): The outer diameter of the cable.

    Returns:
        tuple[pymunk.Body, pymunk.Circle, CableType, float]: A tuple containing the Pymunk Body,
                                                     Pymunk Circle shape, the cable_type, and the outer_diameter.
    """
    mass = 1 # Arbitrary mass for the cable
    effective_radius = calculate_cable_radius(outer_diameter)
    # Calculate moment of inertia for a solid circle
    moment = pymunk.moment_for_circle(mass, 0, effective_radius)
    body = pymunk.Body(mass, moment) # Create the rigid body
    body.position = position # Set its initial position

    # Create the circular physics shape for the cable
    shape = pymunk.Circle(body, effective_radius)
    shape.friction = 0.5      # Standard friction
    shape.elasticity = 0.4    # Some bounciness
    shape.collision_type = COLLTYPE_CABLE # Assign custom collision type for specific handling
    shape.filter = pymunk.ShapeFilter(categories=0b1) # Belongs to category 1 (e.g., for collision filtering)

    return body, shape, cable_type, outer_diameter # Return the body, shape, its type and outer_diameter

def draw_cable(screen: pygame.Surface, body: pymunk.Body, cable_type: CableType, outer_diameter: float):
    """
    Draws a cable, including its sheath and individual cores, on the Pygame screen.

    The cores are drawn rotated according to the cable body's current angle.

    Args:
        screen (pygame.Surface): The Pygame surface to draw on.
        body (pymunk.Body): The Pymunk body of the cable, providing position and angle.
        cable_type (CableType): The type of cable, determining core arrangement and colors.
        outer_diameter (float): The outer diameter of the cable.
    """
    pos = body.position # Center position of the cable body
    angle = body.angle  # Current rotation angle of the cable body
    effective_cable_radius = outer_diameter / 2 # Overall radius for drawing

    # 1. Draw the outer sheath of the cable
    pygame.draw.circle(
        screen, CABLE_SHEATH_COLOR, (int(pos.x), int(pos.y)), effective_cable_radius
    )

    # 2. Draw an inner circle representing the area just inside the sheath (optional visual detail)
    # This color (230, 140, 0) is a dark yellow/orange, perhaps representing insulation layer.
    # SHEATH_THICKNESS is used here, assuming it's a visual property independent of the main outer_diameter for physics.
    # If SHEATH_THICKNESS should scale, this needs adjustment.
    pygame.draw.circle(
        screen,
        (230, 140, 0), # Example: Inner insulation color
        (int(pos.x), int(pos.y)),
        effective_cable_radius - SHEATH_THICKNESS, # Radius is sheath boundary minus sheath thickness
    )

    # 3. Get relative positions of cores and their colors
    # Note: effective_cable_radius passed to get_core_positions is now outer_diameter / 2.
    # The core positions are still based on global CORE_RADIUS, so they might look disproportionate.
    core_relative_positions = get_core_positions(cable_type, effective_cable_radius)
    # Fetch core colors based on cable type (e.g., "single", "three_core")
    core_color_set = CORE_COLORS[cable_type.value] # .value gives the string key for the dict

    # 4. Draw each core
    for i, (offset_x, offset_y) in enumerate(core_relative_positions):
        # Rotate the core's relative offset by the cable body's angle
        rotated_x = offset_x * math.cos(angle) - offset_y * math.sin(angle)
        rotated_y = offset_x * math.sin(angle) + offset_y * math.cos(angle)

        # Calculate the absolute world position of the core's center
        core_x_world = int(pos.x + rotated_x)
        core_y_world = int(pos.y + rotated_y)

        # Determine the color for the current core
        # CORE_COLORS can provide a single color (for single-core) or a list (for multi-core)
        current_core_color = core_color_set[i] if isinstance(core_color_set, list) else core_color_set
        
        # Draw the core insulation
        pygame.draw.circle(screen, current_core_color, (core_x_world, core_y_world), CORE_RADIUS)
        
        # Draw the conductor part of the core (slightly smaller, metallic color)
        pygame.draw.circle(
            screen, CONDUCTOR_COLOR, (core_x_world, core_y_world), CORE_RADIUS - 2 # -2 makes it appear as an inner circle
        )
