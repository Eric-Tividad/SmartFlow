# handles the car behaviors
# the car only knows its position along its own lane (a single number called "pos")

import math
import agentpy as ap

class Vehicle(ap.Agent):

    # car attributes
    def setup(self, direction):
        self.direction = direction
        self.pos = 0.0                      # distance traveled along the lane (starts at the screen edge)
        self.speed = self.p.max_speed
        self.length = self.p.car_length
        self.wait_time = 0                  # how many steps the car sat stopped before the stop line
        self.waiting = False                # True while the car is stopped and has not crossed yet
        self.crossed = False                # True once the car has passed the stop line

    def front_position(self):
        return self.pos + self.length / 2

    # main car behavior
    def step(self, car_ahead):
        # car_ahead is the car directly in front of this one in the same lane, or None if this car is first in line

        speed_limit = self.p.max_speed
        stop_line_position = self.model.stop_pos

        # 1. check traffic light
        # only matters if the car has not reached the stop line yet
        if self.front_position() <= stop_line_position:
            light_color = self.model.controller.state(self.direction)
            distance_to_stop_line = stop_line_position - self.front_position()
            distance_needed_to_stop = (self.speed * self.speed) / (2 * self.p.decel)

            must_stop = False
            if light_color == "red":
                must_stop = True
            if light_color == "yellow":     # on yellow, only stop if the car is still able to stop in time
                if distance_to_stop_line > distance_needed_to_stop:
                    must_stop = True

            # slow down so the car comes to a stop right at the line
            if must_stop == True:
                # aim to stop 4 pixels BEFORE the line 
                # if we aimed right at the line, the car could creep a tiny bit over it, count as "crossed", and drive through the red lights
                room_left = distance_to_stop_line - 4
                if room_left < 0:
                    room_left = 0
                safe_speed_for_light = math.sqrt(2 * self.p.decel * room_left)
                if safe_speed_for_light < speed_limit:
                    speed_limit = safe_speed_for_light
        else:
            self.crossed = True

        # 2. don't crash infront of car, if there is any
        if car_ahead is not None:
            gap = car_ahead.pos - self.pos - self.length
            room_left = gap - self.p.min_gap
            if room_left < 0:
                room_left = 0
            safe_speed_for_car = math.sqrt(2 * self.p.decel * room_left)
            if safe_speed_for_car < speed_limit:
                speed_limit = safe_speed_for_car

        # 3. speed or slow down toward the speed limit
        if self.speed < speed_limit:
            self.speed = self.speed + self.p.accel
            if self.speed > speed_limit:
                self.speed = speed_limit
        else:
            self.speed = self.speed - self.p.decel
            if self.speed < speed_limit:
                self.speed = speed_limit

        # 4. vroom
        self.pos = self.pos + self.speed

        # 5. keep tracks for waiting time (used for result stuff)
        self.waiting = False
        if self.crossed == False and self.speed < 0.1:
            self.waiting = True
        if self.waiting == True:
            self.wait_time = self.wait_time + 1