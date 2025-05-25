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

# --- Global Variables for Fallback Spawning from Pygame window ---
# These are updated by spawn_cable (called by GUI) and used by MOUSEBUTTONDOWN event
last_used_outer_diameter = 60.0  # Default or last used outer diameter
last_used_cable_type = CableType.SINGLE # Default or last used cable type
# ---

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
Each tuple now contains: (id, Pymunk body, Pymunk shape, CableType enum, outer_diameter).
This list is used for rendering cables and for calculations in the GUI."""
# ---

def spawn_cable(position: tuple[int, int], cable_type_to_spawn: CableType, outer_diameter: float):
    """
    Spawns a new cable in the simulation at the given position, type, and outer diameter.

    A Pymunk body and shape are created, assigned a random horizontal velocity,
    and then added to the physics space and the global 'cables' list.
    Updates global 'last_used_outer_diameter' and 'last_used_cable_type'.

    Args:
        position (tuple[int, int]): The (x, y) coordinates where the cable should be spawned.
        cable_type_to_spawn (CableType): The type of cable to spawn.
        outer_diameter (float): The outer diameter of the cable.
    """
    global next_cable_id, last_used_outer_diameter, last_used_cable_type
    
    # create_cable now returns (body, shape, cable_type_obj, returned_outer_diameter)
    # We use the outer_diameter passed into spawn_cable for consistency, though returned_outer_diameter should be the same.
    body, shape, cable_type_obj, _returned_outer_diameter = create_cable(
        position, cable_type_to_spawn, outer_diameter
    )
    
    # Assign a small random horizontal velocity
    body.velocity = (random.uniform(-50, 50), 0)
    space.add(body, shape)
    
    cables.append((next_cable_id, body, shape, cable_type_obj, outer_diameter)) # Store with ID and outer_diameter
    next_cable_id += 1
    
    # Update last used values for potential fallback spawning from Pygame window
    last_used_outer_diameter = outer_diameter
    last_used_cable_type = cable_type_to_spawn
    # GUI updates via QTimer

def remove_cables_by_ids(ids_to_remove: list[int]):
    """
    Removes cables from the simulation based on a list of their IDs.
    It updates both the global 'cables' list and removes the corresponding
    Pymunk bodies and shapes from the physics 'space'.
    """
    global cables, space
    cables_to_keep = []
    for cable_data in cables:
        # Unpack, expecting 5 elements now: (id, body, shape, type, diameter)
        # The last element (diameter) is not used here, but unpacking needs to match.
        cable_id, body, shape, _cable_type, _outer_diameter = cable_data 
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
        # Unpack, expecting 5 elements: (id, body, shape, type, diameter)
        # Only body and shape are needed here.
        _id, body, shape, _cable_type, _outer_diameter = cable_data_tuple 
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
                # Get spawn position using the input handler.
                # For MOUSEBUTTONDOWN in Pygame window, use last_used_outer_diameter and last_used_cable_type.
                # The input_handler's current_cable_type (set by K_1, K_2, K_3) is ignored here
                # in favor of last_used_cable_type set by the GUI or previous spawns.
                spawn_pos_tuple = input_handler.get_spawn_position(current_conduit_radius, last_used_outer_diameter)
                
                # Spawn using the last used type and diameter.
                spawn_cable(spawn_pos_tuple, last_used_cable_type, last_used_outer_diameter)
                # GUI updates via QTimer
        
        # Physics simulation step
        # Step the Pymunk space multiple times per frame for stability
        for _ in range(6): # Sub-steps for physics solver
            space.step(1 / 360.0) # Small, fixed time step
        
        # Rendering
        screen.fill(BACKGROUND_COLOR)  # Clear screen with background color
        # Draw conduit using current_conduit_radius and other config constants
        draw_conduit(screen, CONDUIT_COLOR, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, current_conduit_radius, CONDUIT_THICKNESS)
        
        # Draw each cable currently in the simulation
        # Cables list now stores: (id, body, shape, cable_type_enum, outer_diameter)
        # Unpack shape as _ as it's not directly used by draw_cable.
        for _id, body, _shape, cable_type_enum, outer_diameter_val in cables: # Iterate through the global 'cables' list
            draw_cable(screen, body, cable_type_enum, outer_diameter_val) # Pass outer_diameter_val
        
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
