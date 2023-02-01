'''
TSP policy that find the optimal multi robot TSP on the unserviced tasks
'''
from copy import deepcopy
from policies.util import get_distance_matrix, assign_time_tour_to_actor
from random import randint, shuffle
from time import time
from numpy import inf
from lkh_interface import solve_time_tsp


def prep_tour(actor, tasks, field):

    # Node indices start at 1 and the first index is the position of the actor
    task_indices = [-1, -1]

    pending_tasks = []
    node = 0
    for task in tasks:
        if task.is_pending():
            pending_tasks.append(task)
            task_indices.append(node)
            node += 1

    distances, _ = get_distance_matrix([actor,], tasks=pending_tasks, field=field)

    return distances, task_indices


def policy(actors, tasks, field, current_time=0, max_solver_time=30, service_time=0, cost_exponent=1, eta=1, eta_first=False, gamma=0):
    """tsp policy

    Args:
        actors (_type_): actors in the environment
        tasks (_type_): the tasks arrived
    """

    distances, task_indices = prep_tour(actors[0], tasks, field=field)
    if not len(tasks):
        return

    tours = solve_time_tsp('DVR TSP', 'Distance between Pending Tasks', distances, scale_factor=100.0)

    assign_time_tour_to_actor(actors[0], tasks=tasks, distances=distances, tours=tours, task_indices=task_indices, eta=eta, eta_first=eta_first)

    return False
