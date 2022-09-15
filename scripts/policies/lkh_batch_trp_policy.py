'''
TSP policy that find the optimal multi robot TSP on the unserviced tasks
'''
from copy import deepcopy
from policies.util import get_distance_matrix, assign_tours_to_actors
from random import randint, shuffle
from time import time
from numpy import inf, pad
from lkh_interface import solve_trp

from policies.quad_wait_tsp_policy import policy as our_policy, tour_cost, plan_tours
from policies.util import get_distance_matrix


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


def policy(actors, tasks, new_task_added=False, current_time=0, max_solver_time=30, service_time=0, cost_exponent=1, eta=1, eta_first=False, gamma=0):
    """tsp policy

    Args:
        actors (_type_): actors in the environment
        tasks (_type_): the tasks arrived
    """

    check_tour = False

    # TODO: ASSUMING ONLY ONE ACTOR HERE!!!
    idle_actors = []
    for actor in actors:
        if not actor.is_busy():
            idle_actors.append(actor)
    if not len(idle_actors):
        return True

    pending_tasks, task_indices = prep_tour(tasks)
    if not len(pending_tasks):
        return

    tours = solve_trp('DVR TSP', 'Distance between Pending Tasks', idle_actors[0].pos, pending_tasks,
                      simulation_time=current_time, mean_service_time=service_time, scale_factor=1000.0)

    # tour depot (the actor) is being dropped -- push it back in...
    for tour in tours:
        tour.insert(0, 1)

    if check_tour:
        chk_distance_matrix, _ = get_distance_matrix(idle_actors, pending_tasks)
        # chk_task_indices = task_indices[1:]
        chk_distance_matrix = pad(chk_distance_matrix, 1)

        lkh_cost = tour_cost(
            tours[0],
            distance_matrix=chk_distance_matrix,
            tasks=pending_tasks,
            task_indices=task_indices,
            current_time=current_time,
            service_time=service_time,
            cost_exponent=1.5
        )

        our_tours, our_task_indices, our_cost = plan_tours(
            actors=idle_actors,
            tasks=tasks,
            current_time=current_time,
            service_time=service_time,
            cost_exponent=1.5,
            max_solver_time=max_solver_time
        )
        print(f"Expected LKH Cost: {lkh_cost} -- Our Cost: {our_cost}")

        # with open("tsp_check")

    assign_tours_to_actors(idle_actors, tasks, tours, task_indices, eta=eta, eta_first=eta_first)
    return False
