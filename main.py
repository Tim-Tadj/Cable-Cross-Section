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
import math
import threading
import pymunk # Added for reset_view's type check
from config import *
from cable import create_cable, draw_cable, compute_min_outer_diameter
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

current_conduit_diameter = DEFAULT_CONDUIT_DIAMETER
"""Current internal diameter of the conduit (user-facing)."""
# Internal physics functions expect a radius; compute radius on-demand as diameter/2.
conduit_body = None # To store the static body of the conduit
"""Pymunk static body for the current conduit. Used for removal when rebuilding."""
conduit_segments = [] # To store conduit segment shapes for removal
"""List of Pymunk segment shapes for the current conduit. Used for removal when rebuilding."""

# --- Rendering controls ---
render_zoom = 1.0
"""Current zoom factor for rendering around the screen center (1.0 = 100%)."""

shutdown_event = threading.Event()
"""Global event used to request the simulation loop to exit."""

exit_callbacks = []
"""Callbacks to invoke when the simulation loop exits."""

simulation_thread: threading.Thread | None = None
"""Reference to the thread running main() when launched from the GUI."""


cables = []
"""A list storing tuples for each active cable in the simulation.
Each tuple now contains: (id, Pymunk body, Pymunk shape, CableType enum, outer_diameter).
This list is used for rendering cables and for calculations in the GUI."""
# ---

def spawn_cable(
    position: tuple[int, int],
    cable_type_to_spawn: CableType,
    outer_diameter: float = None,
    core_radius: float = None,
    sheath: float = None,
    margin: float = None,
    core_insulation_thickness: float = None,
):
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
    
    # Enforce minimum OD for multi-core geometry coverage
    # Backwards compatibility: if outer_diameter or other params not provided, compute defaults
    from cable import compute_outer_diameter_for_core_area
    if core_radius is None:
        # Use config CORE_RADIUS value
        core_radius = CORE_RADIUS
    if sheath is None:
        sheath = SHEATH_THICKNESS
    if margin is None:
        margin = MARGIN
    if core_insulation_thickness is None:
        core_insulation_thickness = CORE_INSULATION_THICKNESS
    if outer_diameter is None:
        # Assume default core area from core_radius
        core_area = math.pi * (core_radius ** 2)
        outer_diameter = compute_outer_diameter_for_core_area(
            cable_type_to_spawn, core_area, sheath, margin, core_insulation_thickness
        )
    body, shape, cable_type_obj, _returned_outer_diameter, _cr, _sh, _mg, _ci = create_cable(
        position, cable_type_to_spawn, outer_diameter, core_radius, sheath, margin, core_insulation_thickness
    )
    
    # Assign a small random horizontal velocity
    body.velocity = (random.uniform(-50, 50), 0)
    space.add(body, shape)
    
    cables.append((
        next_cable_id,
        body,
        shape,
        cable_type_obj,
        outer_diameter,
        core_radius,
        sheath,
        margin,
        core_insulation_thickness,
    )) # Store all params
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
        # Unpack safely supporting older and newer tuple formats
        cable_id = cable_data[0]
        body = cable_data[1]
        shape = cable_data[2]
        if cable_id in ids_to_remove:
            # Important: Check if body and shape are currently in the space before removing
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
        # Unpack safely; only body and shape are necessary for removal
        body = cable_data_tuple[1]
        shape = cable_data_tuple[2]
        # Check if body and shape are in space before removal to prevent errors
        if body in space.bodies:
            space.remove(body)
        if shape in space.shapes:
            space.remove(shape)
            
    cables.clear() # Clear the list of cable references
    next_cable_id = 1 # Reset ID counter

    # Conduit itself is rebuilt by update_simulation_conduit_radius if its size changes.
    # Resetting view primarily concerns cables.

def update_simulation_conduit_diameter(new_diameter: float):
    """
    Updates the conduit's internal diameter (user-facing) in the simulation.
    Converts the diameter to a radius for the physics space and rebuilds the conduit.
    """
    global current_conduit_diameter, conduit_body, conduit_segments, space
    current_conduit_diameter = new_diameter

    # Convert to radius for physics functions
    radius = current_conduit_diameter / 2.0

    # Rebuild the conduit in Pymunk space using radius
    new_body, new_segs = rebuild_conduit_in_space(
        space,
        conduit_body,
        conduit_segments,
        radius,
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        CONDUIT_SEGMENT_RADIUS,
        COLLTYPE_CONDUIT
    )
    conduit_body = new_body
    conduit_segments = new_segs


