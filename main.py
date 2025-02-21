# main.py
import pygame
import sys
import random
from config import *
from cable import create_cable, draw_cable
from conduit import draw_conduit
from physics import setup_physics, add_conduit_to_space
from input_handler import InputHandler

def spawn_cable():
    spawn_x, spawn_y = random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)
    body, shape, cable_type = create_cable((spawn_x, spawn_y), CableType.SINGLE)
    body.velocity = (random.uniform(-50, 50), 0)
    space.add(body, shape)
    cables.append((body, shape, cable_type))

def reset_view():
    global cables
    cables = []
    space.remove(*space.bodies, *space.shapes)
    add_conduit_to_space(space)

def main():
    global space, cables
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Multi-Core Cable Simulation")
    clock = pygame.time.Clock()
    
    space = setup_physics()
    add_conduit_to_space(space)
    
    input_handler = InputHandler()
    cables = []
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            input_handler.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                spawn_x, spawn_y = input_handler.get_spawn_position()
                body, shape, cable_type = create_cable(
                    (spawn_x, spawn_y), input_handler.current_cable_type
                )
                body.velocity = (random.uniform(-50, 50), 0)
                space.add(body, shape)
                cables.append((body, shape, cable_type))
        
        for _ in range(6):
            space.step(1 / 360.0)
        
        screen.fill(BACKGROUND_COLOR)
        draw_conduit(screen)
        
        for body, _, cable_type in cables:
            draw_cable(screen, body, cable_type)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()
