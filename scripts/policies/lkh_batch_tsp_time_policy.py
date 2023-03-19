'''
TSP policy that find the optimal multi robot TSP on the unserviced tasks
'''
from policies.util import get_distance_matrix, assign_time_tour_to_actor
from random import randint, shuffle
from time import time
import numpy as np
from lkh_interface import solve_time_tsp


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

        try:
            self.sectors = args['sectors']
            self.sector_angle = np.pi * 2 / self.sectors
        except:
            self.sectors = 1
            self.sector_angle = np.pi
        self.current_sector = 0

    @staticmethod
    def __calc_lines(angles, depot):
        lines = []
        sx = depot[0]
        sy = depot[1]
        for i in range(len(angles)):
            ex = sx + np.cos(angles[i])
            ey = sy + np.sin(angles[i])
            lines.append(((sx, sy), (ex, ey)))
        return lines

    # Positive if left, neg if right
    @staticmethod
    def __side(line, px, py):
        v1, v2 = line
        return (v2[0] - v1[0]) * (py - v1[1]) - (px - v1[0]) * (v2[1] - v1[1])

    @staticmethod
    def __task_in_sector(task, lines):
        if Policy.__side(lines[0], task.location[0], task.location[1]) >= 0 and Policy.__side(lines[1], task.location[0], task.location[1]) < 0:
            return True

    def __next_sector(self, actor):
        actor.current_sector = (actor.current_sector + 1) % self.sectors

    def __prep_tour(self, actor, actor_start_index, tasks, field):

        # Node indices start at 1 and the first index is the position of the actor
        task_indices = [-1, -1]

        pending_tasks = []
        node = 0

        for _ in range(self.sectors):
            angle_start = actor.current_sector * self.sector_angle
            angle_end = (actor.current_sector + 1) * self.sector_angle
            lines = self.__calc_lines(angles=[angle_start, angle_end], depot=actor.depot)

            for task in tasks:
                if task.is_waiting() and (self.sectors == 1 or self.__task_in_sector(task, lines=lines)):
                    pending_tasks.append(task)
                    task_indices.append(node)
                    node += 1

            if len(pending_tasks):
                break

            self.__next_sector(actor=actor)

        distances, _ = get_distance_matrix(actor, actor_start_index=actor_start_index, tasks=pending_tasks, field=field)

        return pending_tasks, distances, task_indices

    def policy(self, actor, tasks, field, current_time=0):
        """tsp policy

        Args:
            actors (_type_): actors in the environment
            tasks (_type_): the tasks arrived
        """

        if actor.is_busy():
            return

        path_start_index, actor_pos = actor.get_nearest_location()

        tasks, distances, task_indices = self.__prep_tour(actor, actor_start_index=path_start_index, tasks=tasks, field=field)
        if not len(tasks):
            return False

        tours = solve_time_tsp('DVR TSP', 'Distance between Pending Tasks', distances, scale_factor=100.0)

        assign_time_tour_to_actor(actor, actor_pos=actor_pos, actor_start_index=path_start_index, tasks=tasks, distances=distances, field=field, tour=tours[0], task_indices=task_indices,
                                  eta=self.eta, eta_first=self.eta_first)
        self.__next_sector(actor)

        return True


def get_policy(args):
    policy = Policy(args)

    return policy.policy
