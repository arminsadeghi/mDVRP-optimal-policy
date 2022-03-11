from math import sqrt
from Task import Task


def euc_distance(task1, task2):
    return sqrt(
        (task1[0] - task2[0])**2 + (task1[1] - task2[1])**2
    )


def get_distance_matrix(actors, tasks):
    task_locations = []
    task_indices = []
    for actor in actors:
        task_locations.append(
            actor.pos
        )
        task_indices.append(-1)

    for task in tasks:
        if task.serviced == True:
            continue
        task_locations.append(task.location)
        task_indices.append(task.id)

    distance_matrix = {}
    for _i in range(len(task_locations)):
        for _j in range(_i, len(task_locations)):
            dist = euc_distance(task_locations[_i], task_locations[_j])
            distance_matrix[(_i, _j)] = dist
            distance_matrix[(_j, _i)] = dist

    return distance_matrix, task_indices


def assign_tours_to_actors(actors, tasks, tours, task_indices):
    for actor in actors:
        actor.path = []

    for actor_index in range(len(actors)):
        for _i in range(1, len(tours[actor_index])):
            index = tours[actor_index][_i]
            task_index = task_indices[index]
            actors[actor_index].path.append(tasks[task_index])
        actors[actor_index].path.append(
            Task(-1, [0, 0], -1)
        )

    return actors
