import argparse

# from policies.random_assgn_policy import rnd_assgn_policy_no_return, rnd_assgn_policy_return
# from policies.tsp_policy import tsp_policy
# from policies.mod_tsp_policy import modified_tsp_policy
from random import seed
from simulation import Simulation
from config import *
import pygame

from importlib import import_module


def main(args):

    pygame.init()
    screen = pygame.display.set_mode((args.height, args.width))
    pygame.display.set_caption('Simulation')

    clock = pygame.time.Clock()
    pygame.font.init()

    # set the seed
    if args.seed is not None:
        seed(args.seed)

    sim = Simulation(
        policy_name=args.policy,
        num_actors=args.actors,
        pois_lambda=args.lambd,
        screen=screen)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        screen.fill((0, 0, 0))
        rval = sim.tick(args.tick_time, args.max_time)
        if rval == -1:
            break
        pygame.display.flip()
        pygame.display.update()
        clock.tick(1.0/args.tick_time*args.simulation_speed)

    if len(sim.serviced_tasks) > 0:
        print("Average service time:", sim._avg_served_time/len(sim.serviced_tasks))
    print("Total serviced:", len(sim.serviced_tasks))


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description=__doc__)
    argparser.add_argument(
        '--height',
        default=SCREEN_HEIGHT,
        type=int,
        help='Screen vertical size')
    argparser.add_argument(
        '--width',
        default=SCREEN_WIDTH,
        type=int,
        help='Screen horizontal size')
    argparser.add_argument(
        '--margin',
        default=SCREEN_MARGIN,
        type=int,
        help='Screen horizontal size')
    argparser.add_argument(
        '-s', '--seed',
        default=None,
        type=float,
        help='Random Seed')
    argparser.add_argument(
        '-l', '--lambd',
        default=LAMBDA,
        type=float,
        help='Exponential Spawn rate for Tasks')
    argparser.add_argument(
        '-a', '--actors',
        default=NUM_ACTORS,
        type=int,
        help='Number of actors in the simulation')
    argparser.add_argument(
        '-p', '--policy',
        default=DEFAULT_POLICY_NAME,
        help='Policy to use')
    argparser.add_argument(
        '--service-time',
        default=SERVICE_TIME,
        type=float,
        help='Service time on arrival at each node')
    argparser.add_argument(
        '--simulation_speed',
        default=SIMULATION_SPEED,
        type=float,
        help='Simulator speed')
    argparser.add_argument(
        '-t', '--tick_time',
        default=TICK_TIME,
        type=float,
        help='Length of Simulation Time Step')
    argparser.add_argument(
        '--max-time',
        default=MAX_SIMULATION_TIME,
        type=float,
        help='Maximum Length of Simulation')

    args = argparser.parse_args()

    main(args)
