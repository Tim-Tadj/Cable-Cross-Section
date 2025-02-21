# physics.py
import pymunk
from config import COLLTYPE_CABLE, COLLTYPE_CONDUIT
from cable import cable_collision_handler
from conduit import create_conduit_segments

def setup_physics():
    space = pymunk.Space()
    space.gravity = (0.0, 981.0)
    space.damping = 0.5
    
    handler = space.add_collision_handler(COLLTYPE_CABLE, COLLTYPE_CABLE)
    handler.separate = cable_collision_handler
    
    return space

def add_conduit_to_space(space):
    body, segments = create_conduit_segments()
    space.add(body)
    for segment in segments:
        space.add(segment)
