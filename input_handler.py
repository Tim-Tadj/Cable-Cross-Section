# input_handler.py
import pygame
import math
import random
from config import CableType, SCREEN_HEIGHT, CONDUIT_RADIUS, SCREEN_WIDTH
from cable import calculate_cable_radius

class InputHandler:
    def __init__(self):
        self.current_cable_type = CableType.SINGLE
        
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.current_cable_type = CableType.SINGLE
            elif event.key == pygame.K_2:
                self.current_cable_type = CableType.THREE_CORE
            elif event.key == pygame.K_3:
                self.current_cable_type = CableType.FOUR_CORE
                
    def get_spawn_position(self):
        margin = calculate_cable_radius(self.current_cable_type) + 10
        spawn_y = SCREEN_HEIGHT / 2 - CONDUIT_RADIUS + margin * 2
        
        y_from_center = abs(spawn_y - SCREEN_HEIGHT / 2)
        available_width = math.sqrt(CONDUIT_RADIUS**2 - y_from_center**2)
        safe_width = available_width - margin * 2
        
        spawn_x = SCREEN_WIDTH / 2 + random.uniform(-safe_width / 2, safe_width / 2)
        return spawn_x, spawn_y
