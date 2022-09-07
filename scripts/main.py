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
from time import sleep


def simulate(args):

    if args.show_sim:
        pygame.init()
        screen = pygame.display.set_mode((args.height, args.width))
        pygame.display.set_caption('Simulation')

        clock = pygame.time.Clock()
        pygame.font.init()
    else:
        screen = None

    # for i in range(15):
    #     sleep(1)

    # set the seed
    if args.seed is not None:
        seed(args.seed)
        print("Setting seed to: ", args.seed)
    else:
        seed(time())

    generator_args = GENERATOR_ARGS
    generator_args['seed'] = args.seed
    generator_args['max_tasks'] = args.max_tasks
    generator_args['max_time'] = args.max_time
    generator_args['service_time'] = args.service_time

    sim = Simulation(
        policy_name=args.policy,
        generator_name=args.generator,
        policy_args={
            'cost_exponent': args.cost_exponent
        },
        generator_args=generator_args,
        num_actors=args.actors,
        pois_lambda=args.lambd,
        service_time=args.service_time,
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

    # Note that neither batch_tsp, nor tsp use the exponent value for anything -- they
    # just need to run once... giving them unique negative values in case we want to graph
    # them
    # policies = ['batch_tsp', 'tsp', 'quad_wait_tsp']
    # policies = ['quad_wait_tsp']
    policies = [args.policy]
    # exponents = [[-2], [-1], [1, 1.5, 2, 2.5, 3, 4, 5, 10]]
    # exponents = [[1, 2]]
    exponents = [[args.cost_exponent], ]

    if len(args.prefix) != 0 and args.prefix[-1] != '_':
        args.prefix = args.prefix + '_'

    for policy, exps in zip(policies, exponents):
        args.policy = policy

        results_file_name = path.join(RESULTS_DIR, args.prefix + args.policy + '_' + str(args.cost_exponent) + '_' + str(args.service_time) + ".csv")
        if not path.exists(results_file_name):
            f = open(results_file_name, 'w')
            f.write('policy,lambda,cost-exponent,sim-time,avg-srv-time,tasks-srvd,max-wait-time,avg-wait-time,wait-sd,total-travel-distance,avg-agent-dist,avg-task-dist,max-agent-dist,max_queue_len\n')
        else:
            f = open(results_file_name, 'a')

        for lam in [0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.98]:  # []:
            # for lam in [0.05, 0.1, 0.2, 0.3, 0.4,  0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]:  # []:
            # for lam in [1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:  # []:

            for e in exps:

                args.cost_exponent = e

                for seed in [21, 6, 42, 52, 97]:
                    args.seed = seed
                    print("================= LAMBDA: {:.2f} =================".format(lam))
                    args.lambd = lam
                    sim = simulate(args)
                    policy = args.policy.replace('_', ' ')
                    f.write(
                        str(policy) + "," + str(lam) + "," + str(e) + "," + str(sim.sim_time) + "," + str(sim._avg_served_time) + "," + str(len(sim.serviced_tasks)) + "," +
                        str(sim._max_served_time) + "," + str(sim._avg_served_time / len(sim.serviced_tasks)) + "," + str(sim.calculate_sd()) + "," +
                        str(sim._total_travel_distance) + "," +
                        str(sim._total_travel_distance / len(sim.actor_list)) + "," + str(sim._total_travel_distance / len(sim.serviced_tasks)) + "," +
                        str(sim._max_travel_distance) + "," + str(sim._max_queue_length) + "\n"
                    )
                    f.flush()

                    if args.actor_stats:
                        actor_stats_file = path.join(RESULTS_DIR, args.prefix + 'actor_' + args.policy + '_' +
                                                     str(args.cost_exponent) + '_' + str(args.service_time) + ".csv")
                        if not path.exists(actor_stats_file):
                            with open(actor_stats_file, 'w') as fp:
                                fp.write('cost-exponent,actor,time,changes,max-changes,path-len\n')

                        with open(actor_stats_file, 'a') as fp:
                            for actor in range(len(sim.actor_list)):
                                for (time, changes, max_changes, length) in sim.actor_list[actor].history:
                                    fp.write(str(args.cost_exponent) + ',' + str(actor) + ',' + str(time) + ',' +
                                             str(changes) + ',' + str(max_changes) + ',' + str(length) + "\n")
                            fp.flush()

        f.close()


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description=__doc__)
    argparser.add_argument(
        '--actor-stats',
        action='store_true',
        help="Record the actor's queue history for the entire test")
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
        '-c', '--cost-exponent',
        default=DEFAULT_POLICY_COST_EXPONENT,
        type=float,
        help='Power of Cost Function for Min Wait')
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
        '--prefix',
        default="",
        help='Prefix on results file name')
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
        multiple_sims(args)

    else:
        simulate(args)
