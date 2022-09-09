'''
TSP policy that find the optimal multi robot TSP on the unserviced tasks
'''
from copy import deepcopy
from policies.util import get_distance_matrix, assign_tours_to_actors
from random import randint, shuffle, random
from time import time
from numpy import inf
from Task import ServiceState


def initialize_tours(actors):
    tours = {}
    for _i in range(len(actors)):
        tours[_i] = []
        tours[_i].append(_i)

    return tours


def random_task_assignment(tours, num_tasks):
    num_actors = len(tours)

    for _i in range(num_actors, num_tasks):
        rnd_actor = randint(0, num_actors - 1)
        tours[rnd_actor].append(_i)
    return tours


def tour_cost(tour, distance_matrix, tasks, task_indices, current_time, service_time, cost_exponent):
    """calculate the total wait time of the tasks given the tour

    Args:
        tour (_type_): the sequence of the tasks
        distance_matrix (_type_): distance matrix
        tasks (_type_): the list of the tasks
        task_indices (_type_): the indices of the tasks in the original task list
        current_time (_type_): the current simulation time

    Returns:
        _type_: returns the cost of the tour
    """

    cost_to_vertex = [0]
    for _i in range(len(tour) - 1):
        cost_to_vertex.append(cost_to_vertex[_i] + distance_matrix[(tour[_i], tour[_i + 1])] + service_time)

    if cost_exponent:
        cost = 0
        for _i in range(len(tour)):
            wait_time = cost_to_vertex[_i] - tasks[task_indices[tour[_i]]].time + current_time
            cost += wait_time ** cost_exponent
    else:
        cost = cost_to_vertex[-1]

    return cost


def random_deletion(tours, p=1):

    candidate_tour = deepcopy(tours)
    deleted_vertices = []

    total_vertices = 0
    for _i in range(len(tours)):
        total_vertices += len(tours[_i])

    if p > total_vertices - len(tours):
        p = max([1, int((total_vertices - len(tours))/2) - 1])

    while (len(deleted_vertices) < p):
        rnd_actor = randint(0, len(tours) - 1)
        if len(tours[rnd_actor]) < 2:
            continue

        rnd_index = randint(1, len(candidate_tour[rnd_actor]) - 1)
        deleted_vertices.append(candidate_tour[rnd_actor].pop(rnd_index))
    return deleted_vertices, candidate_tour


def min_cost_insertion(tours, deleted_vertices, distance_matrix, tasks, task_indices, current_time, service_time, cost_exponent):
    shuffle(deleted_vertices)
    for vertex in deleted_vertices:
        best_tour = None
        best_index = None
        min_cost = inf
        for key, tour in tours.items():
            prev_cost = tour_cost(tour, distance_matrix, tasks, task_indices, current_time, service_time, cost_exponent)
            candid_tour = deepcopy(tour)
            for _j in range(1, len(tour)+1):

                candid_tour.insert(_j, vertex)
                candid_cost = tour_cost(candid_tour, distance_matrix, tasks, task_indices, current_time, service_time, cost_exponent)
                candid_tour.pop(_j)

                insertion_cost = candid_cost - prev_cost
                if insertion_cost < min_cost:
                    best_tour = tour
                    best_index = _j
                    min_cost = insertion_cost

        best_tour.insert(best_index, vertex)
    return tours


def rnd_insertion(tours, deleted_vertices):
    shuffle(deleted_vertices)
    for vertex in deleted_vertices:
        rnd_tour = randint(0, len(tours) - 1)
        n = len(tours[rnd_tour]) - 1

        if n == 0:
            tours[rnd_tour].append(vertex)
            continue

        rnd_loc = randint(1, n)

        if rnd_loc == n:
            tours[rnd_tour].append(vertex)
        else:
            tours[rnd_tour].insert(rnd_loc, vertex)
    return tours


def total_tour_cost(tours, distance_matrix, tasks, task_indices, current_time, service_time, cost_exponent):
    total_cost = 0
    for _i in range(len(tours)):
        total_cost += tour_cost(tours[_i], distance_matrix, tasks, task_indices, current_time, service_time, cost_exponent)
    return total_cost


