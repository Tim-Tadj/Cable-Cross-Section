# main.py
"""
Main module for the Cable Conduit Fill Simulator.
This module initializes Pygame, sets up the physics simulation environment (Pymunk),
handles the main game loop (event processing, physics stepping, rendering),
and manages global-like variables for simulation state.
"""
import pygame
import sys
import random
import pymunk # Added for reset_view's type check
from config import *
from cable import create_cable, draw_cable
from conduit import draw_conduit
from physics import setup_physics, add_conduit_to_space
from input_handler import InputHandler

# --- Global Scope Variables ---
# These variables are defined at the module level to be accessible and modifiable
# by both the main simulation loop in this file and potentially by other modules
# like the GUI (cable_gui.py) for control and display purposes.

input_handler = InputHandler()
"""Manages user input, primarily for selecting cable types via keyboard
and determining spawn positions for new cables."""

space = setup_physics()
"""The Pymunk physics space instance. All physics bodies (cables, conduit walls)
and their interactions are managed within this space."""

cables = []
"""A list storing tuples for each active cable in the simulation.
Each tuple typically contains: (Pymunk body, Pymunk shape, CableType enum).
This list is used for rendering cables and for calculations in the GUI."""
# ---

def spawn_cable(position: tuple[int, int], cable_type_to_spawn: CableType):
    """
    Spawns a new cable in the simulation at the given position and with the specified type.

    A Pymunk body and shape are created for the cable, assigned a random horizontal velocity,
    and then added to the physics space and the global 'cables' list.

    Args:
        position (tuple[int, int]): The (x, y) coordinates where the cable should be spawned.
                                    Typically near the top of the conduit.
        cable_type_to_spawn (CableType): The type of cable to spawn (e.g., SINGLE, THREE_CORE).
    """
    # global space, cables # Not needed as they are already global
    body, shape, cable_type_enum_instance = create_cable(
        position, cable_type_to_spawn
    )
    # Assign a small random horizontal velocity for a slightly more dynamic entry
    body.velocity = (random.uniform(-50, 50), 0)
    space.add(body, shape)
    cables.append((body, shape, cable_type_enum_instance))
    # Note: GUI updates (like recalculating fill percentage) are not directly triggered here.
    # The GUI uses a QTimer to periodically check the 'cables' list and update itself.

def reset_view():
    """
    Resets the simulation state by clearing all dynamically added cables.

    It iterates through all bodies in the Pymunk space and removes those
    that are dynamic (i.e., the cables). The global 'cables' list is also cleared.
    Static elements like conduit walls are assumed to remain.
    """
    # global cables, space # Not needed as they are already global
    cables.clear() # Clear the list of cable references

    # Remove all dynamic Pymunk bodies (the cables) from the space.
    # Static bodies (like conduit walls) are preserved.
    # Iterate over a copy of space.bodies because we are modifying it.
    for body_to_remove in list(space.bodies):
        if body_to_remove.body_type == pymunk.Body.DYNAMIC:
            space.remove(body_to_remove, *body_to_remove.shapes) # Remove body and all its shapes

    # Note: If conduit segments were also dynamically added and need re-adding,
    # a call like `add_conduit_to_space(space)` would be necessary here.
    # However, current design assumes conduit is static and added once.

def main():
    """
    The main function to run the Pygame simulation.

    Initializes Pygame, sets up the display, clock, and physics space.
    It then enters the main simulation loop, handling events, stepping the physics,
    and rendering the simulation elements (conduit, cables) on the screen.
    This function is typically run in a separate thread when the GUI is active.
    """
    # global space, cables, input_handler # Not needed as they are already global
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Multi-Core Cable Simulation")
    clock = pygame.time.Clock()
    
    # Ensure the conduit is added to the (now global) Pymunk space.
    # This is done once at the start.
    add_conduit_to_space(space)
    
    running = True
    while running:
        # Event handling loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False # Exit the main loop
            
            # Pass event to the input handler (manages keyboard state for cable type selection)
            input_handler.handle_event(event)
            
            # Handle cable spawning on mouse click in the Pygame window
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Get spawn position (typically near top, x-coordinate from mouse)
                # and currently selected cable type from the input handler.
                spawn_pos_tuple = input_handler.get_spawn_position()
                current_selected_type = input_handler.current_cable_type
                spawn_cable(spawn_pos_tuple, current_selected_type)
                # The GUI is not directly notified; its QTimer will pick up changes in `main.cables`.
        
        # Physics simulation step
        # Step the Pymunk space multiple times per frame for stability
        for _ in range(6): # Sub-steps for physics solver
            space.step(1 / 360.0) # Small, fixed time step
        
        # Rendering
        screen.fill(BACKGROUND_COLOR)  # Clear screen with background color
        draw_conduit(screen)           # Draw the conduit
        
        # Draw each cable currently in the simulation
        for body, _, cable_type_enum in cables: # Iterate through the global 'cables' list
            draw_cable(screen, body, cable_type_enum)
        
        pygame.display.flip() # Update the full display
        clock.tick(60) # Maintain 60 frames per second
    
    pygame.quit() # Uninitialize Pygame modules
    sys.exit()    # Ensure the program/thread exits cleanly

if __name__ == "__main__":
    # This block allows main.py to be run directly, starting the simulation.
    # When used with the GUI (cable_gui.py), main() is typically called in a thread.
    main()
