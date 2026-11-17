# this script has ALL the designs (how things LOOK) in one place. It only draws, nothing else
# visualizer.py asks this file for a picture and just puts it on the screen

# what is inside:
#   1. CAR DESIGN            -> CarSprites            (the cars)
#   2. TRAFFIC LIGHT DESIGN  -> TrafficLightSprites   (the traffic lights)
#   3. ENVIRONMENT DESIGN    -> Environment           (ground, sidewalks, buildings, trees, people, vendors)

# how it works (same for everything here):
#   1. each picture is drawn ONCE on a big surface, then shrunk down (this makes the edges smooth)
#   2. the finished pictures are saved in a cache, so the game does not redraw them every frame

import math
import random
import pygame
import config

DRAW_SCALE = 4      # everything is drawn 4x bigger first, then shrunk (smoother edges)

# makes a color darker or lighter (used for outlines, shading, glow)
def darker(color, amount):
    return (max(color[0] - amount, 0), max(color[1] - amount, 0), max(color[2] - amount, 0))

def lighter(color, amount):
    return (min(color[0] + amount, 255), min(color[1] + amount, 255), min(color[2] + amount, 255))


# =====================================================================
#   1. CAR DESIGN
# =====================================================================
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

# the picture faces RIGHT. These angles turn it to face the way each direction drives.
# (the direction is where the car comes from, see config.py)
#   N cars come from the top and drive DOWN
#   S cars come from the bottom and drive UP
#   E cars come from the right and drive LEFT
#   W cars come from the left and drive RIGHT
ROTATION_ANGLE = {"N": 270, "S": 90, "E": 180, "W": 0}

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


# =====================================================================
#   2. TRAFFIC LIGHT DESIGN
# =====================================================================

# the three lamp colors (bright = the lamp that is ON)
LIGHT_COLORS = {
    "green": (40, 230, 70),
    "yellow": (255, 205, 30),
    "red": (240, 40, 40),
}

HOUSING_COLOR = (44, 46, 52)        # the box that holds the lamps
HOUSING_EDGE = (16, 16, 20)         # its outline (also used for the little visors)
HOUSING_SHINE = (78, 82, 92)        # a thin light line on the edge of the box

LIGHT_WIDTH = 18                    # size of the traffic light box, in pixels
LIGHT_HEIGHT = 42
LIGHT_PADDING = 7                   # extra space around the box, so the glow does not get cut off

# the lamps from top to bottom (like a real traffic light)
LAMP_ORDER = ["red", "yellow", "green"]
LAMP_RADIUS = 5

