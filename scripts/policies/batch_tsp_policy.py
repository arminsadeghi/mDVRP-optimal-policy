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
            for _j in range(len(tours[_i]) - 1):
                insertion_cost = distance_matrix[(
                    tours[_i][_j], vertex
                )]

                insertion_cost += distance_matrix[(
                    tours[_i][_j + 1], vertex
                )]

                insertion_cost -= distance_matrix[(
                    tours[_i][_j], tours[_i][_j + 1]
                )]

                if insertion_cost < min_cost:
                    best_tour = _i
                    best_index = _j
                    min_cost = insertion_cost

            # check the cost of appending
            _j = len(tours[_i]) - 1
            insertion_cost = distance_matrix[(
                tours[_i][_j], vertex
            )]
            if insertion_cost < min_cost:
                best_tour = _i
                best_index = _j
                min_cost = insertion_cost

        if best_index > len(tours[best_tour]) - 2:
            tours[best_tour].append(vertex)
        else:
            tours[best_tour].insert(
                best_index + 1, vertex
            )
    return tours


def total_tour_cost(tours, distance_matrix):
    total_cost = 0
    for _i in range(len(tours)):
        total_cost += tour_cost(tours[_i], distance_matrix)
    return total_cost


def policy(actors, tasks, new_task_added=False, current_time=0, max_solver_time=30, service_time=0, cost_exponent=1, eta=1, eta_first=False, gamma=0):
    """tsp policy

    Args:
        actors (_type_): actors in the environment
        tasks (_type_): the tasks arrived
    """

    idle_actors = []
    for actor in actors:
        if not actor.is_busy():
            idle_actors.append(actor)

    if not len(idle_actors):
        return True

    # TODO: with multiple agents, we need to make sure that we aren't reassigning tasks that
    #       have already been sent to an agent for handling -- probably need a new
    #       TASK_ASSIGNED state to be created
    distance_matrix, task_indices = get_distance_matrix(idle_actors, tasks)
    tours = initialize_tours(idle_actors)

    total = len(task_indices) - len(idle_actors)
    if total <= 0:
        # nothing to do
        return

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
        else:
            iterations_since_last_improvement += 1

        if iterations_since_last_improvement > 1000:
            break
        iter_count += 1
    assign_tours_to_actors(idle_actors, tasks, best_tours, task_indices, eta=eta)
    return False
