# za warudo (the world) script

# keeps the list of cars, the traffic light controller, and the results

# a run works like this:
#   1. cars arrive at random times for a set duration (30 seconds by default)
#   2. after that, no new cars arrive and the cars that are still on the road finish passing through
#   3. when the road is empty, the run is finished

import agentpy as ap
import config
from agents import Vehicle
from controllers import make_controller

def get_position(car):
    return car.pos

class IntersectionModel(ap.Model):

    # warudo attributes
    def setup(self):
        self.controller = make_controller(self.p)
        self.stop_pos = config.LANE_LENGTH - config.HALF_ROAD      # where the stop line is along the lane
        self.end_pos = 2 * config.LANE_LENGTH                      # where cars leave the map
        self.vehicles = []                                         # all cars currently on the map
        self.finished_waits = []                                   # wait_time of every car that finished
        self.arrivals_end_step = self.p.run_duration               # new cars stop arriving after this step

        #  used to build the results
        self.finished = False                   # becomes True when the run is completely done
        self.finish_step = 0                    # the step when it finished
        self.passed_by_end_of_arrivals = 0      # cars that had already passed through when arrivals stopped
        self.waiting_sum = 0                    # adds up (every step) how many cars were waiting
        self.steps_counted = 0

    # Returns the cars in one lane, with the car closest to the end of the road first
    def get_lane(self, direction):
        cars_in_lane = []
        for car in self.vehicles:
            if car.direction == direction:
                cars_in_lane.append(car)
        cars_in_lane.sort(key=get_position, reverse=True)
        return cars_in_lane

    # counts how many cars are stopped and waiting in one direction
    def queue_length(self, direction):
        count = 0
        for car in self.vehicles:
            if car.direction == direction and car.waiting == True:
                count = count + 1
        return count

    # True if there is room at the start of the lane for a new car (so cars do not overlap)
    def lane_start_is_clear(self, direction):
        space_needed = self.p.car_length + self.p.min_gap + 4
        for car in self.vehicles:
            if car.direction == direction and car.pos <= space_needed:
                return False
        return True
    # each step, every direction has a small chance to get a new car
    # Once the arrival time is over, no new cars are added
    def spawn_cars(self):
        if self.t > self.arrivals_end_step:
            return

        for direction in config.DIRECTIONS:
            random_number = self.random.random()
            if random_number < self.p.spawn_probs[direction]:
                if self.lane_start_is_clear(direction):
                    new_car = Vehicle(self, direction=direction)
                    self.vehicles.append(new_car)

    # the run is finished when the arrival time is over and the road is empty again
    def check_if_run_is_finished(self):
        if self.finished == True:
            return
        if self.t < self.arrivals_end_step:
            return

        if len(self.vehicles) == 0:
            self.finished = True
            self.finish_step = self.t
            self.stop()         # tells AgentPy to end the run (matters for headless runs)

    # adds up the results so far. Used by end() and by metrics.py
    def get_results(self):
        total_cars = len(self.finished_waits)
        total_wait = 0
        max_wait = 0
        cars_that_stopped = 0
        for wait in self.finished_waits:
            total_wait = total_wait + wait
            if wait > max_wait:
                max_wait = wait
            if wait > 0:
                cars_that_stopped = cars_that_stopped + 1

        average_wait = 0
        percent_stopped = 0
        if total_cars > 0:
            average_wait = total_wait / total_cars
            percent_stopped = 100 * cars_that_stopped / total_cars

        average_waiting_cars = 0
        if self.steps_counted > 0:
            average_waiting_cars = self.waiting_sum / self.steps_counted

        clear_time = self.t
        if self.finished == True:
            clear_time = self.finish_step

        results = {}
        results["total_cars"] = total_cars
        results["avg_wait_steps"] = average_wait
        results["max_wait_steps"] = max_wait
        results["percent_stopped"] = percent_stopped
        results["avg_waiting_cars"] = average_waiting_cars
        results["passed_by_end_of_arrivals"] = self.passed_by_end_of_arrivals
        results["clear_time_steps"] = clear_time
        return results

    # main flow of this script
    def step(self):

        # 1. update the traffic light
        self.controller.update(self)

        # 2. maybe add new cars (random chance)
        self.spawn_cars()

        # 3. move every car, one lane at a time, front car first
        for direction in config.DIRECTIONS:
            lane = self.get_lane(direction)
            for index in range(len(lane)):
                car = lane[index]
                if index == 0:
                    car_ahead = None
                else:
                    car_ahead = lane[index - 1]
                car.step(car_ahead)

        # 4. remove cars that drove off the map
        cars_to_remove = []
        for car in self.vehicles:
            if car.pos >= self.end_pos:
                cars_to_remove.append(car)
        for car in cars_to_remove:
            self.finished_waits.append(car.wait_time)
            self.vehicles.remove(car)

        # 5. remember how many cars got through by the time arrivals stopped
        if self.t == self.arrivals_end_step:
            self.passed_by_end_of_arrivals = len(self.finished_waits)

        # 6. check if everything is done
        self.check_if_run_is_finished()

    # saves the queue length of each direction and adds up how many cars are waiting (used for the average)
    def update(self):
        total_waiting = 0
        for direction in config.DIRECTIONS:
            queue = self.queue_length(direction)
            self.record("queue_" + direction, queue)
            total_waiting = total_waiting + queue

        self.waiting_sum = self.waiting_sum + total_waiting
        self.steps_counted = self.steps_counted + 1

    # reports results
    def end(self):
        results = self.get_results()
        for name in results:
            self.report(name, results[name])