# draws one traffic light. active_state = "red", "yellow" or "green" (the lamp that is ON)
def draw_traffic_light(active_state):
    s = DRAW_SCALE
    width = LIGHT_WIDTH
    height = LIGHT_HEIGHT
    pad = LIGHT_PADDING
    picture = pygame.Surface(((width + 2 * pad) * s, (height + 2 * pad) * s), pygame.SRCALPHA)

    box = pygame.Rect(pad * s, pad * s, width * s, height * s)
    corner = 4 * s

    # soft shadow under the box (a little to the bottom-right)
    shadow = pygame.Surface(picture.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 80), box.move(2 * s, 2 * s), border_radius=corner)
    picture.blit(shadow, (0, 0))

    # the box (outline, then the body, then a thin shine on the inside edge)
    pygame.draw.rect(picture, HOUSING_EDGE, box, border_radius=corner)
    pygame.draw.rect(picture, HOUSING_COLOR, box.inflate(-2 * s, -2 * s), border_radius=corner - s)
    pygame.draw.rect(picture, HOUSING_SHINE, box.inflate(-2 * s, -2 * s), width=max(s // 2, 1), border_radius=corner - s)

    # the lamps
    center_x = box.centerx
    spacing = box.height / len(LAMP_ORDER)

    for index in range(len(LAMP_ORDER)):
        lamp_name = LAMP_ORDER[index]
        lamp_color = LIGHT_COLORS[lamp_name]
        center_y = int(box.top + spacing * index + spacing / 2)
        radius = LAMP_RADIUS * s

        # a dark hole behind the lamp
        pygame.draw.circle(picture, HOUSING_EDGE, (center_x, center_y), radius + s)

        if lamp_name == active_state:
            # glow around the lamp (big and faint first, then smaller and stronger)
            glow = pygame.Surface(picture.get_size(), pygame.SRCALPHA)
            for ring in range(7, 0, -1):
                ring_radius = radius + ring * s
                ring_alpha = 14 + (7 - ring) * 6
                pygame.draw.circle(glow, (lamp_color[0], lamp_color[1], lamp_color[2], ring_alpha), (center_x, center_y), ring_radius)
            picture.blit(glow, (0, 0))

            # the lamp itself, a lighter middle, and a small white shine
            pygame.draw.circle(picture, lamp_color, (center_x, center_y), radius)
            pygame.draw.circle(picture, lighter(lamp_color, 70), (center_x, center_y), int(radius * 0.6))
            pygame.draw.circle(picture, (255, 255, 255), (center_x - int(radius * 0.3), center_y - int(radius * 0.3)), max(int(radius * 0.22), 1))
        else:
            # a lamp that is OFF is just a very dark version of its color
            off_color = (lamp_color[0] // 6 + 14, lamp_color[1] // 6 + 14, lamp_color[2] // 6 + 14)
            pygame.draw.circle(picture, off_color, (center_x, center_y), radius)
            pygame.draw.circle(picture, lighter(off_color, 14), (center_x - int(radius * 0.3), center_y - int(radius * 0.3)), max(int(radius * 0.2), 1))

        # a little visor on top of the lamp (like the hoods on real traffic lights)
        visor = pygame.Rect(center_x - radius - s, center_y - radius - 2 * s, 2 * radius + 2 * s, 2 * s)
        pygame.draw.rect(picture, HOUSING_EDGE, visor, border_radius=s)

    # shrink it down to the real size (smoothscale = smooth edges)
    final_size = (width + 2 * pad, height + 2 * pad)
    return pygame.transform.smoothscale(picture, final_size)


class TrafficLightSprites:

    def __init__(self):
        self.cache = {}         # saved pictures, so each one is only drawn once

    # returns the picture for a traffic light that is "red", "yellow" or "green"
    # the picture is centered on the light's position
    # direction "E" and "W" lights lie sideways (they stand along the left-right road), "N" and "S" stand up
    def get(self, state, direction="N"):
        sideways = (direction == "E" or direction == "W")
        key = (state, sideways)
        if key not in self.cache:
            picture = draw_traffic_light(state)
            if sideways == True:
                picture = pygame.transform.rotate(picture, 90)
            self.cache[key] = picture
        return self.cache[key]


# =====================================================================
#   3. ENVIRONMENT DESIGN  (ground, roads, buildings, trees, people...)
# =====================================================================
# Everything that does NOT move for the simulation, but makes the scene look alive.
# It has 2 kinds of things:
#   - STILL things (ground, roads, sidewalks, buildings, bushes): drawn ONE time into a big background picture
#   - MOVING things (trees swaying, people, vendors, a dog...): drawn every frame, but they are small and cheap
# Nothing here is saved in the simulation, so it never changes the results (the metrics).

SIZE = config.SCREEN_SIZE
CENTER = config.CENTER
HALF = config.HALF_ROAD
NEAR = CENTER - HALF            # the top / left edge of the intersection box
FAR = CENTER + HALF             # the bottom / right edge of the intersection box

SIDEWALK_WIDTH = 26             # visualizer.py uses this too, so the traffic lights stand on the sidewalk

# ground and road colors
GRASS_COLORS = [(52, 146, 58), (60, 156, 64), (46, 136, 54), (68, 160, 70)]
DIRT_COLOR = (142, 120, 82)
ROAD_COLOR = (60, 60, 62)
LINE_COLOR = (230, 230, 230)
SIDEWALK_COLOR = (188, 182, 172)
SIDEWALK_TILE_LINE = (164, 158, 148)
CURB_COLOR = (222, 218, 208)
CONCRETE_COLOR = (170, 166, 156)
SHADOW_COLOR = (0, 0, 0, 62)    # the last number = how see-through the shadows are

# colors for the buildings and the people
GI_ROOF_COLORS = [(178, 74, 60), (88, 128, 164), (92, 142, 96), (190, 190, 196), (196, 148, 78), (140, 96, 150)]
PARAPET_COLORS = [(204, 122, 108), (120, 170, 204), (232, 202, 120), (150, 190, 140), (214, 214, 220)]
TARP_COLORS = [(52, 112, 200), (232, 120, 40), (60, 160, 90), (214, 56, 60), (240, 196, 50)]
AWNING_PAIRS = [((214, 56, 60), (245, 245, 245)), ((52, 112, 200), (245, 245, 245)), ((240, 196, 50), (214, 56, 60)), ((60, 160, 90), (245, 245, 245))]
SHIRT_COLORS = [(210, 60, 60), (60, 110, 200), (240, 200, 60), (70, 170, 100), (230, 130, 50),
                (150, 80, 170), (238, 238, 238), (44, 44, 54), (220, 100, 150), (60, 170, 180)]
SKIN_COLORS = [(240, 200, 160), (224, 172, 130), (198, 146, 104), (160, 108, 72)]
HAIR_COLORS = [(24, 20, 18), (40, 28, 20), (62, 42, 26), (18, 18, 24)]
PANTS_COLORS = [(50, 60, 90), (70, 70, 80), (92, 72, 52), (40, 40, 46)]

# the buildings: (kind, x, y, width, height, extra options)
# the 4 green corners of the map each get their own buildings. ("side" = the side that faces the road)
BUILDINGS = [
    # top-left corner (the info text is drawn on top of the top-left, so nothing important is up there)
    ("court", 16, 108, 164, 96, {}),
    ("house", 200, 112, 96, 74, {}),
    ("store", 200, 214, 96, 66, {"side": "S"}),
    ("house", 16, 228, 84, 62, {}),
    ("flats", 112, 222, 74, 68, {}),
    # top-right corner
    ("hall", 516, 36, 150, 96, {}),
    ("chapel", 704, 44, 70, 96, {}),
    ("house", 516, 196, 92, 72, {}),
    ("store", 636, 208, 128, 66, {"side": "S"}),
    # bottom-left corner
    ("flats", 16, 526, 112, 86, {}),
    ("house", 150, 530, 108, 70, {}),
    ("store", 16, 650, 112, 70, {"side": "N"}),
    ("house", 158, 640, 100, 80, {}),
    # bottom-right corner (a small market + houses)
    ("stall", 520, 528, 56, 40, {}),
    ("stall", 586, 528, 56, 40, {}),
    ("stall", 652, 528, 56, 40, {}),
    ("stall", 718, 528, 56, 40, {}),
    ("flats", 520, 650, 120, 90, {}),
    ("house", 666, 656, 108, 72, {}),
]

# paved areas in front of buildings: (x, y, width, height)
PLAZAS = [
    (516, 132, 150, 38),        # in front of the barangay hall
    (692, 140, 94, 46),         # in front of the chapel
]

# street vendors: (x, y, "h" or "v" = which way the sidewalk goes, kind of cart)
VENDORS = [
    (80, 327, "h", "pot"), (200, 327, "h", "fruit"),
    (473, 100, "v", "drink"), (660, 327, "h", "pot"),
    (560, 473, "h", "fruit"), (473, 650, "v", "pot"),
    (327, 580, "v", "drink"), (110, 473, "h", "pot"),
]

# people sitting on the curb: (x, y, which way they look) (look: "up", "down", "left", "right")
SEATED = [
    (327, 140, "right"), (327, 154, "right"),
    (473, 172, "left"), (473, 186, "left"),
    (590, 327, "down"), (604, 327, "down"),
    (640, 473, "up"), (654, 473, "up"),
    (327, 700, "right"), (327, 714, "right"),
    (210, 473, "up"), (224, 473, "up"),
    (140, 327, "down"),
]

# people standing around (chatting, buying from the stores and the market): (x, y, which way they look)
STANDING = [
    (232, 303, "up"), (247, 301, "up"),
    (676, 299, "up"), (692, 297, "up"),
    (48, 629, "down"), (63, 631, "down"),
    (606, 150, "right"), (619, 152, "left"),
    (548, 594, "up"), (606, 592, "up"), (690, 596, "up"), (744, 592, "up"),
    (720, 168, "up"), (738, 172, "up"), (756, 166, "left"),
    (120, 300, "up"),
]

# people walking on the sidewalk, back and forth: (x1, y1, x2, y2)
WALKER_PATHS = [
    (327, 190, 327, 270), (473, 235, 473, 290), (473, 535, 473, 620),
    (700, 473, 790, 473), (327, 625, 327, 680), (40, 473, 95, 473),
    (540, 327, 620, 327),
]
DOG_PATH = (480, 125, 480, 290)

# poles for the electric wires: (which way the sidewalk goes, x or y of the pole line, from, to)
POLE_LINES = [
    ("v", 318, 0, 300), ("v", 482, 0, 300), ("v", 318, 500, 800), ("v", 482, 500, 800),
    ("h", 318, 0, 300), ("h", 318, 500, 800), ("h", 482, 0, 300), ("h", 482, 500, 800),
]

# which way a person looks -> the angle to turn the picture (the pictures face UP by default)
LOOK_ANGLES = {"up": 0, "left": 90, "down": 180, "right": 270}


# ---------- small helpers ----------

# draws something at 4x size, then shrinks it (smooth edges). draw_function(big_surface, scale)
def make_picture(width, height, draw_function):
    s = DRAW_SCALE
    big = pygame.Surface((int(width * s), int(height * s)), pygame.SRCALPHA)
    draw_function(big, s)
    return pygame.transform.smoothscale(big, (int(width), int(height)))

# a circle, but the numbers can have decimals
def big_circle(surface, color, x, y, radius, width=0):
    pygame.draw.circle(surface, color, (int(x), int(y)), max(int(radius), 1), width)

# an ellipse from its center and size (in normal pixels, s = scale)
def big_ellipse(surface, color, s, x, y, w, h):
    pygame.draw.ellipse(surface, color, (int((x - w / 2) * s), int((y - h / 2) * s), int(w * s), int(h * s)))

# True if a circle touches a rectangle (used to keep trees away from roads and buildings)
def circle_hits_rect(x, y, radius, rect):
    nearest_x = max(rect.left, min(x, rect.right))
    nearest_y = max(rect.top, min(y, rect.bottom))
    return (x - nearest_x) ** 2 + (y - nearest_y) ** 2 < radius ** 2

# the angle (for pygame rotate, picture facing UP) for a walking direction
def angle_for_heading(hx, hy):
    return math.degrees(math.atan2(-hx, -hy))

def get_road_rects():
    return [pygame.Rect(NEAR, 0, 2 * HALF, SIZE), pygame.Rect(0, NEAR, SIZE, 2 * HALF)]

# the 8 sidewalk pieces (along both roads, on both sides). they meet at the 4 corners of the intersection
def get_sidewalk_rects():
    w = SIDEWALK_WIDTH
    return [
        pygame.Rect(NEAR - w, 0, w, NEAR), pygame.Rect(NEAR - w, FAR, w, SIZE - FAR),
        pygame.Rect(FAR, 0, w, NEAR), pygame.Rect(FAR, FAR, w, SIZE - FAR),
        pygame.Rect(0, NEAR - w, NEAR, w), pygame.Rect(FAR, NEAR - w, SIZE - FAR, w),
        pygame.Rect(0, FAR, NEAR, w), pygame.Rect(FAR, FAR, SIZE - FAR, w),
    ]

# a soft shadow behind a box (the light comes from the top-left, so the shadow falls to the bottom-right)
def add_box_shadow(layer, rect, depth):
    x, y, w, h = rect
    points = [(x, y), (x + w, y), (x + w + depth, y + depth), (x + w + depth, y + h + depth), (x + depth, y + h + depth), (x, y + h)]
    pygame.draw.polygon(layer, SHADOW_COLOR, points)


# ---------- ground, roads, sidewalks ----------

def draw_ground(surface, rng):
    surface.fill(GRASS_COLORS[0])

    # big soft patches in slightly different greens
    for i in range(650):
        color = rng.choice(GRASS_COLORS)
        pygame.draw.circle(surface, color, (rng.randint(0, SIZE), rng.randint(0, SIZE)), rng.randint(8, 26))

    # a few bare dirt patches (a softer ring first, then the dirt)
    for i in range(9):
        x = rng.randint(0, SIZE)
        y = rng.randint(0, SIZE)
        w = rng.randint(30, 70)
        h = rng.randint(18, 40)
        ring = (96, 128, 70)
        pygame.draw.ellipse(surface, ring, (x - w // 2 - 5, y - h // 2 - 4, w + 10, h + 8))
        pygame.draw.ellipse(surface, DIRT_COLOR, (x - w // 2, y - h // 2, w, h))

    # tiny blades of grass
    for i in range(2600):
        x = rng.randint(0, SIZE)
        y = rng.randint(0, SIZE)
        base = rng.choice(GRASS_COLORS)
        if rng.random() < 0.5:
            color = darker(base, 22)
        else:
            color = lighter(base, 22)
        pygame.draw.line(surface, color, (x, y), (x + rng.randint(-1, 1), y - rng.randint(2, 4)))

def draw_roads(surface, rng):
    for road in get_road_rects():
        pygame.draw.rect(surface, ROAD_COLOR, road)

    # a little roughness on the asphalt
    for i in range(2200):
        x = rng.randint(0, SIZE)
        y = rng.randint(0, SIZE)
        inside_road = (NEAR <= x <= FAR) or (NEAR <= y <= FAR)
        if inside_road:
            shade = rng.randint(-7, 7)
            surface.set_at((x, y), (ROAD_COLOR[0] + shade, ROAD_COLOR[1] + shade, ROAD_COLOR[2] + shade))

def draw_sidewalks(surface):
    for rect in get_sidewalk_rects():
        pygame.draw.rect(surface, SIDEWALK_COLOR, rect)

        # tile lines (every 18 pixels)
        if rect.height > rect.width:
            for y in range(rect.top, rect.bottom, 18):
                pygame.draw.line(surface, SIDEWALK_TILE_LINE, (rect.left, y), (rect.right - 1, y))
        else:
            for x in range(rect.left, rect.right, 18):
                pygame.draw.line(surface, SIDEWALK_TILE_LINE, (x, rect.top), (x, rect.bottom - 1))

    # the curb = the light strip right next to the road
    for rect in [pygame.Rect(NEAR - 3, 0, 3, NEAR), pygame.Rect(NEAR - 3, FAR, 3, SIZE - FAR),
                 pygame.Rect(FAR, 0, 3, NEAR), pygame.Rect(FAR, FAR, 3, SIZE - FAR),
                 pygame.Rect(0, NEAR - 3, NEAR, 3), pygame.Rect(FAR, NEAR - 3, SIZE - FAR, 3),
                 pygame.Rect(0, FAR, NEAR, 3), pygame.Rect(FAR, FAR, SIZE - FAR, 3)]:
        pygame.draw.rect(surface, CURB_COLOR, rect)

    # a thin dark edge where the sidewalk meets the grass
    edge = (150, 144, 134)
    w = SIDEWALK_WIDTH
    pygame.draw.line(surface, edge, (NEAR - w, 0), (NEAR - w, NEAR - w))
    pygame.draw.line(surface, edge, (NEAR - w, FAR + w), (NEAR - w, SIZE))
    pygame.draw.line(surface, edge, (FAR + w, 0), (FAR + w, NEAR - w))
    pygame.draw.line(surface, edge, (FAR + w, FAR + w), (FAR + w, SIZE))
    pygame.draw.line(surface, edge, (0, NEAR - w), (NEAR - w, NEAR - w))
    pygame.draw.line(surface, edge, (FAR + w, NEAR - w), (SIZE, NEAR - w))
    pygame.draw.line(surface, edge, (0, FAR + w), (NEAR - w, FAR + w))
    pygame.draw.line(surface, edge, (FAR + w, FAR + w), (SIZE, FAR + w))

def draw_road_markings(surface):
    # dashed center lines (skipped inside the intersection box)
    for spot in range(0, SIZE, 30):
        inside_intersection = (spot >= NEAR and spot <= FAR)
        if inside_intersection == False:
            pygame.draw.line(surface, LINE_COLOR, (CENTER, spot), (CENTER, spot + 15), 2)
            pygame.draw.line(surface, LINE_COLOR, (spot, CENTER), (spot + 15, CENTER), 2)

    # stop lines, one for each direction
    pygame.draw.line(surface, LINE_COLOR, (NEAR, NEAR), (CENTER, NEAR), 4)     # North
    pygame.draw.line(surface, LINE_COLOR, (CENTER, FAR), (FAR, FAR), 4)        # South
    pygame.draw.line(surface, LINE_COLOR, (FAR, NEAR), (FAR, CENTER), 4)       # East
    pygame.draw.line(surface, LINE_COLOR, (NEAR, CENTER), (NEAR, FAR), 4)      # West

    # zebra crossings, just inside the 4 edges of the intersection box (after the stop lines)
    bar = 8
    step = 14
    depth = 14
    inset = 5
    position = NEAR + 3
    while position + bar <= FAR - 3:
        pygame.draw.rect(surface, LINE_COLOR, (position, NEAR - inset -depth, bar, depth))             # top
        pygame.draw.rect(surface, LINE_COLOR, (position, FAR + inset, bar, depth))      # bottom
        pygame.draw.rect(surface, LINE_COLOR, (NEAR - inset - depth, position, depth, bar))             # left
        pygame.draw.rect(surface, LINE_COLOR, (FAR + inset, position, depth, bar))      # right
        position += step


# ---------- buildings (all drawn from above) ----------

# a roof made of corrugated sheets (GI sheet). It has a ridge down the middle: one side lighter, one darker
def draw_gable_roof(surface, rect, color, rng):
    pygame.draw.rect(surface, darker(color, 60), rect)          # the edge of the roof
    roof = rect.inflate(-4, -4)
    light_side = lighter(color, 14)
    dark_side = darker(color, 18)

    if roof.width >= roof.height:
        middle = roof.top + roof.height // 2
        pygame.draw.rect(surface, light_side, (roof.left, roof.top, roof.width, middle - roof.top))
        pygame.draw.rect(surface, dark_side, (roof.left, middle, roof.width, roof.bottom - middle))
        for x in range(roof.left + 3, roof.right, 5):           # the corrugated lines
            pygame.draw.line(surface, darker(light_side, 22), (x, roof.top), (x, middle - 2))
            pygame.draw.line(surface, darker(dark_side, 22), (x, middle + 2), (x, roof.bottom - 1))
        pygame.draw.line(surface, lighter(color, 60), (roof.left, middle), (roof.right - 1, middle), 3)
    else:
        middle = roof.left + roof.width // 2
        pygame.draw.rect(surface, light_side, (roof.left, roof.top, middle - roof.left, roof.height))
        pygame.draw.rect(surface, dark_side, (middle, roof.top, roof.right - middle, roof.height))
        for y in range(roof.top + 3, roof.bottom, 5):
            pygame.draw.line(surface, darker(light_side, 22), (roof.left, y), (middle - 2, y))
            pygame.draw.line(surface, darker(dark_side, 22), (middle + 2, y), (roof.right - 1, y))
        pygame.draw.line(surface, lighter(color, 60), (middle, roof.top), (middle, roof.bottom - 1), 3)

    # a few rusty spots, so the roof does not look brand new
    for i in range(rng.randint(2, 4)):
        w = rng.randint(6, 13)
        h = rng.randint(4, 8)
        x = rng.randint(roof.left + 2, max(roof.right - w - 2, roof.left + 3))
        y = rng.randint(roof.top + 2, max(roof.bottom - h - 2, roof.top + 3))
        rust = ((color[0] + 150) // 2, (color[1] + 88) // 2, (color[2] + 60) // 2)
        pygame.draw.rect(surface, rust, (x, y, w, h))

    # something small on the roof (sometimes)
    extra = rng.choice(["tank", "dish", "none", "none"])
    if extra == "tank":
        big_circle(surface, (36, 44, 60), roof.right - 10, roof.top + 10, 5)
        big_circle(surface, (90, 110, 140), roof.right - 11, roof.top + 9, 2)
    elif extra == "dish":
        big_circle(surface, (225, 225, 230), roof.left + 10, roof.bottom - 10, 4)
        pygame.draw.line(surface, (110, 110, 118), (roof.left + 10, roof.bottom - 10), (roof.left + 14, roof.bottom - 14), 2)

# a concrete building with a flat roof (water tank, stairs, aircon boxes)
def draw_flat_roof(surface, rect, parapet_color, rng):
    pygame.draw.rect(surface, parapet_color, rect)
    roof = rect.inflate(-8, -8)
    pygame.draw.rect(surface, (176, 176, 182), roof)

    for i in range(4):                                          # old stains on the concrete
        w = rng.randint(10, 22)
        h = rng.randint(8, 16)
        x = rng.randint(roof.left, max(roof.right - w, roof.left + 1))
        y = rng.randint(roof.top, max(roof.bottom - h, roof.top + 1))
        pygame.draw.rect(surface, (164, 164, 170), (x, y, w, h))

    pygame.draw.rect(surface, (146, 146, 154), (roof.left + 6, roof.top + 6, 18, 14))      # the stairs house
    pygame.draw.rect(surface, (120, 120, 128), (roof.left + 6, roof.top + 6, 18, 14), 2)
    big_circle(surface, (40, 78, 120), roof.right - 14, roof.top + 14, 9)                  # the water tank
    big_circle(surface, (70, 110, 156), roof.right - 14, roof.top + 14, 6)
    big_circle(surface, (150, 186, 220), roof.right - 16, roof.top + 12, 2)
    for i in range(2):                                          # aircon boxes with a fan
        x = roof.left + 8 + i * 16
        y = roof.bottom - 16
        pygame.draw.rect(surface, (212, 212, 216), (x, y, 12, 9))
        big_circle(surface, (96, 96, 104), x + 6, y + 4, 3)

# a small shop. The striped awning sticks out on the side that faces the road
def draw_store(surface, shadow_layer, rect, roof_color, side, rng):
    draw_gable_roof(surface, rect, roof_color, rng)
    colors = rng.choice(AWNING_PAIRS)
    depth = 12

    if side == "S":
        awning = pygame.Rect(rect.left + 4, rect.bottom, rect.width - 8, depth)
    elif side == "N":
        awning = pygame.Rect(rect.left + 4, rect.top - depth, rect.width - 8, depth)
    elif side == "E":
        awning = pygame.Rect(rect.right, rect.top + 4, depth, rect.height - 8)
    else:
        awning = pygame.Rect(rect.left - depth, rect.top + 4, depth, rect.height - 8)

    add_box_shadow(shadow_layer, awning, 3)
    along_x = (side == "S" or side == "N")
    start = awning.left if along_x else awning.top
    end = awning.right if along_x else awning.bottom
    index = 0
    for position in range(start, end, 6):
        stripe = colors[index % 2]
        size = min(6, end - position)
        if along_x:
            pygame.draw.rect(surface, stripe, (position, awning.top, size, awning.height))
        else:
            pygame.draw.rect(surface, stripe, (awning.left, position, awning.width, size))
        index = index + 1
    pygame.draw.rect(surface, darker(colors[0], 70), awning, 1)

    # a sign on the roof
    if along_x:
        pygame.draw.rect(surface, (250, 232, 120), (rect.left + 10, rect.top + 6, 22, 7))
        pygame.draw.rect(surface, (180, 60, 50), (rect.left + 10, rect.top + 6, 22, 7), 1)

def draw_chapel(surface, rect, rng):
    pygame.draw.rect(surface, (150, 150, 158), rect)
    roof = rect.inflate(-4, -4)
    middle = roof.left + roof.width // 2
    pygame.draw.rect(surface, (236, 236, 240), (roof.left, roof.top, middle - roof.left, roof.height))
    pygame.draw.rect(surface, (206, 206, 214), (middle, roof.top, roof.right - middle, roof.height))
    pygame.draw.line(surface, (252, 252, 252), (middle, roof.top), (middle, roof.bottom - 1), 3)

    # a cross lying on the roof
    cross_y = roof.top + roof.height // 3
    pygame.draw.rect(surface, (96, 104, 140), (middle - 2, cross_y - 14, 4, 28))
    pygame.draw.rect(surface, (96, 104, 140), (middle - 9, cross_y - 6, 18, 4))

    # the bell tower in front (a square tower with a pointy roof)
    tower = pygame.Rect(middle - 11, roof.bottom - 20, 22, 22)
    pygame.draw.rect(surface, (214, 210, 200), tower)
    pygame.draw.rect(surface, (150, 146, 138), tower, 2)
    pygame.draw.line(surface, (150, 146, 138), tower.topleft, tower.bottomright)
    pygame.draw.line(surface, (150, 146, 138), tower.topright, tower.bottomleft)
    big_circle(surface, (120, 116, 108), tower.centerx, tower.centery, 2)

def draw_hall(surface, rect, rng):
    pygame.draw.rect(surface, (40, 96, 104), rect)
    roof = rect.inflate(-6, -6)
    middle = roof.top + roof.height // 2
    pygame.draw.rect(surface, (74, 150, 160), (roof.left, roof.top, roof.width, middle - roof.top))
    pygame.draw.rect(surface, (56, 124, 134), (roof.left, middle, roof.width, roof.bottom - middle))
    for x in range(roof.left + 3, roof.right, 6):
        pygame.draw.line(surface, (50, 116, 126), (x, roof.top), (x, middle - 2))
        pygame.draw.line(surface, (42, 102, 112), (x, middle + 2), (x, roof.bottom - 1))
    pygame.draw.line(surface, (150, 210, 216), (roof.left, middle), (roof.right - 1, middle), 3)

    # the front porch with columns
    porch = pygame.Rect(rect.centerx - 28, rect.bottom, 56, 10)
    pygame.draw.rect(surface, (226, 222, 212), porch)
    for x in (porch.left + 4, porch.centerx, porch.right - 4):
        big_circle(surface, (150, 146, 138), x, porch.bottom - 3, 2)

    # a sign on the roof
    pygame.draw.rect(surface, (240, 240, 240), (rect.centerx - 22, roof.top + 8, 44, 10))
    pygame.draw.rect(surface, (30, 70, 160), (rect.centerx - 22, roof.top + 8, 44, 10), 2)

# a basketball court, with a concrete area around it
def draw_court(surface, rect):
    pygame.draw.rect(surface, CONCRETE_COLOR, rect.inflate(14, 14))
    pygame.draw.rect(surface, (52, 108, 156), rect)
    white = (240, 240, 240)
    inner = rect.inflate(-10, -10)
    pygame.draw.rect(surface, white, inner, 2)
    pygame.draw.line(surface, white, (rect.centerx, inner.top), (rect.centerx, inner.bottom), 2)
    pygame.draw.circle(surface, white, rect.center, int(rect.height * 0.17), 2)
    key_w = int(rect.width * 0.17)
    key_h = int(rect.height * 0.38)
    for key_x in (inner.left, inner.right - key_w):             # the painted areas under each hoop
        key = pygame.Rect(key_x, rect.centery - key_h // 2, key_w, key_h)
        pygame.draw.rect(surface, (196, 70, 60), key)
        pygame.draw.rect(surface, white, key, 2)
    for hoop_x, rim_x in ((inner.left + 2, inner.left + 9), (inner.right - 4, inner.right - 11)):
        pygame.draw.rect(surface, (250, 250, 250), (hoop_x, rect.centery - 8, 3, 16))      # backboard
        big_circle(surface, (240, 120, 30), rim_x, rect.centery, 3, 2)                      # the ring

# a market stall: a colored tarp with a little crate of fruits in front
def draw_stall(surface, shadow_layer, rect, color, rng):
    add_box_shadow(shadow_layer, rect, 5)
    pygame.draw.rect(surface, darker(color, 50), rect)
    tarp = rect.inflate(-3, -3)
    pygame.draw.rect(surface, color, tarp)
    surface.set_clip(tarp)                                      # so the stripes stay inside the tarp
    for x in range(tarp.left - tarp.height, tarp.right, 10):    # diagonal stripes on the tarp
        pygame.draw.line(surface, lighter(color, 36), (x, tarp.bottom - 1), (x + tarp.height, tarp.top), 4)
    surface.set_clip(None)
    pygame.draw.rect(surface, darker(color, 50), rect, 2)
    for corner in (rect.topleft, rect.topright, rect.bottomleft, rect.bottomright):        # the poles
        big_circle(surface, (96, 66, 44), corner[0], corner[1], 2)

    # crates of fruits and vegetables in front of the stall
    crates = pygame.Rect(rect.left + 3, rect.bottom + 1, rect.width - 6, 9)
    pygame.draw.rect(surface, (150, 108, 66), crates)
    for x in range(crates.left + 3, crates.right - 3, 6):
        fruit = rng.choice([(232, 80, 60), (250, 200, 50), (120, 190, 70), (240, 140, 50), (150, 60, 140)])
        big_circle(surface, fruit, x + 2, crates.centery, 2)
        big_circle(surface, lighter(fruit, 50), x + 1, crates.centery - 1, 1)

def draw_yard(surface, rect, color):
    pygame.draw.rect(surface, color, rect, border_radius=3)
    pygame.draw.rect(surface, darker(color, 24), rect, 1, border_radius=3)


# ---------- people, vendors, trees (small pictures, drawn once and reused) ----------

# one person from above (head and shoulders). The picture faces UP. seated = legs stretched out in front
def draw_person_picture(shirt, skin, hair, pants, seated):
    size = 28
    mid = size / 2

    def draw(big, s):
        if seated:
            for side in (-1, 1):
                big_ellipse(big, pants, s, mid + side * 3.2, mid - 6.5, 4.4, 10)     # legs
                big_ellipse(big, (30, 30, 34), s, mid + side * 3.2, mid - 12.0, 4.4, 3.2)    # shoes
        for side in (-1, 1):
            big_ellipse(big, darker(shirt, 30), s, mid + side * 7.2, mid + 0.5, 3.4, 7)      # arms
        big_ellipse(big, darker(shirt, 40), s, mid, mid + 1, 15, 8.4)
        big_ellipse(big, shirt, s, mid, mid + 1, 14, 7.4)                                    # shoulders
        big_ellipse(big, hair, s, mid, mid - 0.3, 7.4, 7.4)                                  # head (hair)
        big_ellipse(big, skin, s, mid, mid - 2.4, 4.6, 3.0)                                  # face
    return make_picture(size, size, draw)

# a street vendor's umbrella from above (colored pie slices)
def draw_umbrella_picture(color_1, color_2):
    size = 30

    def draw(big, s):
        c = size * s / 2
        r = 13 * s
        for i in range(8):
            a_start = 2 * math.pi * i / 8
            a_end = 2 * math.pi * (i + 1) / 8
            points = [(c, c)]
            for k in range(7):
                a = a_start + (a_end - a_start) * k / 6
                points.append((c + r * math.cos(a), c + r * math.sin(a)))
            if i % 2 == 0:
                pygame.draw.polygon(big, color_1, points)
            else:
                pygame.draw.polygon(big, color_2, points)
        for i in range(8):                                       # the ribs
            a = 2 * math.pi * i / 8
            pygame.draw.line(big, (70, 60, 56), (c, c), (c + r * math.cos(a), c + r * math.sin(a)), max(s // 2, 1))
        big_circle(big, darker(color_1, 90), c, c, r, max(s // 2, 1) + 1)
        big_circle(big, (70, 60, 52), c, c, 2 * s)
    return make_picture(size, size, draw)

# a vendor's cart, lying along the x direction (turned later if the sidewalk goes up-down)
def draw_cart_picture(kind):
    w = 26
    h = 14

    def draw(big, s):
        def box(x, y, bw, bh, color):
            pygame.draw.rect(big, color, (int(x * s), int(y * s), int(bw * s), int(bh * s)), border_radius=int(s))

        for wheel_x in (4, 17):                                  # wheels
            box(wheel_x, 0, 5, 2, (30, 30, 32))
            box(wheel_x, h - 2, 5, 2, (30, 30, 32))

        if kind == "pot":
            box(1, 2, 24, 10, (172, 176, 184))
            box(1, 2, 24, 10, (172, 176, 184))
            big_circle(big, (70, 72, 80), 8 * s, 7 * s, 4.4 * s)
            big_circle(big, (210, 124, 52), 8 * s, 7 * s, 3.1 * s)
            for row in range(4):                                 # a tray of skewers
                box(14, 3.5 + row * 2.2, 9, 1, (236, 214, 160))
        elif kind == "fruit":
            box(1, 2, 24, 10, (140, 100, 62))
            fruit_colors = [(232, 80, 60), (250, 200, 50), (120, 190, 70), (240, 140, 50)]
            for i in range(4):
                box(2.2 + i * 5.7, 3, 5, 8, (176, 130, 80))
                for k in range(3):
                    big_circle(big, fruit_colors[i], (4.7 + i * 5.7) * s, (4.6 + k * 2.6) * s, 1.15 * s)
        else:
            box(1, 2, 24, 10, (66, 116, 176))
            jar_colors = [(255, 196, 64), (240, 110, 150), (110, 200, 230)]
            for i in range(3):
                big_circle(big, (240, 240, 244), (6 + i * 7) * s, 7 * s, 3.2 * s)
                big_circle(big, jar_colors[i], (6 + i * 7) * s, 7 * s, 2.4 * s)
    return make_picture(w, h, draw)

# a dog from above, facing RIGHT
def draw_dog_picture():
    def draw(big, s):
        big_ellipse(big, (150, 102, 62), s, 8, 6, 11, 5.4)       # body
        big_ellipse(big, (120, 80, 48), s, 2.5, 6, 4, 2)         # tail
        big_circle(big, (150, 102, 62), 13.5 * s, 6 * s, 2.7 * s)  # head
        big_ellipse(big, (96, 62, 36), s, 12.4, 3.6, 2.4, 1.6)   # ears
        big_ellipse(big, (96, 62, 36), s, 12.4, 8.4, 2.4, 1.6)
        big_circle(big, (30, 24, 22), 16 * s, 6 * s, 0.9 * s)    # nose
    return make_picture(18, 12, draw)

# a tree with a round top (mango tree and the like)
def draw_broadleaf_picture(radius, seed):
    rng = random.Random(seed)
    size = radius * 2 + 6

    def draw(big, s):
        c = size * s / 2
        big_circle(big, (28, 92, 42), c, c, radius * s)
        for i in range(10):
            angle = rng.uniform(0, 2 * math.pi)
            distance = rng.uniform(0, radius * 0.55)
            blob = rng.uniform(radius * 0.32, radius * 0.5)
            shade = rng.choice([(36, 108, 50), (44, 122, 58), (34, 100, 46), (56, 138, 68)])
            big_circle(big, shade, c + math.cos(angle) * distance * s, c + math.sin(angle) * distance * s, blob * s)
        for i in range(5):                                       # light spots (the sun hits the top-left)
            big_circle(big, (92, 172, 92), c - radius * rng.uniform(0.1, 0.5) * s, c - radius * rng.uniform(0.1, 0.5) * s, radius * 0.17 * s)
        for i in range(rng.randint(0, 5)):                       # fruits
            angle = rng.uniform(0, 2 * math.pi)
            distance = rng.uniform(0, radius * 0.75)
            big_circle(big, (240, 196, 60), c + math.cos(angle) * distance * s, c + math.sin(angle) * distance * s, 1.1 * s)
        big_circle(big, (20, 66, 34), c, c, radius * s, int(1.6 * s))
    return make_picture(size, size, draw)

# a coconut palm from above (long leaves going out from the middle)
def draw_palm_picture(radius, seed):
    rng = random.Random(seed)
    size = radius * 2 + 6

    def draw(big, s):
        c = size * s / 2
        leaves = 9
        for i in range(leaves):
            angle = 2 * math.pi * i / leaves + rng.uniform(-0.12, 0.12)
            length = radius * rng.uniform(0.86, 1.0) * s
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            side = radius * 0.2 * s
            tip = (c + cos_a * length, c + sin_a * length)
            middle = (c + cos_a * length * 0.55, c + sin_a * length * 0.55)
            points = [(c, c), (middle[0] - sin_a * side, middle[1] + cos_a * side), tip, (middle[0] + sin_a * side, middle[1] - cos_a * side)]
            pygame.draw.polygon(big, (36, 126, 58), points)
            pygame.draw.line(big, (118, 192, 98), (c, c), tip, s)
        big_circle(big, (112, 84, 56), c, c, 3 * s)
        for i in range(3):                                       # coconuts
            angle = 2 * math.pi * i / 3 + 0.5
            big_circle(big, (88, 58, 30), c + math.cos(angle) * 2.4 * s, c + math.sin(angle) * 2.4 * s, 1.7 * s)
    return make_picture(size, size, draw)

# a small bush (some have flowers)
def draw_bush_picture(radius, seed):
    rng = random.Random(seed)
    size = radius * 2 + 4

    def draw(big, s):
        c = size * s / 2
        for i in range(4):
            angle = rng.uniform(0, 2 * math.pi)
            big_circle(big, rng.choice([(30, 100, 46), (40, 118, 56), (50, 132, 62)]),
                       c + math.cos(angle) * radius * 0.35 * s, c + math.sin(angle) * radius * 0.35 * s, radius * 0.62 * s)
        flower = rng.choice([None, None, (236, 92, 146), (250, 210, 70), (230, 70, 70)])
        if flower is not None:
            for i in range(7):
                angle = rng.uniform(0, 2 * math.pi)
                distance = rng.uniform(0, radius * 0.7)
                big_circle(big, flower, c + math.cos(angle) * distance * s, c + math.sin(angle) * distance * s, 1.2 * s)
    return make_picture(size, size, draw)


# ---------- the whole environment ----------

class Environment:

    def __init__(self, seed=7):
        self.rng = random.Random(seed)      # same seed = the same town every time
        self.cache = {}                     # saved pictures

        # people: every person gets a random look, picked once
        self.vendors = []
        for x, y, axis, kind in VENDORS:
            self.vendors.append(self.make_vendor(x, y, axis, kind))
        self.seated = []
        for x, y, look in SEATED:
            self.seated.append({"x": x, "y": y, "angle": LOOK_ANGLES[look], "look": self.random_look(), "phase": self.rng.uniform(0, 6)})
        self.standing = []
        for x, y, look in STANDING:
            self.standing.append({"x": x, "y": y, "angle": LOOK_ANGLES[look], "look": self.random_look(), "phase": self.rng.uniform(0, 6)})
        self.walkers = []
        for path in WALKER_PATHS:
            self.walkers.append(self.make_walker(path, 14 + self.rng.random() * 5))
        self.dog = self.make_walker(DOG_PATH, 22)
        self.players = self.make_players()

        self.trees = []
        self.bushes = []
        self.background = self.build_background()

    # ----- layout (done once) -----

    def random_look(self):
        rng = self.rng
        return (rng.choice(SHIRT_COLORS), rng.choice(SKIN_COLORS), rng.choice(HAIR_COLORS), rng.choice(PANTS_COLORS))

    def make_vendor(self, x, y, axis, kind):
        rng = self.rng
        # which way is the road from this sidewalk? (the vendor waves to the road)
        if axis == "h":
            road = (0, 1) if y < CENTER else (0, -1)
            person = (x + 19, y)
            angle = 90
        else:
            road = (1, 0) if x < CENTER else (-1, 0)
            person = (x, y + 19)
            angle = 0
        return {"x": x, "y": y, "axis": axis, "kind": kind, "road": road, "person": person, "angle": angle,
                "umbrella": rng.choice(AWNING_PAIRS), "look": self.random_look(), "phase": rng.uniform(0, 6)}

    def make_walker(self, path, speed):
        x1, y1, x2, y2 = path
        length = math.hypot(x2 - x1, y2 - y1)
        return {"path": path, "length": length, "speed": speed, "phase": self.rng.random() * 2 * length, "look": self.random_look()}

    def make_players(self):
        # 4 kids playing basketball on the first court (they run around in loops)
        court = [b for b in BUILDINGS if b[0] == "court"][0]
        cx = court[1] + court[3] / 2
        cy = court[2] + court[4] / 2
        players = []
        team_colors = [(210, 60, 60), (210, 60, 60), (240, 240, 240), (240, 240, 240)]
        for i in range(4):
            look = (team_colors[i], self.rng.choice(SKIN_COLORS), self.rng.choice(HAIR_COLORS), (40, 40, 46))
            players.append({"cx": cx, "cy": cy, "ax": 56 + i * 6, "ay": 26 + (i % 2) * 8,
                            "w1": 0.5 + i * 0.13, "w2": 0.7 + i * 0.09, "phase": i * 1.7, "look": look})
        return players

    def get_picture(self, key, make_function):
        if key not in self.cache:
            self.cache[key] = make_function()
        return self.cache[key]

    def get_person(self, look, seated):
        key = ("person", look, seated)
        return self.get_picture(key, lambda: draw_person_picture(look[0], look[1], look[2], look[3], seated))

    # ----- the still background (drawn once) -----

    def build_background(self):
        rng = self.rng
        surface = pygame.Surface((SIZE, SIZE))
        shadows = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)

        draw_ground(surface, rng)
        draw_roads(surface, rng)
        draw_sidewalks(surface)
        draw_road_markings(surface)

        # paved yards under some of the buildings, and the plazas
        for kind, x, y, w, h, options in BUILDINGS:
            if kind in ("house", "flats", "store") and rng.random() < 0.65:
                yard = pygame.Rect(x, y, w, h).inflate(18, 18)
                draw_yard(surface, yard, rng.choice([CONCRETE_COLOR, (150, 128, 94), (176, 172, 160)]))
        for x, y, w, h in PLAZAS:
            draw_yard(surface, pygame.Rect(x, y, w, h), (190, 186, 176))

        # find the spots for trees and bushes, so their shadows can go on the shadow layer too
        self.place_trees_and_bushes()

        # shadows
        for kind, x, y, w, h, options in BUILDINGS:
            if kind != "court":
                add_box_shadow(shadows, pygame.Rect(x, y, w, h), 7 if kind in ("flats", "hall", "chapel") else 5)
        for tree in self.trees:
            if tree["kind"] == "palm":
                pygame.draw.ellipse(shadows, SHADOW_COLOR, (tree["x"] - 4, tree["y"] - 2, tree["radius"] * 1.7, tree["radius"] * 1.2))
            else:
                pygame.draw.ellipse(shadows, SHADOW_COLOR, (tree["x"] - tree["radius"] + 6, tree["y"] - tree["radius"] + 7, tree["radius"] * 2, tree["radius"] * 1.9))
        surface.blit(shadows, (0, 0))

        # the buildings (the roof colors are used in a shuffled order, so two roofs next to each other are not the same)
        roof_colors = GI_ROOF_COLORS[:]
        rng.shuffle(roof_colors)
        roof_count = 0
        stall_count = 0
        for kind, x, y, w, h, options in BUILDINGS:
            rect = pygame.Rect(x, y, w, h)
            roof_color = roof_colors[roof_count % len(roof_colors)]
            if kind == "house" or kind == "store":
                roof_count = roof_count + 1
            if kind == "house":
                draw_gable_roof(surface, rect, roof_color, rng)
            elif kind == "store":
                draw_store(surface, shadows, rect, roof_color, options["side"], rng)
            elif kind == "flats":
                draw_flat_roof(surface, rect, rng.choice(PARAPET_COLORS), rng)
            elif kind == "chapel":
                draw_chapel(surface, rect, rng)
            elif kind == "hall":
                draw_hall(surface, rect, rng)
            elif kind == "court":
                draw_court(surface, rect)
            elif kind == "stall":
                draw_stall(surface, shadows, rect, TARP_COLORS[(stall_count * 2 + 1) % len(TARP_COLORS)], rng)
                stall_count = stall_count + 1

        # bushes, then the electric poles and wires
        for bush in self.bushes:
            picture = bush["picture"]
            surface.blit(picture, picture.get_rect(center=(bush["x"], bush["y"])))
        self.draw_poles_and_wires(surface)

        # the flag pole of the barangay hall (the flag itself moves, so it is drawn later)
        hall = [b for b in BUILDINGS if b[0] == "hall"][0]
        self.flag_pole = (hall[1] + 18, hall[2] + hall[4] + 20)
        big_circle(surface, (240, 240, 240), self.flag_pole[0], self.flag_pole[1], 3)
        big_circle(surface, (120, 120, 126), self.flag_pole[0], self.flag_pole[1], 3, 1)

        if pygame.display.get_surface() is not None:
            surface = surface.convert()
        return surface

    # picks the spots for the trees and bushes. A spot is skipped if it touches a road, sidewalk or building
    def place_trees_and_bushes(self):
        rng = self.rng
        blocked = get_road_rects() + get_sidewalk_rects()
        for kind, x, y, w, h, options in BUILDINGS:
            extra = 16 if kind in ("store", "court") else 8
            blocked.append(pygame.Rect(x, y, w, h).inflate(extra * 2, extra * 2))
        for x, y, w, h in PLAZAS:
            blocked.append(pygame.Rect(x, y, w, h).inflate(10, 10))
        for x, y, look in SEATED + STANDING:
            blocked.append(pygame.Rect(x - 10, y - 10, 20, 20))

        # trees
        attempts = 0
        while len(self.trees) < 30 and attempts < 6000:
            attempts = attempts + 1
            x = rng.randint(6, SIZE - 6)
            y = rng.randint(6, SIZE - 6)
            kind = "palm" if rng.random() < 0.28 else "broadleaf"
            radius = rng.randint(12, 17) if kind == "palm" else rng.randint(11, 19)
            if any(circle_hits_rect(x, y, radius + 3, rect) for rect in blocked):
                continue
            if any(math.hypot(x - t["x"], y - t["y"]) < (radius + t["radius"]) * 0.8 for t in self.trees):
                continue
            seed = rng.randint(0, 99999)
            if kind == "palm":
                picture = draw_palm_picture(radius, seed)
            else:
                picture = draw_broadleaf_picture(radius, seed)
            self.trees.append({"x": x, "y": y, "kind": kind, "radius": radius, "picture": picture, "phase": rng.uniform(0, 6)})

        # bushes (they may stand close to buildings, but not on them)
        solid = get_road_rects() + get_sidewalk_rects() + [pygame.Rect(b[1], b[2], b[3], b[4]).inflate(6, 6) for b in BUILDINGS]
        attempts = 0
        while len(self.bushes) < 44 and attempts < 4000:
            attempts = attempts + 1
            x = rng.randint(6, SIZE - 6)
            y = rng.randint(6, SIZE - 6)
            radius = rng.randint(5, 8)
            if any(circle_hits_rect(x, y, radius + 1, rect) for rect in solid):
                continue
            if any(math.hypot(x - t["x"], y - t["y"]) < radius + t["radius"] for t in self.trees):
                continue
            self.bushes.append({"x": x, "y": y, "picture": draw_bush_picture(radius, rng.randint(0, 99999))})

    # electric poles along the sidewalks, with the wires between them
    def draw_poles_and_wires(self, surface):
        wire = (34, 34, 38)
        for axis, line, start, end in POLE_LINES:
            poles = list(range(start + 50, end, 110))
            if len(poles) == 0:
                continue
            for offset in (-6, 0, 6):               # 3 wires
                if axis == "v":
                    pygame.draw.line(surface, wire, (line + offset, start), (line + offset, poles[-1]))
                else:
                    pygame.draw.line(surface, wire, (start, line + offset), (poles[-1], line + offset))
            for position in poles:
                if axis == "v":
                    pygame.draw.rect(surface, (90, 64, 42), (line - 8, position - 1, 16, 3))        # the cross arm
                    big_circle(surface, (70, 50, 34), line, position, 3)
                else:
                    pygame.draw.rect(surface, (90, 64, 42), (position - 1, line - 8, 3, 16))
                    big_circle(surface, (70, 50, 34), position, line, 3)

    # ----- the calm, still things (drawn every frame, but nothing moves). t is kept so visualizer.py still works -----

    # the ground-level things: drawn BEFORE the traffic lights and cars
    # (no people, dog, players, carts or umbrellas anymore. Only the still flag is drawn here)
    def draw_ground(self, screen, t=0):
        screen.blit(self.background, (0, 0))

        self.draw_flag(screen)

    # the flag on the barangay hall, hanging still (no wind)
    def draw_flag(self, screen, t=0):
        px, py = self.flag_pole
        pieces = 12
        for i in range(pieces):
            left = px + 3 + i * 2
            pygame.draw.rect(screen, (0, 56, 168), (left, py - 6, 3, 6))
            pygame.draw.rect(screen, (206, 17, 38), (left, py, 3, 6))
        pygame.draw.polygon(screen, (250, 250, 250), [(px + 3, py - 6), (px + 3, py + 6), (px + 13, py)])
        big_circle(screen, (252, 209, 22), px + 6, py, 1.5)

    # the tree tops: drawn AFTER the cars, so they are above everything (they stay still now)
    def draw_overhead(self, screen, t=0):
        for tree in self.trees:
            picture = tree["picture"]
            screen.blit(picture, picture.get_rect(center=(int(tree["x"]), int(tree["y"]))))