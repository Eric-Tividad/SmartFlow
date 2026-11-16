# this script only draws the frontend of the program, the pygame one

# One Viewer = one run of one mode ("normal" or "smartflow"):
#   viewer = Viewer("smartflow")
#   finished = viewer.run()      # opens the window, shows the run, closes the window when done

# What the drawing code can read from the model:
#   model.vehicles                      -> the cars (car.direction, car.pos, car.length, car.wait_time)
#   model.controller.state(direction)   -> "green", "yellow" or "red" for that direction
#   model.controller.name               -> the name of the traffic light mode
#   model.controller.last_decision      -> a short sentence about the light's latest decision
#   model.queue_length(direction)       -> how many cars are waiting in that direction
#   model.t, model.arrivals_end_step    -> the time now / when new cars stop arriving
#   model.finished                      -> True when the run is over

import pygame
import config
import metrics
from model import IntersectionModel
from car_design import CarSprites

# colors
GRASS_COLOR = (34, 139, 34)
ROAD_COLOR = (60, 60, 60)
LINE_COLOR = (230, 230, 230)
LIGHT_COLORS = {
    "green": (0, 220, 0),
    "yellow": (240, 200, 0),
    "red": (220, 0, 0),
}

# where each direction's traffic light is drawn (the corners of the intersection)
LIGHT_POSITIONS = {
    "N": (config.CENTER - config.HALF_ROAD - 14, config.CENTER - config.HALF_ROAD - 14),
    "S": (config.CENTER + config.HALF_ROAD + 14, config.CENTER + config.HALF_ROAD + 14),
    "E": (config.CENTER + config.HALF_ROAD + 14, config.CENTER - config.HALF_ROAD - 14),
    "W": (config.CENTER - config.HALF_ROAD - 14, config.CENTER + config.HALF_ROAD + 14),
}

# turns (direction, distance along the lane) into an x and y on the screen
# cars drive on the right side of the road
def get_car_screen_position(direction, pos):
    center = config.CENTER
    length = config.LANE_LENGTH
    offset = config.LANE_OFFSET

    # car comes from top and drives down
    if direction == "N":
        x = center - offset
        y = center - length + pos

    # care comes from bottom and drives up
    elif direction == "S":
        x = center + offset
        y = center + length - pos

    # car comes from  right and drives left
    elif direction == "E":
        x = center + length - pos
        y = center - offset

    # care comes from the left and drives right
    else:
        x = center - length + pos
        y = center + offset

    return x, y

