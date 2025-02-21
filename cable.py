# cable.py
import math
from config import *
import pymunk

def cable_collision_handler(arbiter, space, data):
    cable_a, cable_b = arbiter.shapes
    normal = arbiter.normal
    points = arbiter.contact_point_set.points

    for point in points:
        impulse = 5.0
        cable_a.body.apply_impulse_at_world_point(
            normal * impulse, point.point_a
        )
        cable_b.body.apply_impulse_at_world_point(
            -normal * impulse, point.point_b
        )

    return True

def calculate_cable_radius(cable_type):
    if cable_type == CableType.SINGLE:
        return CORE_RADIUS + SHEATH_THICKNESS + MARGIN
    elif cable_type == CableType.THREE_CORE:
        core_center_distance = (2 * CORE_RADIUS) / math.sqrt(3)
        return core_center_distance + CORE_RADIUS + MARGIN + SHEATH_THICKNESS
    else:  # FOUR_CORE
        core_center_distance = math.sqrt(2) * CORE_RADIUS
        return core_center_distance + CORE_RADIUS + MARGIN + SHEATH_THICKNESS

def get_core_positions(cable_type, cable_radius):
    if cable_type == CableType.SINGLE:
        return [(0, 0)]
    elif cable_type == CableType.THREE_CORE:
        core_center_distance = (2 * CORE_RADIUS) / math.sqrt(3)
        angles = [0, 2 * math.pi / 3, 4 * math.pi / 3]
        return [
            (math.cos(angle) * core_center_distance, math.sin(angle) * core_center_distance)
            for angle in angles
        ]
    else:  # FOUR_CORE
        core_center_distance = math.sqrt(2) * CORE_RADIUS
        return [
            (0, -core_center_distance),
            (core_center_distance, 0),
            (0, core_center_distance),
            (-core_center_distance, 0),
        ]

def create_cable(position, cable_type):
    mass = 1
    moment = pymunk.moment_for_circle(mass, 0, calculate_cable_radius(cable_type))
    body = pymunk.Body(mass, moment)
    body.position = position

    shape = pymunk.Circle(body, calculate_cable_radius(cable_type))
    shape.friction = 0.5
    shape.elasticity = 0.4
    shape.collision_type = COLLTYPE_CABLE
    shape.filter = pymunk.ShapeFilter(categories=0b1)

    return body, shape, cable_type

def draw_cable(screen, body, cable_type):
    pos = body.position
    angle = body.angle
    cable_radius = calculate_cable_radius(cable_type)

    pygame.draw.circle(
        screen, CABLE_SHEATH_COLOR, (int(pos.x), int(pos.y)), cable_radius
    )

    pygame.draw.circle(
        screen,
        (230, 140, 0),
        (int(pos.x), int(pos.y)),
        cable_radius - SHEATH_THICKNESS,
    )

    core_positions = get_core_positions(cable_type, cable_radius)
    colors = CORE_COLORS[cable_type.value]

    for i, (offset_x, offset_y) in enumerate(core_positions):
        rotated_x = offset_x * math.cos(angle) - offset_y * math.sin(angle)
        rotated_y = offset_x * math.sin(angle) + offset_y * math.cos(angle)

        core_x = int(pos.x + rotated_x)
        core_y = int(pos.y + rotated_y)

        color = colors[i] if isinstance(colors, list) else colors
        pygame.draw.circle(screen, color, (core_x, core_y), CORE_RADIUS)
        pygame.draw.circle(
            screen, COPPER_COLOR, (core_x, core_y), CORE_RADIUS - 2
        )
