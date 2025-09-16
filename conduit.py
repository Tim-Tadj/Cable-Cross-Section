# conduit.py
"""
Handles the creation and drawing of the conduit in the Pygame simulation.
The conduit is represented as a series of static Pymunk segments forming a circle.
"""
import math
import pymunk
import pygame # Added for type hinting in draw_conduit

# from config import * # No longer needed if all params are passed

def create_conduit_segments(radius: float, screen_width: int, screen_height: int, segment_radius: float, colltype_conduit: int) -> tuple[pymunk.Body, list[pymunk.Segment]]:
    """
    Creates the static physics segments that form the circular boundary of the conduit.

    The conduit is approximated by a series of short, straight Pymunk segments.
    These segments are attached to a single static Pymunk body.

    Args:
        radius (float): The internal radius of the conduit.
        screen_width (int): Width of the simulation screen.
        screen_height (int): Height of the simulation screen.
        segment_radius (float): Physics collision radius for conduit segments. Small (e.g., 1) gives tight contact.
        colltype_conduit (int): Collision type for the conduit segments.


    Returns:
        tuple[pymunk.Body, list[pymunk.Segment]]: A tuple containing:
            - body (pymunk.Body): The static Pymunk body to which all segments are attached.
            - segments (list[pymunk.Segment]): A list of Pymunk Segment shapes forming the conduit.
    """
    # Create a static body for the conduit segments. Static bodies are not affected by gravity or collisions.
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    segments = [] # List to hold the individual segment shapes

    num_segments = 64 # Number of segments to approximate the circle. More segments = smoother circle.
    
    # Calculate points for each segment around the circumference of the conduit
    for i in range(num_segments):
        angle1 = (2 * math.pi * i) / num_segments  # Start angle for the current segment
        angle2 = (2 * math.pi * (i + 1)) / num_segments # End angle for the current segment

        # Calculate start (x1, y1) and end (x2, y2) points for the segment
        # The conduit is centered on the screen.
        x1 = screen_width / 2 + radius * math.cos(angle1)
        y1 = screen_height / 2 + radius * math.sin(angle1)
        x2 = screen_width / 2 + radius * math.cos(angle2)
        y2 = screen_height / 2 + radius * math.sin(angle2)

        # Create a Pymunk segment shape with small physics radius so cables can visually touch the wall
        segment = pymunk.Segment(body, (x1, y1), (x2, y2), segment_radius)
        segment.friction = 0.5      # Standard friction property
        segment.elasticity = 0.4    # Some bounciness
        segment.collision_type = colltype_conduit # Use passed colltype_conduit
        segments.append(segment)
        
    return body, segments

def draw_conduit(screen: pygame.Surface, color: tuple[int,int,int], center_x: int, center_y: int, radius: float, thickness: int):
    """
    Draws the conduit on the Pygame screen as a circle.

    Note: This draws a perfect circle visually, even though the physics model
    uses segments. For visual purposes, a single circle is simpler and looks cleaner.

    Args:
        screen (pygame.Surface): The Pygame surface to draw on.
        color (tuple[int,int,int]): The RGB color for the conduit.
        center_x (int): The x-coordinate of the conduit's center.
        center_y (int): The y-coordinate of the conduit's center.
        radius (float): The radius of the conduit.
        thickness (int): The thickness of the circle's line.
    """
    # Draw a circle representing the conduit
    # pygame.draw.circle(surface, color, center_pos, radius, width)
    # Using thickness for the 'width' argument makes it draw the edge of the circle.
    pygame.draw.circle(
        screen, 
        color, 
        (center_x, center_y), # Center of the screen
        radius, 
        thickness # This makes it a ring, not a filled circle
    )
