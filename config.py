# config.py
"""
Global configuration settings for the Cable Conduit Fill Simulator.
This file centralizes parameters for screen dimensions, colors,
cable properties, physics settings, and cable type definitions.
"""
from enum import Enum
import pygame # Not strictly needed for config values but often imported alongside
import pymunk # For type hinting or specific Pymunk constants if used directly

# --- Screen and Display Settings ---
SCREEN_WIDTH = 800  # Width of the Pygame simulation window in pixels
SCREEN_HEIGHT = 800 # Height of the Pygame simulation window in pixels

# --- Color Definitions (RGB tuples) ---
BACKGROUND_COLOR = (255, 255, 255)  # White, for the Pygame window background
CONDUIT_COLOR = (0, 0, 0)           # Black, for drawing the conduit outline
CABLE_SHEATH_COLOR = (255, 165, 0)  # Orange, for the outer sheath of cables
CONDUCTOR_COLOR = (184, 115, 51)    # Copper/Brown, for the conductor part of cable cores

# --- Cable and Conduit Physical Parameters (all units are abstract, e.g., pixels or mm) ---
DEFAULT_CONDUIT_RADIUS = 300 # Renamed from CONDUIT_RADIUS # Internal radius of the conduit
CONDUIT_THICKNESS = 5       # Visual thickness of the conduit wall when drawn
CORE_RADIUS = 30            # Radius of a single electrical core within a cable
SHEATH_THICKNESS = 3        # Thickness of the protective outer sheath of a cable
MARGIN = 2                  # Additional margin around cables for physics calculations (spacing)

# --- Pymunk Physics Collision Types ---
# These are arbitrary integer constants used to categorize different types of physics shapes.
# They allow specific collision handlers to be set up for interactions between different types.
COLLTYPE_CONDUIT = 1 # Collision type for conduit wall segments
COLLTYPE_CABLE = 2   # Collision type for cable shapes

# --- Pymunk Physics Engine Parameters ---
GRAVITY = (0.0, 981.0)  # Global gravity vector (x, y). 981 simulates Earth-like gravity (y-down).
DAMPING = 0.5           # Global damping for the physics space. Reduces overall velocity of objects over time,
                        # helping to stabilize the simulation and prevent excessive bouncing.

# --- Cable Type Definitions ---
class CableType(Enum):
    """
    Enumeration defining the supported types of cables.
    The string value (e.g., "single") is used as a key in CORE_COLORS
    and potentially for other type-specific logic.
    """
    SINGLE = "single"       # Represents a single-core cable
    THREE_CORE = "three"    # Represents a three-core cable (e.g., trefoil arrangement)
    FOUR_CORE = "four"      # Represents a four-core cable (e.g., quad arrangement)

# --- Core Color Definitions ---
CORE_COLORS = {
    "single": (255, 255, 255), # Color for single-core cables (White)
    "three": [                 # Colors for the three cores in a three-core cable
        (255, 0, 0),           # Red
        (255, 255, 255),       # White (or Yellow, depending on standard)
        (0, 0, 255),           # Blue
    ],
    "four": [                  # Colors for the four cores in a four-core cable
        (255, 0, 0),           # Red
        (255, 255, 255),       # White
        (0, 0, 255),           # Blue
        (0, 0, 0),             # Black (Neutral or Earth, depending on standard)
    ],
}
# Note: The core color assignments above are examples and might not strictly adhere
# to specific electrical wiring color codes (which can vary by region and standard).
# For a real-world application, these would need to be verified.
