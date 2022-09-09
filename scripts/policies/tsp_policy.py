'''
TSP policy that find the optimal multi robot TSP on the unserviced tasks
'''
from copy import deepcopy
from policies.util import get_distance_matrix, assign_tours_to_actors
from random import randint, shuffle
from time import time
from numpy import inf


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


def tour_cost(tour, distance_matrix):
    cost = 0
    for _i in range(len(tour) - 1):
        cost += distance_matrix[(
            tour[_i], tour[_i + 1]
        )]
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


def min_cost_insertion(tours, deleted_vertices, distance_matrix):

    shuffle(deleted_vertices)
    for vertex in deleted_vertices:
        best_tour = 0
        best_index = len(tours[0])
        min_cost = inf
        for _i in range(len(tours)):
            for _j in range(0, len(tours[_i]) - 1):
                insertion_cost = distance_matrix[(tours[_i][_j], vertex)] + \
                    distance_matrix[(vertex, tours[_i][_j + 1])]

                insertion_cost -= distance_matrix[(tours[_i][_j], tours[_i][_j + 1])]

                if insertion_cost < min_cost:
                    best_tour = _i
                    best_index = _j
                    min_cost = insertion_cost

            # check the cost of appending
            insertion_cost = distance_matrix[(
                tours[_i][-1], vertex
            )]
            if insertion_cost < min_cost:
                best_tour = _i
                best_index = len(tours[_i])
                min_cost = insertion_cost

        tours[best_tour].insert(best_index + 1, vertex)

    return tours


def total_tour_cost(tours, distance_matrix):
    total_cost = 0
    for _i in range(len(tours)):
        total_cost += tour_cost(tours[_i], distance_matrix)
    return total_cost


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


def policy(actors, tasks, new_task_added=False, current_time=0, max_solver_time=30, service_time=0, cost_exponent=0, eta=1, eta_first=False,  gamma=0):
    """tsp policy

    Args:
        actors (_type_): actors in the environment
        tasks (_type_): the tasks arrived
    """

    if not (new_task_added or (tasks_waiting(tasks=tasks) and actors_idle(actors=actors))):
        # nothing to do
        return

    distance_matrix, task_indices = get_distance_matrix(actors, tasks)
    tours = initialize_tours(actors)

    best_tours = random_task_assignment(tours, len(task_indices))
    best_cost = total_tour_cost(best_tours, distance_matrix)

    s_time = time()
    iterations_since_last_improvement = 0
    iter_count = 0
    while time() - s_time < max_solver_time:
        candidate_tours = deepcopy(best_tours)
        deleted_vertices, candidate_tours = random_deletion(candidate_tours, p=2)
        candidate_tours = min_cost_insertion(candidate_tours, deleted_vertices, distance_matrix)
        candidate_tour_cost = total_tour_cost(candidate_tours, distance_matrix)
        if candidate_tour_cost < best_cost:
            best_cost = candidate_tour_cost
            best_tours = candidate_tours
            iterations_since_last_improvement = 0
            print("improved cost", best_cost)
        else:
            iterations_since_last_improvement += 1

        if iterations_since_last_improvement > 1000:
            break
        iter_count += 1
    assign_tours_to_actors(actors, tasks, best_tours, task_indices, eta=eta, eta_first=eta_first)
    return False
