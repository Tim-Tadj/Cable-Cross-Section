# config.py
from enum import Enum
import pygame
import pymunk

# Window dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 800

# Colors
BACKGROUND_COLOR = (255, 255, 255)  # White
CONDUIT_COLOR = (0, 0, 0)  # Black
CABLE_SHEATH_COLOR = (255, 165, 0)  # Orange
CONDUCTOR_COLOR = (184, 115, 51)  # Copper

# Cable parameters
CONDUIT_RADIUS = 300
CONDUIT_THICKNESS = 5
CORE_RADIUS = 30
SHEATH_THICKNESS = 3
MARGIN = 2

# Collision types
COLLTYPE_CONDUIT = 1
COLLTYPE_CABLE = 2

# Physics parameters
GRAVITY = (0.0, 981.0)
DAMPING = 0.5

class CableType(Enum):
    SINGLE = "single"
    THREE_CORE = "three"
    FOUR_CORE = "four"

CORE_COLORS = {
    "single": (255, 255, 255),
    "three": [
        (255, 0, 0),    # Red
        (255, 255, 255),  # White
        (0, 0, 255),    # Blue
    ],
    "four": [
        (255, 0, 0),    # Red
        (255, 255, 255),  # White
        (0, 0, 255),    # Blue
        (0, 0, 0),      # Black
    ],
}
