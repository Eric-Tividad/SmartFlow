# settings or numbers used in the simul
# if you want to change how the simulation behaves, change the numbers in this file

# screen and road sizes in pixels
SCREEN_SIZE = 800
CENTER = 400                # the middle of the screen (the middle of the intersection)
LANE_LENGTH = 400           # distance from the edge of the screen to the middle of the intersection
HALF_ROAD = 60              # half of the width of the intersection box
LANE_OFFSET = 30            # how far a lane sits from the center line of the road

STEPS_PER_SECOND = 60       # 60 simulation steps = 1 second (used to show seconds on screen)

# directions
# the direction is where the car comes from
# main flow: car from top goes down, vice versa
DIRECTIONS = ["N", "S", "E", "W"]
NORTH_SOUTH = ["N", "S"]
EAST_WEST = ["E", "W"]

# main simul settings
DEFAULT_PARAMS = {
    # run settings
    "controller": "normal",     # "normal" = normal traffic lights, "smartflow" = SmartFlow traffic lights
    "seed": 42,                 # same seed = same random traffic every run 
    "steps": 100000,            # safety limit only. A run normally ends by itself when every car has left

    # new cars keep arriving for this long, then the road clears and the run ends
    "run_duration": 1800,       # 1800 steps = 30 seconds

    # car settings
    "max_speed": 2.5,           # pixels per step
    "accel": 0.08,              # how fast a car speeds up
    "decel": 0.30,              # how fast a car can slow down
    "car_length": 22,
    "min_gap": 6,               # smallest space a car keeps behind the car in front

    # Chance (0 to 1) that a new car appears each step, for each direction
    # North/South is busier than East/West on purpose, because that is where
    # the SmartFlow light should do better than a normal timer
    "spawn_probs": {"N": 0.025, "S": 0.025, "E": 0.010, "W": 0.010},

    # normal traffic light settings (counted in steps)
    "green_time": 300,
    "yellow_time": 60,
    "all_red_time": 30,

    # SmartFlow traffic light settings (counted in steps, except the distance)
    "smartflow_min_green": 180,             # a green light always stays on at least this long
    "smartflow_max_green": 300,             # a green light never stays on longer than this (if someone is waiting)
    "smartflow_detection_distance": 150,    # how far before the stop line the light can "see" approaching cars
    "smartflow_switch_margin": 30,          # how much more pressure the other road needs before we switch
}