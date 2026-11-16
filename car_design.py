# this script only draws the CARS (the look of one car), nothing else
# visualizer.py asks this file for a car picture and just puts it on the screen

# how it works:
#   1. each car picture is drawn ONCE (facing right) on a big surface, then shrunk down (this makes the edges smooth)
#   2. the picture is rotated so it faces the way the car is driving
#   3. the finished pictures are saved in a cache, so the game does not redraw the car every frame

import pygame

# body colors, a car gets one of these based on its id (so a car keeps the same color the whole run)
CAR_COLORS = [
    (238, 238, 240),    # white
    (178, 184, 192),    # silver
    (196, 38, 46),      # red
    (44, 92, 182),      # blue
    (242, 190, 36),     # yellow
    (232, 118, 38),     # orange
    (28, 150, 146),     # teal
    (122, 30, 52),      # maroon
    (44, 46, 52),       # black
]

GLASS_COLOR = (40, 56, 76)
HEADLIGHT_COLOR = (255, 244, 190)
TAILLIGHT_OFF = (120, 20, 24)       # brake lights when the car is not braking
TAILLIGHT_ON = (255, 50, 40)        # brake lights when the car is braking
BRAKE_GLOW = (255, 60, 50, 90)      # the soft red glow behind the brake lights

DRAW_SCALE = 4      # the car is drawn 4x bigger first, then shrunk (smoother edges)

# the picture faces RIGHT. These angles turn it to face the way each direction drives.
# (the direction is where the car comes from, see config.py)
#   N cars come from the top and drive DOWN
#   S cars come from the bottom and drive UP
#   E cars come from the right and drive LEFT
#   W cars come from the left and drive RIGHT
ROTATION_ANGLE = {"N": 270, "S": 90, "E": 180, "W": 0}

# makes a color darker (used for outlines and the roof shade)
def darker(color, amount):
    return (max(color[0] - amount, 0), max(color[1] - amount, 0), max(color[2] - amount, 0))

def lighter(color, amount):
    return (min(color[0] + amount, 255), min(color[1] + amount, 255), min(color[2] + amount, 255))

# draws one car facing right and returns it as a picture
def draw_car_facing_right(length, width, body_color, braking):
    s = DRAW_SCALE
    big_length = length * s
    big_width = width * s
    car = pygame.Surface((big_length, big_width), pygame.SRCALPHA)

    # small helper: positions are given as a fraction of the car (0 to 1) so it works for any car size
    def box(x1, y1, x2, y2):
        left = int(x1 * big_length)
        top = int(y1 * big_width)
        return pygame.Rect(left, top, int(x2 * big_length) - left, int(y2 * big_width) - top)

    # brake glow (only while braking), drawn first so it sits behind the car
    if braking == True:
        glow = pygame.Surface((big_length, big_width), pygame.SRCALPHA)
        pygame.draw.rect(glow, BRAKE_GLOW, box(0.0, 0.0, 0.14, 1.0), border_radius=int(big_width * 0.3))
        car.blit(glow, (0, 0))

    # body (outline first, then the color slightly smaller on top)
    corner = int(big_width * 0.32)
    pygame.draw.rect(car, darker(body_color, 70), box(0.02, 0.04, 0.98, 0.96), border_radius=corner)
    pygame.draw.rect(car, body_color, box(0.045, 0.10, 0.955, 0.90), border_radius=corner)

    # hood and trunk are a little lighter than the roof
    pygame.draw.rect(car, lighter(body_color, 14), box(0.72, 0.18, 0.93, 0.82), border_radius=int(corner * 0.6))
    pygame.draw.rect(car, lighter(body_color, 14), box(0.08, 0.18, 0.25, 0.82), border_radius=int(corner * 0.6))

    # windshield (front, it gets narrower toward the front) and the back window
    windshield = [(0.56, 0.16), (0.56, 0.84), (0.70, 0.74), (0.70, 0.26)]
    rear_window = [(0.27, 0.18), (0.27, 0.82), (0.20, 0.74), (0.20, 0.26)]
    for shape in (windshield, rear_window):
        points = []
        for point in shape:
            points.append((point[0] * big_length, point[1] * big_width))
        pygame.draw.polygon(car, GLASS_COLOR, points)

    # roof (between the two windows)
    pygame.draw.rect(car, darker(body_color, 12), box(0.27, 0.17, 0.56, 0.83), border_radius=int(corner * 0.4))
    pygame.draw.rect(car, lighter(body_color, 10), box(0.30, 0.24, 0.53, 0.76), border_radius=int(corner * 0.3))

    # side mirrors
    pygame.draw.rect(car, darker(body_color, 40), box(0.60, 0.0, 0.66, 0.14), border_radius=int(corner * 0.3))
    pygame.draw.rect(car, darker(body_color, 40), box(0.60, 0.86, 0.66, 1.0), border_radius=int(corner * 0.3))

    # headlights (front = right side) and tail lights (back = left side)
    pygame.draw.rect(car, HEADLIGHT_COLOR, box(0.90, 0.14, 0.98, 0.32), border_radius=int(corner * 0.3))
    pygame.draw.rect(car, HEADLIGHT_COLOR, box(0.90, 0.68, 0.98, 0.86), border_radius=int(corner * 0.3))

    taillight_color = TAILLIGHT_OFF
    if braking == True:
        taillight_color = TAILLIGHT_ON
    pygame.draw.rect(car, taillight_color, box(0.02, 0.14, 0.09, 0.32), border_radius=int(corner * 0.3))
    pygame.draw.rect(car, taillight_color, box(0.02, 0.68, 0.09, 0.86), border_radius=int(corner * 0.3))

    # shrink it down to the real size (smoothscale = smooth edges)
    return pygame.transform.smoothscale(car, (length, width))


class CarSprites:

    def __init__(self, length, width=12):
        self.length = int(length)
        self.width = width
        self.cache = {}         # saved pictures, so each one is only drawn once

    # returns the picture for one car
    #   car_id    -> picks the color (same car = same color)
    #   direction -> "N", "S", "E" or "W", which way the picture is turned
    #   braking   -> True lights up the brake lights
    def get(self, car_id, direction, braking):
        color_index = car_id % len(CAR_COLORS)
        key = (color_index, direction, braking)

        if key not in self.cache:
            picture = draw_car_facing_right(self.length, self.width, CAR_COLORS[color_index], braking)
            self.cache[key] = pygame.transform.rotate(picture, ROTATION_ANGLE[direction])
        return self.cache[key]