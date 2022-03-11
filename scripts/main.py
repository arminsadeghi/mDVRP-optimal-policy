import argparse
from importlib.metadata import distribution
from random import seed
from simulation import Simulation
from config import *
import pygame

from importlib import import_module
from os import path, mkdir
from time import time
from pickle import load, dump


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
        print("Setting seed to: ", args.seed)
    else:
        seed(time())

    sim = Simulation(
        policy_name=args.policy,
        generator_name=args.generator,
        generator_args={
            'min': -1,
            'max': 1,
            'distributions': [
                [0.5, 0.2],
                [-0.5, 0.2]
            ],
            'seed': args.seed,
            'dim': 2,
        },
        num_actors=args.actors,
        pois_lambda=args.lambd,
        screen=screen,
        show_sim=args.show_sim,
        max_tasks=args.max_tasks,
        max_time=args.max_time
    )

    if args.seed is not None:
        if not path.isdir(TASKS_DIR):
            mkdir(TASKS_DIR)

        pickle_file = path.join(TASKS_DIR, TASK_LIST_FILE_PREFIX + '_' + str(args.lambd) + '_' + str(args.generator) + '_' + str(args.seed) + '.pkl')
        try:
            with open(pickle_file, 'rb') as fp:
                task_list = load(fp)
                sim.reset(task_list)
        except Exception as e:
            print(e)
            # not loading, save it instead
            with open(pickle_file, 'wb') as fp:
                dump(sim.task_list, fp)

    while True:
        if args.show_sim:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
            screen.fill((0, 0, 0))
        rval = sim.tick(tick_time=args.tick_time, max_simulation_time=args.max_time, max_tasks=args.max_tasks)
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

    if not path.isdir(RESULTS_DIR):
        mkdir(RESULTS_DIR)

    results_file_name = path.join(RESULTS_DIR, "res_" + args.policy + ".txt")
    if not path.exists(results_file_name):
        f = open(results_file_name, 'w')
        f.write('policy,lambda,sim-time,avg-srv-time,tasks-srvd,max-wait-time,avg-wait-time,wait-sd,total-travel-distance,avg-agent-dist,avg-task-dist,max-agent-dist\n')
    else:
        f = open(results_file_name, 'a')

    for seed in [2, 6, 42, 52, 97, 35, 81, 1932, 493, 89234657]:
        args.seed = seed

        new_task_list = True
        for lam in [0.05, 0.1, 0.2, 0.3, 0.4,  0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]:  # []:
            print("================= LAMBDA: {:.2f} =================".format(lam))
            args.lambd = lam
            sim = simulate(args)
            policy = args.policy.replace('_', ' ')
            f.write(
                str(policy) + "," + str(lam) + "," + str(sim.sim_time) + "," + str(sim._avg_served_time) + "," + str(len(sim.serviced_tasks)) + "," +
                str(sim._max_served_time) + "," + str(sim._avg_served_time / len(sim.serviced_tasks)) + "," + str(sim.calculate_sd()) + "," +
                str(sim._total_travel_distance) + "," +
                str(sim._total_travel_distance / len(sim.actor_list)) + "," + str(sim._total_travel_distance / len(sim.serviced_tasks)) + "," +
                str(sim._max_travel_distance) + "\n"
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
        type=int,
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
        '-g', '--generator',
        default=DEFAULT_GENERATOR_NAME,
        help='Random Generator to use')
    argparser.add_argument(
        '--load-tasks',
        action='store_true',
        help='Load the most recent list of tasks')
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
    argparser.add_argument(
        '--multipass',
        action='store_true',
        help='Run the simulation over multiple lambda and seeds')

    args = argparser.parse_args()

    if args.multipass:
        for policy in ['batch_tsp', 'tsp', 'mod_tsp', 'quad_wait_tsp']:
            args.policy = policy
            multiple_sims(args)

    else:
        simulate(args)
