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
from designs import CarSprites, TrafficLightSprites, Environment, SIDEWALK_WIDTH

# where each direction's traffic light is drawn: on the sidewalk, a bit before the stop line
# (the sidewalk is drawn in designs.py, the Environment section)
LIGHT_MIDDLE = SIDEWALK_WIDTH // 2      # the middle of the sidewalk
LIGHT_END_GAP = 26                      # how far the light is from the intersection, along the road
LIGHT_POSITIONS = {
    "N": (config.CENTER - config.HALF_ROAD - LIGHT_MIDDLE, config.CENTER - config.HALF_ROAD - LIGHT_END_GAP),
    "S": (config.CENTER + config.HALF_ROAD + LIGHT_MIDDLE, config.CENTER + config.HALF_ROAD + LIGHT_END_GAP),
    "E": (config.CENTER + config.HALF_ROAD + LIGHT_END_GAP, config.CENTER - config.HALF_ROAD - LIGHT_MIDDLE),
    "W": (config.CENTER - config.HALF_ROAD - LIGHT_END_GAP, config.CENTER + config.HALF_ROAD + LIGHT_MIDDLE),
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

        # pictures (see designs.py). The 12 is how wide a car is drawn, in pixels
        self.car_sprites = CarSprites(params["car_length"], 12)
        self.light_sprites = TrafficLightSprites()
        self.environment = Environment()     # the ground, buildings, trees, people (see designs.py)
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

    def draw_lights(self):
        for direction in config.DIRECTIONS:
            light_state = self.model.controller.state(direction)

            # the picture comes from designs.py, it is centered on the light's position
            light_picture = self.light_sprites.get(light_state, direction)
            light_rect = light_picture.get_rect(center=LIGHT_POSITIONS[direction])
            self.screen.blit(light_picture, light_rect)

    def draw_cars(self):
        for car in self.model.vehicles:
            x, y = get_car_screen_position(car.direction, car.pos)

            # the picture comes from designs.py. It is already turned the right way
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
        # the moving things in the town use the real clock, so they keep moving even when paused
        now = pygame.time.get_ticks() / 1000

        self.environment.draw_ground(self.screen, now)      # ground, roads, buildings, people (designs.py)
        self.draw_lights()
        self.draw_cars()
        self.environment.draw_overhead(self.screen, now)    # the tree tops, above the cars
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