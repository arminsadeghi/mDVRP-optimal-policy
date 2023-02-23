'''
TSP policy that find the optimal multi robot TSP on the unserviced tasks
'''
from copy import deepcopy
from policies.util import get_distance_matrix, assign_tours_to_actors
from random import randint, shuffle
from time import time
from numpy import inf, pad
from lkh_interface import solve_trp
from os import path

from policies.quad_wait_tsp_policy import policy as our_policy, tour_cost, plan_tours

fname = 'trp_costs.csv'
if not path.exists(fname):
    with open(fname, 'w') as fp:
        fp.write('lkh-cost,2opt-cost,length,same-first-step\n')


def prep_tour(tasks):
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


def policy(actors, tasks, field, new_task_added=False, current_time=0, max_solver_time=30, service_time=0, cost_exponent=1, eta=1, eta_first=False):
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
                      simulation_time=current_time, mean_service_time=service_time, cost_exponent=cost_exponent, scale_factor=10000.0)

    # tour depot (the actor) is being dropped -- push it back in...
    for tour in tours:
        tour.insert(0, 1)

    if check_tour:
        chk_distance_matrix, _ = get_distance_matrix(idle_actors, pending_tasks)
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
        first_lkh_id = pending_tasks[task_indices[tours[0][1]]]
        first_our_id = tasks[our_task_indices[our_tours[0][1]]]
        print(f"Expected LKH Cost: {lkh_cost} -- Our Cost: {our_cost} -- Same First: {first_lkh_id == first_our_id}")

        with open(fname, "a") as fp:
            fp.write(f'{lkh_cost},{our_cost},{len(tours[0])}\n')

    assign_tours_to_actors(idle_actors, pending_tasks, tours, task_indices, eta=eta, eta_first=eta_first)
    return False
