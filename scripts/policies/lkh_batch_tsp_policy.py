'''
TSP policy that find the optimal multi robot TSP on the unserviced tasks
'''
from copy import deepcopy
from policies.util import get_distance_matrix, assign_tours_to_actors
from random import randint, shuffle
from time import time
from numpy import inf
from lkh_interface import solve_tsp


def prep_tour(tasks):
    pending_tasks = []

    # Node indices start at 1 and the first index is the position of the actor
    task_indices = [-1, -1]

    node = 0
    for task in tasks:
        if task.is_pending():
            pending_tasks.append(task)
            task_indices.append(node)
            node += 1

    return pending_tasks, task_indices


def policy(actors, tasks, field, new_task_added=False, current_time=0, max_solver_time=30, service_time=0, cost_exponent=1, eta=1, eta_first=False, gamma=0):
    """tsp policy

    Args:
        actors (_type_): actors in the environment
        tasks (_type_): the tasks arrived
    """

    # TODO: ASSUMING ONLY ONE ACTOR HERE!!!
    idle_actors = []
    for actor in actors:
        if not actor.is_busy():
            idle_actors.append(actor)
    if not len(idle_actors):
        return True

    tasks, task_indices = prep_tour(tasks)
    if not len(tasks):
        return

    tours = solve_tsp('DVR TSP', 'Distance between Pending Tasks', idle_actors[0].pos, tasks, scale_factor=10000.0)

    assign_tours_to_actors([idle_actors[0],], tasks, tours, task_indices, eta=eta, eta_first=eta_first)

    return False