# Backwards-compatible alias: some code/tests may call update_simulation_conduit_radius
def update_simulation_conduit_radius(new_radius: float):
    """Compatibility wrapper: accept radius and update diameter accordingly."""
    # If code passes a radius, convert to diameter and call the diameter-based function
    update_simulation_conduit_diameter(new_radius * 2.0)

def set_render_zoom(new_zoom: float):
    """Set the render zoom factor, clamped to a safe range."""
    global render_zoom
    # Clamp between 0.25x and 10x to avoid extremes
    render_zoom = max(0.25, min(10.0, float(new_zoom)))


def register_exit_callback(callback):
    """Register a callback to invoke when the simulation loop exits."""
    if callback not in exit_callbacks:
        exit_callbacks.append(callback)


def set_simulation_thread(thread: threading.Thread):
    """Record the active simulation thread so callers can join it later."""
    global simulation_thread
    simulation_thread = thread


def join_simulation_thread(timeout: float | None = None):
    """Wait for the simulation thread to finish if it is running."""
    global simulation_thread
    thread = simulation_thread
    if thread and thread.is_alive():
        thread.join(timeout)
    if thread and not thread.is_alive():
        simulation_thread = None


def request_simulation_shutdown():
    """Signal the simulation loop to exit at the next opportunity."""
    shutdown_event.set()


def _notify_exit_callbacks():
    """Invoke registered exit callbacks, ignoring any individual failures."""
    for callback in list(exit_callbacks):
        try:
            callback()
        except Exception:
            pass

def main():
    """
    The main function to run the Pygame simulation.

    Initializes Pygame, sets up the display, clock, and physics space.
    It then enters the main simulation loop, handling events, stepping the physics,
    and rendering the simulation elements (conduit, cables) on the screen.
    This function is typically run in a separate thread when the GUI is active.
    """
    global conduit_body, conduit_segments, render_zoom # Ensure these are treated as global for initial setup

    shutdown_event.clear()

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Multi-Core Cable Simulation")
    clock = pygame.time.Clock()
    
    # Initial conduit setup:
    # This replaces the old add_conduit_to_space(space) call.
    # It populates the global conduit_body and conduit_segments.
    # Create initial conduit using current diameter converted to radius
    conduit_body, conduit_segments = rebuild_conduit_in_space(
        space,
        None,  # No old body to remove initially
        [],    # No old segments to remove initially
        current_conduit_diameter / 2.0,
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
        CONDUIT_SEGMENT_RADIUS,
        COLLTYPE_CONDUIT
    )
    
    running = True
    while running and not shutdown_event.is_set():
        # Event handling loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False # Exit the main loop
                shutdown_event.set()
            
            # Pass event to the input handler (manages keyboard state for cable type selection)
            input_handler.handle_event(event)
            
            # Handle zoom via mouse wheel (Pygame window)
            if event.type == pygame.MOUSEWHEEL:
                # event.y > 0 is scroll up (zoom in), < 0 is zoom out
                zoom_step = 1.1 if event.y > 0 else (1/1.1)
                set_render_zoom(render_zoom * zoom_step)
        
        # Physics simulation step
        # Step the Pymunk space multiple times per frame for stability
        for _ in range(6): # Sub-steps for physics solver
            space.step(1 / 360.0) # Small, fixed time step
        
        # Rendering
        screen.fill(BACKGROUND_COLOR)  # Clear screen with background color

        # Draw conduit using radius scaled by zoom (user-facing diameter -> radius)
        scaled_radius = (current_conduit_diameter / 2.0) * render_zoom
        scaled_thickness = max(1, int(CONDUIT_THICKNESS))
        draw_conduit(screen, CONDUIT_COLOR, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, scaled_radius, scaled_thickness)

        # Draw each cable currently in the simulation
        # Cables list now stores: (id, body, shape, cable_type_enum, outer_diameter)
        # Unpack shape as _ as it's not directly used by draw_cable.
        for _id, body, _shape, cable_type_enum, outer_diameter_val, core_radius, sheath, margin, core_ins_thick in cables:
            draw_cable(
                screen,
                body,
                cable_type_enum,
                outer_diameter_val,
                core_radius,
                sheath,
                margin,
                core_ins_thick,
                render_zoom,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
            )
        
        pygame.display.flip() # Update the full display
        clock.tick(60) # Maintain 60 frames per second
    
    pygame.quit() # Uninitialize Pygame modules
    _notify_exit_callbacks()
    shutdown_event.set()

if __name__ == "__main__":
    # This block allows main.py to be run directly, starting the simulation.
    # When used with the GUI (cable_gui.py), main() is typically called in a thread.
    main()

# Ensure rebuild_conduit_in_space is imported from physics.py at the top # REMOVED LINE
# from physics import rebuild_conduit_in_space # REMOVED LINE
