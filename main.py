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
from physics import setup_physics, rebuild_conduit_in_space # MODIFIED HERE
from input_handler import InputHandler

# --- Global Scope Variables ---
# These variables are defined at the module level to be accessible and modifiable
# by both the main simulation loop in this file and potentially by other modules
# like the GUI (cable_gui.py) for control and display purposes.

next_cable_id = 1
"""Counter to assign unique IDs to spawned cables."""

input_handler = InputHandler()
"""Manages user input, primarily for selecting cable types via keyboard
and determining spawn positions for new cables."""

space = setup_physics()
"""The Pymunk physics space instance. All physics bodies (cables, conduit walls)
and their interactions are managed within this space."""

current_conduit_radius = DEFAULT_CONDUIT_RADIUS
"""Current radius of the conduit, can be changed dynamically via GUI."""
conduit_body = None # To store the static body of the conduit
"""Pymunk static body for the current conduit. Used for removal when rebuilding."""
conduit_segments = [] # To store conduit segment shapes for removal
"""List of Pymunk segment shapes for the current conduit. Used for removal when rebuilding."""


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
    # Ensure next_cable_id is accessible if it's modified here (it is, so global keyword is needed)
    global next_cable_id 
    
    body, shape, cable_type_obj = create_cable( # from cable.py
        position, cable_type_to_spawn
    )
    
    # Assign a small random horizontal velocity for a slightly more dynamic entry
    body.velocity = (random.uniform(-50, 50), 0)
    space.add(body, shape) # Add to physics space
    
    cables.append((next_cable_id, body, shape, cable_type_obj)) # Store ID
    next_cable_id += 1
    # Note: GUI updates (like recalculating fill percentage) are not directly triggered here.
    # The GUI uses a QTimer to periodically check the 'cables' list and update itself.

def remove_cables_by_ids(ids_to_remove: list[int]):
    """
    Removes cables from the simulation based on a list of their IDs.
    It updates both the global 'cables' list and removes the corresponding
    Pymunk bodies and shapes from the physics 'space'.
    """
    global cables, space
    cables_to_keep = []
    for cable_data in cables:
        cable_id, body, shape, _ = cable_data
        if cable_id in ids_to_remove:
            # Important: Check if body and shape are currently in the space before removing
            # This can prevent errors if an object was already removed or not fully added.
            if body in space.bodies:
                 space.remove(body)
            if shape in space.shapes:
                 space.remove(shape)
        else:
            cables_to_keep.append(cable_data)
    cables = cables_to_keep

def reset_view():
    """
    Resets the simulation state by clearing all dynamically added cables.

    It iterates through all bodies in the Pymunk space and removes those
    that are dynamic (i.e., the cables). The global 'cables' list is also cleared.
    The global 'next_cable_id' is reset to 1.
    Static elements like conduit walls are assumed to remain.
    """
    global cables, space, next_cable_id # next_cable_id is now also reset
    
    # Iterate through a copy of the cables list for safe removal
    for cable_data_tuple in list(cables):
        _id, body, shape, _ = cable_data_tuple # Unpack assuming new structure (id, body, shape, type)
        # Check if body and shape are in space before removal to prevent errors
        if body in space.bodies:
            space.remove(body)
        if shape in space.shapes:
            space.remove(shape)
            
    cables.clear() # Clear the list of cable references
    next_cable_id = 1 # Reset ID counter

    # Conduit itself is rebuilt by update_simulation_conduit_radius if its size changes.
    # Resetting view primarily concerns cables.

def update_simulation_conduit_radius(new_radius: float):
    """
    Updates the conduit's radius in the simulation.
    This involves removing the old conduit segments from the Pymunk space
    and adding new ones with the specified radius.
    """
    global current_conduit_radius, conduit_body, conduit_segments, space
    
    current_conduit_radius = new_radius
    
    # Rebuild the conduit in Pymunk space
    # Using constants from config.py for screen_width, screen_height, etc.
    new_body, new_segs = rebuild_conduit_in_space(
        space, 
        conduit_body, 
        conduit_segments, 
        current_conduit_radius,
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        CONDUIT_THICKNESS,
        COLLTYPE_CONDUIT
    )
    conduit_body = new_body
    conduit_segments = new_segs
    # The GUI's QTimer will handle calling update_calculations_display,
    # which will use the new main.current_conduit_radius.

def main():
    """
    The main function to run the Pygame simulation.

    Initializes Pygame, sets up the display, clock, and physics space.
    It then enters the main simulation loop, handling events, stepping the physics,
    and rendering the simulation elements (conduit, cables) on the screen.
    This function is typically run in a separate thread when the GUI is active.
    """
    global conduit_body, conduit_segments # Ensure these are treated as global for initial setup

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Multi-Core Cable Simulation")
    clock = pygame.time.Clock()
    
    # Initial conduit setup:
    # This replaces the old add_conduit_to_space(space) call.
    # It populates the global conduit_body and conduit_segments.
    conduit_body, conduit_segments = rebuild_conduit_in_space(
        space, 
        None,  # No old body to remove initially
        [],    # No old segments to remove initially
        current_conduit_radius,
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        CONDUIT_THICKNESS,
        COLLTYPE_CONDUIT
    )
    
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
        # Draw conduit using current_conduit_radius and other config constants
        draw_conduit(screen, CONDUIT_COLOR, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, current_conduit_radius, CONDUIT_THICKNESS)
        
        # Draw each cable currently in the simulation
        # Now iterates through (id, body, shape, cable_type_enum)
        for _, body, _, cable_type_enum in cables: # Iterate through the global 'cables' list
            draw_cable(screen, body, cable_type_enum)
        
        pygame.display.flip() # Update the full display
        clock.tick(60) # Maintain 60 frames per second
    
    pygame.quit() # Uninitialize Pygame modules
    sys.exit()    # Ensure the program/thread exits cleanly

if __name__ == "__main__":
    # This block allows main.py to be run directly, starting the simulation.
    # When used with the GUI (cable_gui.py), main() is typically called in a thread.
    main()

# Ensure rebuild_conduit_in_space is imported from physics.py at the top # REMOVED LINE
# from physics import rebuild_conduit_in_space # REMOVED LINE
