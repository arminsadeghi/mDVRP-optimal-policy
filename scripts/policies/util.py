from math import sqrt
from Task import Task, ServiceState
from random import randint
import numpy as np


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
        if task.is_pending():
            task_locations.append(task.location)
            task_indices.append(task.id)

    distance_matrix = np.zeros([len(task_locations), len(task_locations)])
    for _i in range(len(task_locations)):
        for _j in range(_i, len(task_locations)):
            dist = euc_distance(task_locations[_i], task_locations[_j])
            distance_matrix[_i, _j] = dist
            distance_matrix[_j, _i] = dist

    return distance_matrix, task_indices


def assign_tours_to_actors(actors, tasks, tours, task_indices, eta=1, eta_first=False):
    for actor in actors:
        actor.path = []
        actor.complete_path = []

    for actor_index in range(len(actors)):

        tour_len = len(tours[actor_index]) - 1
        tour_start = 1
        tour_end = tour_start + tour_len
        tour_step = 1

        if eta < 1:
            tour_len = min(tour_len, max(1, int(tour_len * eta)))
            if not eta_first:
                tour_start = randint(1, len(tours[actor_index]) - tour_len)
            tour_end = tour_start + tour_len

            start_task = tasks[task_indices[tours[actor_index][tour_start]]]
            end_task = tasks[task_indices[tours[actor_index][tour_end-1]]]
            if actors[actor_index].distance_to(start_task.location) > actors[actor_index].distance_to(end_task.location):
                tmp = tour_start
                tour_start = tour_end - 1
                tour_end = tmp - 1
                tour_step = -1
                print(f"reversing tour: {tour_start} -> {tour_end} -- {tour_start - tour_end} tasks")

            print(f"assigning a tour of {tour_len} stops starting at {tour_start}/{len(tours[actor_index])}")

        for _i in range(tour_start, tour_end, tour_step):
            index = tours[actor_index][_i]
            task_index = task_indices[index]
            tasks[task_index].service_state = ServiceState.ASSIGNED
            actors[actor_index].path.append(tasks[task_index])

        actors[actor_index].path.append(Task(-1, actors[actor_index].get_depot(), -1))

        # store the complete path as well for visualization purposes
        for index in tours[actor_index][1:]:
            task_index = task_indices[index]
            actors[actor_index].complete_path.append(tasks[task_index])
        actors[actor_index].complete_path.append(Task(-1, actors[actor_index].get_depot(), -1))

    return actors
