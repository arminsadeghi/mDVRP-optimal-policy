from random import randint
from Task import Task, ServiceState


def policy(actors, tasks, new_task_added=False, current_time=0, service_time=0, cost_exponent=1, eta=1):
    if not new_task_added:
        return False

    for actor in actors:
        actor.path = []

    for _task in tasks:
        if _task.service_state == ServiceState.WAITING:
            rnd_index = randint(0, len(actors) - 1)
            actors[rnd_index].path.append(_task)

    for actor in actors:
        actor.path.append(
            Task(-1, [0, 0], -1)
        )
    return False
