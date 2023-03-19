'''
TSP policy that find the optimal multi robot TSP on the unserviced tasks
'''
from copy import deepcopy
from policies.util import get_distance_matrix, assign_tour_to_actor
from time import time
from lkh_interface import solve_trp
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
            self.cost_exponent = args['cost_exponent']
        except KeyError:
            self.cost_exponent = 1

    @staticmethod
    def __prep_tour(actor, tasks, field):
        pending_tasks = []

        # Node indices start at 1 and the first index is the position of the actor
        task_indices = [-1, -1]

        node = 0
        at_least_one_waiting = False
        for task in tasks:
            # TODO: This will cause problems with actors stealing tasks from each other -- should check that the task is
            #       assigned to this particular actor.  Next time....
            if task.is_pending():
                if task.is_waiting():
                    at_least_one_waiting = True
                pending_tasks.append(task)
                task_indices.append(node)
                node += 1

        if not at_least_one_waiting:
            return [], [], False

        return pending_tasks, task_indices, at_least_one_waiting

    def policy(self, actor, tasks, field, current_time=0):
        """tsp policy

        Args:
            actors (_type_): actors in the environment
            tasks (_type_): the tasks arrived
        """

        tasks, task_indices, new_task_arrived = self.__prep_tour(tasks)
        if not len(tasks) or not new_task_arrived:
            return

        tours = solve_trp('DVR TSP', 'Distance between Pending Tasks', actor.pos, tasks,
                          simulation_time=current_time, mean_service_time=self.service_time, cost_exponent=self.cost_exponent,
                          scale_factor=10000.0)

        # tour depot (the actor) is being dropped -- push it back in...
        for tour in tours:
            tour.insert(0, 1)

        assign_tour_to_actor(actor, tasks, tours[0], task_indices, eta=self.eta, eta_first=self.eta_first)
        return False


def get_policy(args):
    policy = Policy(args)

    return policy.policy
