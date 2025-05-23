# input_handler.py
"""
Manages user input for the Pygame simulation, specifically keyboard events
for selecting cable types and mouse events (implicitly through Pygame's event loop in main.py)
for determining cable spawn positions.
"""
import pygame
import math
import random
from config import CableType, SCREEN_HEIGHT, CONDUIT_RADIUS, SCREEN_WIDTH
from cable import calculate_cable_radius # Used to determine cable size for spawn positioning

class InputHandler:
    """
    Handles user input events to control aspects of the cable simulation.
    Currently supports:
    - Selecting the type of cable to be spawned (single, three-core, four-core) via keyboard keys 1, 2, 3.
    - Calculating a randomized spawn position for new cables near the top of the conduit.
    """
    def __init__(self):
        """
        Initializes the InputHandler.
        Sets the default cable type to be spawned as SINGLE.
        """
        self.current_cable_type: CableType = CableType.SINGLE
        
    def handle_event(self, event: pygame.event.Event):
        """
        Processes a Pygame event to update the current cable type if a relevant key is pressed.

        Args:
            event (pygame.event.Event): The Pygame event to handle.
                                        Listens for KEYDOWN events for keys K_1, K_2, K_3.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.current_cable_type = CableType.SINGLE
                print("Selected Cable Type: SINGLE") # Feedback for user
            elif event.key == pygame.K_2:
                self.current_cable_type = CableType.THREE_CORE
                print("Selected Cable Type: THREE_CORE")
            elif event.key == pygame.K_3:
                self.current_cable_type = CableType.FOUR_CORE
                print("Selected Cable Type: FOUR_CORE")
                
    def get_spawn_position(self) -> tuple[float, float]:
        """
        Calculates a suitable (x, y) position for spawning a new cable.

        The position is determined to be near the top of the conduit, with some
        random horizontal variation to prevent cables from stacking perfectly.
        It considers the radius of the currently selected cable type to ensure
        it spawns within the conduit boundaries.

        Returns:
            tuple[float, float]: A tuple (spawn_x, spawn_y) representing the calculated
                                 spawn coordinates for a new cable.
        """
        # Calculate a margin based on the current cable's radius plus some padding
        current_cable_physical_radius = calculate_cable_radius(self.current_cable_type)
        margin_from_wall = current_cable_physical_radius + 10 # Extra 10 units padding from conduit wall

        # Spawn Y position: near the top opening of the conduit.
        # Positioned such that the top of the cable is roughly 'margin_from_wall' from the conduit's inner top edge.
        spawn_y = (SCREEN_HEIGHT / 2) - CONDUIT_RADIUS + margin_from_wall

        # Calculate available horizontal spawn width at this y-level to keep cables within conduit
        # y_from_center: distance of spawn_y from the conduit's horizontal centerline
        y_from_center = abs(spawn_y - (SCREEN_HEIGHT / 2))
        
        # Using circle equation: x^2 + y^2 = r^2  => x = sqrt(r^2 - y^2)
        # available_half_width is the horizontal distance from conduit center to its edge at spawn_y
        if CONDUIT_RADIUS**2 >= y_from_center**2:
            available_half_width = math.sqrt(CONDUIT_RADIUS**2 - y_from_center**2)
        else:
            available_half_width = 0 # Should not happen if spawn_y is correctly within conduit
            
        # Reduce the spawnable width by the cable's own radius (or margin_from_wall) on both sides
        # to prevent parts of the cable spawning outside the conduit.
        safe_spawn_half_width = max(0, available_half_width - current_cable_physical_radius)
        
        # Randomize X position within this safe horizontal width
        random_offset_x = random.uniform(-safe_spawn_half_width, safe_spawn_half_width)
        spawn_x = (SCREEN_WIDTH / 2) + random_offset_x
        
        return spawn_x, spawn_y
