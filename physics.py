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
    # Some environments have reported an AttributeError for Space.add_collision_handler
    # (likely due to an unexpected pymunk version/environment issue). Provide a fallback
    # using the default collision handler and filtering inside a wrapper callback.
    if hasattr(space, "add_collision_handler"):
        try:
            handler = space.add_collision_handler(COLLTYPE_CABLE, COLLTYPE_CABLE)
            handler.separate = cable_collision_handler
        except Exception:
            pass  # Silently continue if unexpected failure; collisions still work with defaults
    elif hasattr(space, "add_default_collision_handler"):
        # Older / environment-specific API providing only default handler
        try:
            def _selective_separate(arbiter: pymunk.Arbiter, inner_space: pymunk.Space, data: dict):
                a, b = arbiter.shapes
                if getattr(a, 'collision_type', None) == COLLTYPE_CABLE and getattr(b, 'collision_type', None) == COLLTYPE_CABLE:
                    return cable_collision_handler(arbiter, inner_space, data)
                return True
            default_handler = space.add_default_collision_handler()
            default_handler.separate = _selective_separate
        except Exception:
            pass
    else:
        # No collision handler customization available in this environment; proceed with defaults
        pass
    # Note: Conduit is no longer added here; it's managed by main.py via rebuild_conduit_in_space
    return space

def rebuild_conduit_in_space(space: pymunk.Space, old_conduit_body: pymunk.Body | None, old_segments_list: list[pymunk.Segment], new_radius: float, screen_width: int, screen_height: int, segment_radius: float, colltype_conduit: int) -> tuple[pymunk.Body, list[pymunk.Segment]]:
    """
    Removes old conduit segments (if any) and adds new ones with the specified radius.

    Args:
        space (pymunk.Space): The Pymunk space.
        old_conduit_body (pymunk.Body | None): The previous static body for the conduit.
        old_segments_list (list[pymunk.Segment]): List of previous conduit segment shapes.
        new_radius (float): The new radius for the conduit.
        screen_width (int): Width of the simulation screen.
        screen_height (int): Height of the simulation screen.
        segment_radius (float): Physics collision radius of the conduit wall segments.
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
    new_body, new_segment_shapes = create_conduit_segments(new_radius, screen_width, screen_height, segment_radius, colltype_conduit)
    space.add(new_body)
    for segment in new_segment_shapes:
        space.add(segment)
    
    return new_body, new_segment_shapes # Return new body and segments to be stored
