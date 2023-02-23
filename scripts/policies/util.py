from math import sqrt
from Task import Task, ServiceState
from random import randint
import numpy as np


def euc_distance(task1, task2):
    return sqrt(
        (task1[0] - task2[0])**2 + (task1[1] - task2[1])**2
    )


def get_distance_matrix(actors, tasks, field=None):

    if field is None or field.is_euclidean():
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

    else:

        pending_tasks = []
        for task in tasks:
            if task.is_pending():
                pending_tasks.append(task)

        distance_matrix = np.zeros([len(pending_tasks)+1, len(pending_tasks)+1])
        task_indices = []
        actor = actors[0]
        actor_idx = 0

        task_indices.append(-1)
        for task_idx, task in enumerate(pending_tasks):
            task_idx += len(actors)
            if actor.last_task is None:
                actor.path_start_index = actor.sector
                # the actor is idle and sitting at the depot -- use that to calculate distances
                distance_matrix[actor_idx, task_idx] = field.distances[actor.sector, task.index]
                distance_matrix[task_idx, actor_idx] = field.distances[task.index, actor.sector]
            else:
                actor.path_start_index = actor.last_task.index
                # a little more complicated -- the actor is somewhere between the last task and the depot  - use a mix of both distances
                distance_last_to_home = field.distances[actor.last_task.index, actor.sector]
                distance_matrix[actor_idx, task_idx] = (field.distances[actor.sector, task.index] + distance_last_to_home * (1 - actor.ratio_complete))*(actor.ratio_complete) + \
                                                       (field.distances[actor.last_task.index, task.index] +
                                                        distance_last_to_home * actor.ratio_complete)*(1.0-actor.ratio_complete)
                distance_matrix[task_idx, actor_idx] = (field.distances[task.index, actor.sector] + distance_last_to_home * (1 - actor.ratio_complete))*(actor.ratio_complete) + \
                                                       (field.distances[task.index, actor.last_task.index] +
                                                        distance_last_to_home * actor.ratio_complete)*(1.0-actor.ratio_complete)

        # now complete the rest of the tasks
        for src_idx, src_task in enumerate(pending_tasks):
            task_indices.append(task.id)
            src_idx += len(actors)
            for dst_idx, dst_task in enumerate(pending_tasks):
                dst_idx += len(actors)
                distance_matrix[src_idx, dst_idx] = field.distances[src_task.index, dst_task.index]

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
            actors[actor_index].path.append((tasks[task_index], None))

        actors[actor_index].path.append((Task(-1, actors[actor_index].get_depot(), -1), None))

        # store the complete path as well for visualization purposes
        for index in tours[actor_index][1:]:
            task_index = task_indices[index]
            actors[actor_index].complete_path.append(tasks[task_index])
        actors[actor_index].complete_path.append(Task(-1, actors[actor_index].get_depot(), -1))

    return actors


def assign_time_tour_to_actor(actor, tasks, distances, tours, task_indices, eta=1, eta_first=False):
    # reset the actor's path
    actor.path = []

    tour = tours[0]
    tour_len = len(tours[0]) - 1
    tour_start = 1
    tour_end = tour_start + tour_len
    tour_step = 1

    if eta < 1:
        tour_len = min(tour_len, max(1, int(tour_len * eta)))
        if not eta_first:
            tour_start = randint(1, len(tours[0]) - tour_len)
        tour_end = tour_start + tour_len

    if distances[0, tour_start] > distances[0, tour_end-1]:
        tour_start, tour_end = tour_end - 1, tour_start - 1
        tour_step = -1
        print(f"reversing tour: {tour_start} -> {tour_end} -- {tour_start - tour_end} tasks")

    print(f"assigning a tour of {tour_len} stops starting at {tour_start}/{len(tour)}")

    # The actor is always the first row/column of the distance matrix
    actor_idx = 0
    last_index = actor_idx
    for _i in range(tour_start, tour_end, tour_step):
        index = tour[_i]
        task_index = task_indices[index]
        distance_index = task_index + 1
        tasks[task_index].service_state = ServiceState.ASSIGNED
        actor.path.append((tasks[task_index], distances[last_index, distance_index]))
        last_index = distance_index

    # add a node to the path to send the actor back to base
    actor.path.append((Task(
        id=-1,
        location=actor.get_depot(),
        sector=actor.sector,
        time=0,
        index=actor.sector,
        service_time=0
    ), distances[last_index, actor_idx]))

    # store the complete path as well for visualization purposes
    actor.complete_path = []
    if tour_step > 0:
        tour_start = 1
        tour_end = len(tour)
    else:
        tour_start = len(tour)-1
        tour_end = 0
    for _i in range(tour_start, tour_end, tour_step):
        index = tour[_i]
        task_index = task_indices[index]
        actor.complete_path.append(tasks[task_index])
    actor.complete_path.append(Task(
        id=-1,
        location=actor.get_depot(),
        sector=actor.sector,
        time=0,
        index=actor.sector,
        service_time=0
    ))