def validate_tours(actors, tasks, tours, task_indices, gamma=1):
    valid_actors = []
    valid_tours = []

    # Walk backwards through the list of actors and check each trajectory
    for actor_index in range(len(actors)-1, -1, -1):

        tour_OK = True
        tour_len = len(tours[actor_index]) - 1
        threshold = int(round(gamma * tour_len))

        # if the actor isn't doing anything, we replan regardless
        if actors[actor_index].is_busy():
            # note that the tour always starts with the actor's current location (+1)
            for _i in range(1+threshold, 1+tour_len):
                index = tours[actor_index][_i]
                task_index = task_indices[index]
                if tasks[task_index].service_state == ServiceState.WAITING:
                    # new task appeared after the threshold - toss this tour as we're already overloaded
                    print(f"Rejecting path, over threshold:  {_i}/{tour_len+1} [{threshold+1}]")
                    tour_OK = False
                    break

        if tour_OK:
            # move all tasks on the subtour to assigned
            for _i in range(1, 1+threshold):
                index = tours[actor_index][_i]
                task_index = task_indices[index]
                tasks[task_index].service_state = ServiceState.ASSIGNED
            valid_actors.append(actors[actor_index])
            valid_tours.append(tours[actor_index])

    return valid_actors, valid_tours


def tasks_waiting(tasks):
    tasks_waiting = 0

    for task in tasks:
        if task.is_pending():
            tasks_waiting += 1

    return tasks_waiting


def actors_idle(actors):
    idle_actors = 0

    for actor in actors:
        if not actor.is_busy():
            idle_actors += 1

    return idle_actors


def policy(actors, tasks, new_task_added=False, current_time=0, max_solver_time=30, service_time=0, cost_exponent=2, eta=1, eta_first=False, gamma=0):
    """tsp policy

    Args:
        actors (_type_): actors in the environment
        tasks (_type_): the tasks arrived
    """

    distance_matrix, task_indices = get_distance_matrix(actors, tasks)
    tours = initialize_tours(actors)
    total = len(task_indices) - len(actors)

    if not (new_task_added or (tasks_waiting(tasks=tasks) and actors_idle(actors=actors))):
        # nothing to do
        return

    best_tours = random_task_assignment(tours, len(task_indices))

    best_cost = total_tour_cost(best_tours, distance_matrix, tasks, task_indices, current_time, service_time, cost_exponent)
    s_time = time()
    iterations_since_last_improvement = 0
    iter_count = 0
    print("initial cost", best_cost)
    iteration_limit = False

    while time() - s_time < max_solver_time:
        candidate_tours = deepcopy(best_tours)

        deleted_vertices, candidate_tours = random_deletion(candidate_tours, p=2)
        # if random() < 0.8:
        candidate_tours = min_cost_insertion(candidate_tours, deleted_vertices, distance_matrix, tasks,
                                             task_indices, current_time, service_time, cost_exponent)
        # else:
        #     candidate_tours = rnd_insertion(candidate_tours, deleted_vertices)
        candidate_tour_cost = total_tour_cost(candidate_tours, distance_matrix, tasks, task_indices, current_time, service_time, cost_exponent)

        if candidate_tour_cost < best_cost:
            best_cost = candidate_tour_cost
            best_tours = candidate_tours
            iterations_since_last_improvement = 0
            print("improved cost", best_cost)
        else:
            iterations_since_last_improvement += 1

        if iterations_since_last_improvement > 1000:
            # print("Hit Iteration Limit")
            iteration_limit = True
            break

        iter_count += 1

    if not iteration_limit:
        print("WARNING: Time expired while searching")

    # check the tours and remove any that are over the threshold
    actors, tours = validate_tours(actors, tasks, best_tours, task_indices, gamma=gamma)

    assign_tours_to_actors(actors, tasks, tours, task_indices, eta=eta, eta_first=eta_first)
    return False
