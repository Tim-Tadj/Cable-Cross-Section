# conduit.py
"""
Handles the creation and drawing of the conduit in the Pygame simulation.
The conduit is represented as a series of static Pymunk segments forming a circle.
"""
import math
import pymunk
from config import * # Imports SCREEN_WIDTH, SCREEN_HEIGHT, CONDUIT_RADIUS, etc.

def create_conduit_segments() -> tuple[pymunk.Body, list[pymunk.Segment]]:
    """
    Creates the static physics segments that form the circular boundary of the conduit.

    The conduit is approximated by a series of short, straight Pymunk segments.
    These segments are attached to a single static Pymunk body.

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
        x1 = SCREEN_WIDTH / 2 + CONDUIT_RADIUS * math.cos(angle1)
        y1 = SCREEN_HEIGHT / 2 + CONDUIT_RADIUS * math.sin(angle1)
        x2 = SCREEN_WIDTH / 2 + CONDUIT_RADIUS * math.cos(angle2)
        y2 = SCREEN_HEIGHT / 2 + CONDUIT_RADIUS * math.sin(angle2)

        # Create a Pymunk segment shape
        segment = pymunk.Segment(body, (x1, y1), (x2, y2), CONDUIT_THICKNESS)
        segment.friction = 0.5      # Standard friction property
        segment.elasticity = 0.4    # Some bounciness
        segment.collision_type = COLLTYPE_CONDUIT # Assign custom collision type
        segments.append(segment)
        
    return body, segments

def draw_conduit(screen: pygame.Surface):
    """
    Draws the conduit on the Pygame screen as a circle.

    Note: This draws a perfect circle visually, even though the physics model
    uses segments. For visual purposes, a single circle is simpler and looks cleaner.

    Args:
        screen (pygame.Surface): The Pygame surface to draw on.
    """
    # Draw a circle representing the conduit
    # pygame.draw.circle(surface, color, center_pos, radius, width)
    # Using CONDUIT_THICKNESS for the 'width' argument makes it draw the edge of the circle.
    pygame.draw.circle(
        screen, 
        CONDUIT_COLOR, 
        (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), # Center of the screen
        CONDUIT_RADIUS, 
        CONDUIT_THICKNESS # This makes it a ring, not a filled circle
    )
