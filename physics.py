# physics.py
"""
Manages the setup of the Pymunk physics space, including gravity, damping,
and collision handlers. Also handles adding static conduit elements to the space.
"""
import pymunk
from config import COLLTYPE_CABLE # Custom collision type constants (COLLTYPE_CONDUIT no longer needed here)
from cable import cable_collision_handler # Specific handler for cable-to-cable collisions
from conduit import create_conduit_segments # Function to get conduit's physics segments

def setup_physics() -> pymunk.Space:
    """
    Initializes and configures the Pymunk physics space.

    Sets up global physics properties like gravity and damping.
    It also configures a collision handler for interactions between cables.

    Returns:
        pymunk.Space: The configured Pymunk space object.
    """
    space = pymunk.Space()
    space.gravity = (0.0, 981.0)  # Standard gravity in Pygame coordinates (y-downwards)
    space.damping = 0.5           # Damping to reduce overall energy and stabilize simulation

    # Setup a collision handler for cable-to-cable collisions.
    # COLLTYPE_CABLE is an integer constant defined in config.py.
    # When two shapes with this collision_type interact, the specified handler functions are called.
    handler = space.add_collision_handler(COLLTYPE_CABLE, COLLTYPE_CABLE)
    
    # The 'separate' callback is triggered when two shapes stop overlapping.
    # cable_collision_handler is a function (defined in cable.py) that will be
    # called to manage the physics of this interaction (e.g., apply impulses).
    # Other callbacks like 'begin', 'pre_solve', 'post_solve' could also be used
    # for different stages of collision handling.
    handler.separate = cable_collision_handler # Using 'separate' might be less common than 'begin' or 'pre_solve' for active repulsion.
                                               # This implies the handling logic is applied when they move apart.
                                               # Consider if `pre_solve` or `begin` would be more appropriate for typical collision responses.
    # Note: Conduit is no longer added here; it's managed by main.py via rebuild_conduit_in_space
    return space

def rebuild_conduit_in_space(space: pymunk.Space, old_conduit_body: pymunk.Body | None, old_segments_list: list[pymunk.Segment], new_radius: float, screen_width: int, screen_height: int, conduit_thickness: int, colltype_conduit: int) -> tuple[pymunk.Body, list[pymunk.Segment]]:
    """
    Removes old conduit segments (if any) and adds new ones with the specified radius.

    Args:
        space (pymunk.Space): The Pymunk space.
        old_conduit_body (pymunk.Body | None): The previous static body for the conduit.
        old_segments_list (list[pymunk.Segment]): List of previous conduit segment shapes.
        new_radius (float): The new radius for the conduit.
        screen_width (int): Width of the simulation screen.
        screen_height (int): Height of the simulation screen.
        conduit_thickness (int): Visual and physical thickness of the conduit wall.
        colltype_conduit (int): Collision type for the conduit segments.

    Returns:
        tuple[pymunk.Body, list[pymunk.Segment]]: The new Pymunk body and list of segment shapes for the conduit.
    """
    # Remove old conduit segments if they exist
    if old_conduit_body:
        # It's crucial to remove shapes associated with a body BEFORE removing the body itself
        # if the shapes are not explicitly removed separately.
        # However, since we have old_segments_list, we iterate and remove them.
        for segment in old_segments_list:
            if segment in space.shapes: # Check if shape is in space before removing
                 space.remove(segment)
        if old_conduit_body in space.bodies: # Check if body is in space before removing
            space.remove(old_conduit_body)
    old_segments_list.clear() # Clear the passed list

    # Create and add new conduit segments
    # create_conduit_segments now takes radius and other params
    new_body, new_segment_shapes = create_conduit_segments(new_radius, screen_width, screen_height, conduit_thickness, colltype_conduit)
    space.add(new_body)
    for segment in new_segment_shapes:
        space.add(segment)
    
    return new_body, new_segment_shapes # Return new body and segments to be stored