class Viewer:

    def __init__(self, mode_name):
        pygame.init()
        self.screen = pygame.display.set_mode((config.SCREEN_SIZE, config.SCREEN_SIZE))
        pygame.display.set_caption("SmartFlow")
        self.font = pygame.font.SysFont("consolas", 16)
        self.clock = pygame.time.Clock()

        # build the simulation for this mode
        params = config.DEFAULT_PARAMS.copy()
        params["controller"] = mode_name
        self.model = IntersectionModel(params)
        self.model.sim_setup()
        self.arrival_seconds = metrics.get_arrival_seconds(params)

        self.running = True         # becomes False if the window is closed early
        self.paused = False
        self.speed = 1              # how many simulation steps happen per frame

        # car pictures (see car_design.py). car_width is how wide a car is drawn, in pixels
        self.car_sprites = CarSprites(params["car_length"], 12)
        self.braking_cars = set()   # ids of the cars whose brake lights are on

    # keyboard and simulation
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT: 
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:    # esc = quit
                    self.running = False
                elif event.key == pygame.K_SPACE:   # space = pause
                    self.paused = not self.paused
                elif event.key == pygame.K_UP:      # up arrow = speed up
                    if self.speed < 10:
                        self.speed = self.speed + 1
                elif event.key == pygame.K_DOWN:    # down arrow = slow down
                    if self.speed > 1:
                        self.speed = self.speed - 1

    def update_simulation(self):
        if self.paused == True:
            return
        speed_before = {}
        for car in self.model.vehicles:
            speed_before[car.id] = car.speed

        for _ in range(self.speed):
            if self.model.finished == False:
                self.model.sim_step()

        self.update_brake_lights(speed_before)

    # a car's brake lights are on while it is slowing down or stopped in a queue
    def update_brake_lights(self, speed_before):
        self.braking_cars = set()
        for car in self.model.vehicles:
            if car.waiting == True:
                self.braking_cars.add(car.id)
            elif car.id in speed_before and car.speed < speed_before[car.id] - 0.01:
                self.braking_cars.add(car.id)

    # draws enviroment
    def draw_road(self):
        center = config.CENTER
        half = config.HALF_ROAD
        size = config.SCREEN_SIZE

        # grass background, then the two roads
        self.screen.fill(GRASS_COLOR)
        pygame.draw.rect(self.screen, ROAD_COLOR, (center - half, 0, 2 * half, size))
        pygame.draw.rect(self.screen, ROAD_COLOR, (0, center - half, size, 2 * half))

        # dashed center lines (skipped inside the intersection box)
        for spot in range(0, size, 30):
            inside_intersection = (spot >= center - half and spot <= center + half)
            if inside_intersection == False:
                pygame.draw.line(self.screen, LINE_COLOR, (center, spot), (center, spot + 15), 2)
                pygame.draw.line(self.screen, LINE_COLOR, (spot, center), (spot + 15, center), 2)

        # stop lines, one for each direction
        pygame.draw.line(self.screen, LINE_COLOR, (center - half, center - half), (center, center - half), 4)   # North
        pygame.draw.line(self.screen, LINE_COLOR, (center, center + half), (center + half, center + half), 4)   # South
        pygame.draw.line(self.screen, LINE_COLOR, (center + half, center - half), (center + half, center), 4)   # East
        pygame.draw.line(self.screen, LINE_COLOR, (center - half, center), (center - half, center + half), 4)   # West

    def draw_lights(self):
        for direction in config.DIRECTIONS:
            light_state = self.model.controller.state(direction)
            light_color = LIGHT_COLORS[light_state]
            light_position = LIGHT_POSITIONS[direction]
            pygame.draw.circle(self.screen, (20, 20, 20), light_position, 11)
            pygame.draw.circle(self.screen, light_color, light_position, 8)

    def draw_cars(self):
        for car in self.model.vehicles:
            x, y = get_car_screen_position(car.direction, car.pos)

            # the picture comes from car_design.py. It is already turned the right way
            braking = car.id in self.braking_cars
            car_picture = self.car_sprites.get(car.id, car.direction, braking)
            car_rect = car_picture.get_rect(center=(int(x), int(y)))
            self.screen.blit(car_picture, car_rect)

    # a short info box in the top-left corner
    def draw_info_text(self):
        model = self.model

        # line 1: the mode and the time
        seconds_now = model.t / config.STEPS_PER_SECOND
        time_text = str(round(seconds_now, 1)) + " s"
        if model.t <= model.arrivals_end_step:
            time_text = time_text + " / " + str(self.arrival_seconds) + " s"
        else:
            time_text = time_text + " (no new cars, clearing the road)"
        line_1 = model.controller.name + "  |  " + time_text
        if self.paused == True:
            line_1 = line_1 + "  [PAUSED]"

        # line 2: how many cars are waiting in each direction
        line_2 = "waiting  "
        for direction in config.DIRECTIONS:
            line_2 = line_2 + direction + ":" + str(model.queue_length(direction)) + "  "

        all_lines = [line_1, line_2]

        # line 3 (SmartFlow only): the rule the light is using right now
        if model.controller.last_decision != "":
            all_lines.append(model.controller.last_decision)

        row = 0
        for text in all_lines:
            text_image = self.font.render(text, True, (255, 255, 255), (0, 0, 0))
            self.screen.blit(text_image, (8, 8 + row * 20))
            row = row + 1

        # the controls, small, at the bottom of the screen
        controls_text = "SPACE pause   UP/DOWN speed x" + str(self.speed) + "   ESC stop"
        controls_image = self.font.render(controls_text, True, (255, 255, 255), (0, 0, 0))
        self.screen.blit(controls_image, (8, config.SCREEN_SIZE - 26))

    def draw_simulation(self):
        self.draw_road()
        self.draw_lights()
        self.draw_cars()
        self.draw_info_text()

    # main loop
    # handles the keys, moves the simulation, and draws 1 frame
    def run_one_frame(self, events):
        self.handle_events(events)
        self.update_simulation()
        self.draw_simulation()
        pygame.display.flip()

    # runs until the simulation finishes or the window is closed early
    def run(self):
        while self.running == True and self.model.finished == False:
            events = pygame.event.get()
            self.run_one_frame(events)
            self.clock.tick(60)

        run_finished = self.model.finished
        pygame.quit()
        return run_finished