'''
TSP policy that find the optimal multi robot TSP on the unserviced tasks
'''
from copy import deepcopy
from policies.util import get_distance_matrix, assign_time_tour_to_actor
from random import randint, shuffle
from time import time
from numpy import inf, pad
from lkh_interface import solve_time_trp
from os import path


class Policy:
    def __init__(self, args) -> None:
        try:
            self.max_solver_time = args['max_solver_time']
        except KeyError:
            self.max_solver_time = 30

        try:
            self.service_time = args['service_time']
        except KeyError:
            self.service_time = 0

        try:
            self.eta = args['eta']
        except KeyError:
            self.eta = 1

        try:
            self.eta_first = args['eta_first']
        except KeyError:
            self.eta_first = False

        try:
            self.cost_exponent = args['cost_exponent']
        except KeyError:
            self.cost_exponent = 1

    @staticmethod
    def __prep_tour(actor, tasks, field):

        # Node indices start at 1 and the first index is the position of the actor
        task_indices = [-1, -1]

        pending_tasks = []
        node = 0
        for task in tasks:
            if task.is_waiting():
                pending_tasks.append(task)
                task_indices.append(node)
                node += 1

        distances, _ = get_distance_matrix([actor,], tasks=pending_tasks, field=field)

        return distances, task_indices

    def policy(self, actor, tasks, field, current_time=0):
        """tsp policy

        Args:
            actors (_type_): actors in the environment
            tasks (_type_): the tasks arrived
        """

        if actor.is_busy():
            return

        distances, task_indices = self.__prep_tour(actor, tasks, field=field)
        if not len(tasks):
            return

        try:
            tours = solve_time_trp('DVR TRP', 'Time between Pending Tasks', tasks=tasks, distances=distances,
                                   simulation_time=current_time, mean_service_time=self.service_time, cost_exponent=self.cost_exponent, scale_factor=100.0)
        except Exception as e:
            print(e)
            print("ERROR!")

        # tour depot (the actor) is being dropped -- push it back in...
        tours[0].insert(0, 1)

        assign_time_tour_to_actor(actor, tasks=tasks, distances=distances, tour=tours[0], task_indices=task_indices,
                                  eta=self.eta, eta_first=self.eta_first)
        return False


def get_policy(args):
    policy = Policy(args)

    return policy.policy
