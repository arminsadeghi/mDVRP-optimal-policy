'''
TSP policy that find the optimal multi robot TSP on the unserviced tasks
'''
from copy import deepcopy
from policies.util import get_distance_matrix, assign_tour_to_actor
from time import time
from numpy import inf, pad
from lkh_interface import solve_trp
from os import path

from policies.quad_wait_tsp_policy import policy as our_policy, tour_cost, plan_tours


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

        self.check_tour = False
        if self.check_tour:
            self.fname = 'trp_costs.csv'
            if not path.exists(self.fname):
                with open(self.fname, 'w') as fp:
                    fp.write('lkh-cost,2opt-cost,length,same-first-step\n')

    @staticmethod
    def __prep_tour(tasks):
        pending_tasks = []

        # Node indices start at 1 and the first index is the position of the actor
        task_indices = [-1, -1]

        node = 0
        for task in tasks:
            if task.is_waiting():
                pending_tasks.append(task)
                task_indices.append(node)
                node += 1

        return pending_tasks, task_indices

    def policy(self, actor, tasks, field, current_time=0):
        """tsp policy

        Args:
            actors (_type_): actors in the environment
            tasks (_type_): the tasks arrived
        """

        if actor.is_busy():
            return

        pending_tasks, task_indices = self.__prep_tour(tasks)
        if not len(pending_tasks):
            return

        tours = solve_trp('DVR TSP', 'Distance between Pending Tasks', actor.pos, pending_tasks,
                          simulation_time=current_time, mean_service_time=self.service_time, cost_exponent=self.cost_exponent,
                          scale_factor=10000.0)

        # tour depot (the actor) is being dropped -- push it back in...
        for tour in tours:
            tour.insert(0, 1)

        if self.check_tour:
            chk_distance_matrix, _ = get_distance_matrix(actor, tasks=pending_tasks)
            chk_distance_matrix = pad(chk_distance_matrix, 1)

            lkh_cost = tour_cost(
                tours[0],
                distance_matrix=chk_distance_matrix,
                tasks=pending_tasks,
                task_indices=task_indices,
                current_time=current_time,
                service_time=self.service_time,
                cost_exponent=1.5
            )

            our_tours, our_task_indices, our_cost = plan_tours(
                actors=[actor,],
                tasks=tasks,
                current_time=current_time,
                service_time=self.service_time,
                cost_exponent=1.5,
                max_solver_time=self.max_solver_time
            )
            first_lkh_id = pending_tasks[task_indices[tours[0][1]]]
            first_our_id = tasks[our_task_indices[our_tours[0][1]]]
            print(f"Expected LKH Cost: {lkh_cost} -- Our Cost: {our_cost} -- Same First: {first_lkh_id == first_our_id}")

            with open(self.fname, "a") as fp:
                fp.write(f'{lkh_cost},{our_cost},{len(tours[0])}\n')

        assign_tour_to_actor(actor, pending_tasks, tours[0], task_indices, eta=self.eta, eta_first=self.eta_first)
        return False


def get_policy(args):
    policy = Policy(args)
    return policy.policy
