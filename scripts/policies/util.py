from math import sqrt
from Task import Task, ServiceState
from random import randint
import numpy as np


def euc_distance(task1, task2):
    return sqrt(
        (task1[0] - task2[0])**2 + (task1[1] - task2[1])**2
    )


def get_distance_matrix(actor, tasks, field=None, actor_start_index=None):

    if field is None or field.is_euclidean():
        task_locations = []
        task_indices = []
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
        actor_idx = 0

        if actor_start_index is None:
            actor_start_index = actor.cluster_id

        task_indices.append(-1)
        for task_idx, task in enumerate(pending_tasks):
            task_idx += 1
            distance_matrix[actor_idx, task_idx] = field.distances[actor_start_index, task.index]
            distance_matrix[task_idx, actor_idx] = field.distances[task.index, actor_start_index]

        # now complete the rest of the tasks
        for src_idx, src_task in enumerate(pending_tasks):
            task_indices.append(task.id)
            src_idx += 1
            for dst_idx, dst_task in enumerate(pending_tasks):
                dst_idx += 1
                distance_matrix[src_idx, dst_idx] = field.distances[src_task.index, dst_task.index]

    return distance_matrix, task_indices


def assign_tour_to_actor(actor, tasks, tour, task_indices, eta=1, eta_first=False):
    actor.path = []
    actor.complete_path = []

    tour_len = len(tour) - 1
    tour_start = 1
    tour_end = tour_start + tour_len
    tour_step = 1

    if eta < 1:
        tour_len = min(tour_len, max(1, int(tour_len * eta)))
        if not eta_first:
            tour_start = randint(1, len(tour) - tour_len)
        tour_end = tour_start + tour_len

    start_task = tasks[task_indices[tour[tour_start]]]
    end_task = tasks[task_indices[tour[tour_end-1]]]
    if actor.distance_to(start_task.location) > actor.distance_to(end_task.location):
        tmp = tour_start
        tour_start = tour_end - 1
        tour_end = tmp - 1
        tour_step = -1
        print(f"reversing tour: {tour_start} -> {tour_end} -- {tour_start - tour_end} tasks")

    print(f"assigning a tour of {tour_len} stops starting at {tour_start}/{len(tour)}")

    for _i in range(tour_start, tour_end, tour_step):
        index = tour[_i]
        task_index = task_indices[index]
        tasks[task_index].service_state = ServiceState.ASSIGNED
        actor.path.append((tasks[task_index], None))

    actor.path.append((Task(-1, actor.get_depot(), -1), None))

    # store the complete path as well for visualization purposes
    for index in tour[1:]:
        task_index = task_indices[index]
        actor.complete_path.append(tasks[task_index])
    actor.complete_path.append(Task(-1, actor.get_depot(), -1))


def assign_time_tour_to_actor(actor, actor_pos, actor_start_index, tasks, distances, field, tour, task_indices, eta=1, eta_first=False):
    # reset the actor's path
    actor.path = []

    tour_len = len(tour) - 1
    tour_start = 1
    tour_end = tour_start + tour_len
    tour_step = 1

    if eta < 1:
        tour_len = min(tour_len, max(1, int(tour_len * eta)))
        if not eta_first:
            tour_start = randint(1, len(tour) - tour_len)
        tour_end = tour_start + tour_len

    if distances[0, tour_start] > distances[0, tour_end-1]:
        tour_start, tour_end = tour_end - 1, tour_start - 1
        tour_step = -1
        print(f"reversing tour: {tour_start} -> {tour_end} -- {tour_start - tour_end} tasks")

    print(f"assigning a tour of {tour_len} stops starting at {tour_start}/{len(tour)}")

    # reset the actor state
    actor.pos = actor_pos
    actor.current_goal = None
    actor.last_task = Task(
        id=-1,
        location=actor_pos,
        cluster_id=actor.cluster_id,
        time=0,
        index=actor_start_index,
        service_time=0
    )

    # The actor is always the first row/column of the distance matrix
    actor_idx = 0
    last_index = actor_idx
    last_task_index = None

    # reset the path time
    for _i in range(tour_start, tour_end, tour_step):
        index = tour[_i]
        task_index = task_indices[index]
        distance_index = task_index + 1
        tasks[task_index].service_state = ServiceState.ASSIGNED
        last_task_index = task_index
        actor.path.append((tasks[task_index], distances[last_index, distance_index]))
        last_index = distance_index

    distance_to_home = field.distances[tasks[last_task_index].index, actor.cluster_id]

    # add a node to the path to send the actor back to base
    actor.path.append((Task(
        id=-1,
        location=actor.get_depot(),
        cluster_id=actor.cluster_id,
        time=0,
        index=actor.cluster_id,
        service_time=0
    ), distance_to_home))

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
        cluster_id=actor.cluster_id,
        time=0,
        index=actor.cluster_id,
        service_time=0
    ))
