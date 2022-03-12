DISTANCE_TOLERANCE = 0.005
SIMULATION_SPEED = 100

MAX_SIMULATION_TIME = 1000
MAX_SERVICED_TASKS = 1000
NUM_ACTORS = 1
ACTOR_SPEED = 1
LAMBDA = 0.8
SERVICE_TIME = 0
TICK_TIME = 0.01

DEFAULT_POLICY_NAME = "random_assgn"
DEFAULT_GENERATOR_NAME = "uniform"
GENERATOR_ARGS = {
    'min': -1,
    'max': 1,
    'distributions': [
        [0.5, 0.1],
        [-0.5, 0.1]
    ],
    'seed': None,
    'dim': 2,
    'mix': 0.05,
}
SHOW_SIM = False

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000
SCREEN_MARGIN = 150

RESULTS_DIR = 'results'
TASKS_DIR = 'tasks'

TASK_LIST_FILE_PREFIX = "dvrp_tasks"
