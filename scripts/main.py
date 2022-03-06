import argparse
from random import seed
from simulation import Simulation
from config import *
import pygame

from importlib import import_module
from os import path, mkdir


def simulate(args):

    if args.show_sim:
        pygame.init()
        screen = pygame.display.set_mode((args.height, args.width))
        pygame.display.set_caption('Simulation')

        clock = pygame.time.Clock()
        pygame.font.init()
    else:
        screen = None

    # set the seed
    if args.seed is not None:
        seed(args.seed)

    sim = Simulation(
        policy_name=args.policy,
        num_actors=args.actors,
        pois_lambda=args.lambd,
        screen=screen,
        show_sim=args.show_sim)

    while True:
        if args.show_sim:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
            screen.fill((0, 0, 0))
        rval = sim.tick(args.tick_time, max_simulation_time=args.max_time, max_serviced_tasks=args.max_tasks)
        if rval == -1:
            break

        if args.show_sim:
            pygame.display.flip()
            pygame.display.update()
            clock.tick(1.0/args.tick_time*args.simulation_speed)

    if len(sim.serviced_tasks) > 0:
        print("Average service time:", sim._avg_served_time/len(sim.serviced_tasks))
    print("Total serviced:", len(sim.serviced_tasks))
    return sim


def multiple_sims(args):

    if not path.isdir('results'):
        mkdir(RESULTS_DIR)

    f = open(path.join(RESULTS_DIR, "res_" + args.policy + ".txt"), "a")
    for lam in [0.05, 0.1, 0.2, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9]:
        print("================= LAMBDA: {:.2f} =================".format(lam))
        args.lambd = lam
        sim = simulate(args)
        f.write(
            str(lam) + "," + str(sim._avg_served_time) + "," + str(sim._curr_max_time) +
            "," + str(len(sim.serviced_tasks)) + "," + str(sim._max_served_time) + "," + str(sim._avg_served_time / len(sim.serviced_tasks)) + "\n"
        )
    f.close()


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
        default=None,
        type=float,
        help='Maximum Length of Simulation')
    argparser.add_argument(
        '--max-tasks',
        default=MAX_SERVICED_TASKS,
        type=int,
        help='Maximum number of Tasks to service')
    argparser.add_argument(
        '--show-sim',
        action='store_true',
        help='Display the simulation window')

    args = argparser.parse_args()

    multiple_sims(args)
