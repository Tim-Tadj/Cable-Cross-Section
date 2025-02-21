# conduit.py
import math
import pymunk
from config import *

def create_conduit_segments():
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    segments = []
    num_segments = 64
    for i in range(num_segments):
        angle1 = 2 * math.pi * i / num_segments
        angle2 = 2 * math.pi * (i + 1) / num_segments
        x1 = SCREEN_WIDTH / 2 + CONDUIT_RADIUS * math.cos(angle1)
        y1 = SCREEN_HEIGHT / 2 + CONDUIT_RADIUS * math.sin(angle1)
        x2 = SCREEN_WIDTH / 2 + CONDUIT_RADIUS * math.cos(angle2)
        y2 = SCREEN_HEIGHT / 2 + CONDUIT_RADIUS * math.sin(angle2)
        segment = pymunk.Segment(body, (x1, y1), (x2, y2), CONDUIT_THICKNESS)
        segment.friction = 0.5
        segment.elasticity = 0.4
        segment.collision_type = COLLTYPE_CONDUIT
        segments.append(segment)
    return body, segments

def draw_conduit(screen):
    pygame.draw.circle(screen, CONDUIT_COLOR, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), CONDUIT_RADIUS, CONDUIT_THICKNESS)
