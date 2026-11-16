# the main brain of the traffic lights

# also determines how each mode works:
#   NormalController    -> Normal traffic lights (a plain timer)
#   SmartFlowController -> SmartFlow traffic lights (rule-based, looks at the traffic)

import config

# directions stuff
def get_road_of_direction(direction):
    if direction in config.NORTH_SOUTH:
        return "NS"
    return "EW"

def get_other_road(road):
    if road == "NS":
        return "EW"
    return "NS"

class BaseController:
    name = "base"
    last_decision = ""      # a short sentence about the latest decision (shown on screen if not empty)

    def update(self, model):
        raise NotImplementedError

    def state(self, direction):
        raise NotImplementedError

# normal traffic lights - plain timer
class NormalController(BaseController):
    # North/South green -> yellow -> all red -> East/West green -> yellow -> all red -> repeat
    name = "Normal traffic lights"

    def __init__(self, params):
        green_time = params.green_time
        yellow_time = params.yellow_time
        all_red_time = params.all_red_time

        # each phase says which road has the light, what color it is, and how many steps it lasts.
        self.phases = [
            {"road": "NS", "color": "green", "duration": green_time},
            {"road": "NS", "color": "yellow", "duration": yellow_time},
            {"road": "none", "color": "red", "duration": all_red_time},

            {"road": "EW", "color": "green", "duration": green_time},
            {"road": "EW", "color": "yellow", "duration": yellow_time},
            {"road": "none", "color": "red", "duration": all_red_time},
        ]
        self.current_phase_index = 0
        self.timer = 0

    def update(self, model):
        self.timer = self.timer + 1
        current_phase = self.phases[self.current_phase_index]

        # when the phase runs out, go to the next one (and loop back to the start at the end)
        if self.timer >= current_phase["duration"]:
            self.current_phase_index = self.current_phase_index + 1
            if self.current_phase_index >= len(self.phases):
                self.current_phase_index = 0
            self.timer = 0

    def state(self, direction):
        current_phase = self.phases[self.current_phase_index]
        my_road = get_road_of_direction(direction)

        # only the road that has the light gets the phase color. the other road is red
        if current_phase["road"] == my_road:
            return current_phase["color"]
        return "red"

# SmartFlow traffic lights - "smart lights", or rule-based one
class SmartFlowController(BaseController):
    # instead of a timer deciding everything, this light looks at the traffic and uses rules
    
    # the light is always in one of three phases:
    #   "green"   -> one road (NS or EW) has green. The rules below run every step to decide
    #                if it is time to switch
    #   "yellow"  -> the green road is ending (fixed length)
    #   "all_red" -> everybody is red so the intersection can clear (fixed length),
    #                then other roads gets green

    # main rules (checked in this order while a road has green):
    #   Rule 1: keep green if the minimum green time has not passed yet
    #   Rule 2: keep green if nobody is waiting on the other road

    #   Rule 3: switch if the maximum green time has passed (so nobody waits forever)
    #   Rule 4: switch if the green road is empty (no cars waiting or coming)
    #   Rule 5: switch if the other road has much more "waiting pressure" than the green road
    #   Rule 6: otherwise keep green

    name = "SmartFlow traffic lights"

    def __init__(self, params):
        self.yellow_time = params.yellow_time
        self.all_red_time = params.all_red_time
        self.min_green_time = params.smartflow_min_green
        self.max_green_time = params.smartflow_max_green
        self.detection_distance = params.smartflow_detection_distance
        self.switch_margin = params.smartflow_switch_margin

        self.green_road = "NS"
        self.phase = "green"
        self.timer = 0
        self.last_decision = "Start: NS has green"

    # looks at all cars on one road (NS or EW) that have not crossed the stop line yet and counts them:
    #   waiting  = # of cars stopped in line
    #   arriving = # of moving cars close to the stop line (inside the detection distance)
    #   score    = waiting pressure. every waiting car adds 1, plus 1 more for every
    #              second it has already waited. long waits count more
    def measure_road(self, model, road):
        waiting_count = 0
        arriving_count = 0
        score = 0.0

        for car in model.vehicles:
            if get_road_of_direction(car.direction) != road:
                continue

            if car.front_position() > model.stop_pos: # this car already crossed the stop line
                continue        

            if car.waiting == True:
                waiting_count = waiting_count + 1
                seconds_waited = car.wait_time / config.STEPS_PER_SECOND
                score = score + 1 + seconds_waited

            else:
                distance_to_stop_line = model.stop_pos - car.front_position()
                if distance_to_stop_line <= self.detection_distance:
                    arriving_count = arriving_count + 1

        return {"waiting": waiting_count, "arriving": arriving_count, "score": score}

    # begin ending the current green: go to yellow first
    def start_switching(self, reason):
        self.phase = "yellow"
        self.timer = 0
        self.last_decision = reason

    def check_rules(self, model):
        green_info = self.measure_road(model, self.green_road)
        other_info = self.measure_road(model, get_other_road(self.green_road))

        # Rule 1: minimum green time
        if self.timer < self.min_green_time:
            self.last_decision = "Rule 1: keep green (minimum green time not reached)"
            return

        # Rule 2: nobody is waiting on the other road, so there is no reason to switch
        if other_info["waiting"] == 0:
            self.last_decision = "Rule 2: keep green (nobody waiting on the other road)"
            return

        # Rule 3: maximum green time
        if self.timer >= self.max_green_time:
            self.start_switching("Rule 3: switch (maximum green time reached)")
            return

        # Rule 4: the green road is empty
        green_cars_nearby = green_info["waiting"] + green_info["arriving"]
        if green_cars_nearby == 0:
            self.start_switching("Rule 4: switch (green road is empty)")
            return

        # Rule 5: compare the pressure of both roads
        green_pressure = green_info["score"] + green_info["arriving"]
        other_pressure = other_info["score"]
        if other_pressure >= green_pressure + self.switch_margin:
            self.start_switching("Rule 5: switch (other road has more waiting pressure)")
            return

        # Rule 6: nothing says to switch
        self.last_decision = "Rule 6: keep green (green road still needs it)"

    def update(self, model):
        self.timer = self.timer + 1

        if self.phase == "green":
            self.check_rules(model)

        elif self.phase == "yellow":
            if self.timer >= self.yellow_time:
                self.phase = "all_red"
                self.timer = 0

        elif self.phase == "all_red":
            if self.timer >= self.all_red_time:
                self.green_road = get_other_road(self.green_road)
                self.phase = "green"
                self.timer = 0
                self.last_decision = "Switched: " + self.green_road + " has green now"

    def state(self, direction):
        my_road = get_road_of_direction(direction)

        if self.phase == "all_red":
            return "red"
        if my_road == self.green_road:
            return self.phase       # green or yellow hmm
        return "red"

# decides which traffic lights mode to use
def make_controller(params):
    if params.controller == "normal":
        return NormalController(params)
    if params.controller == "smartflow":
        return SmartFlowController(params)
    raise ValueError("Unknown controller: " + str(params.controller))