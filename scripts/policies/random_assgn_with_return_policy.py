from random import randint
from Task import Task, ServiceState


def policy(actors, tasks, new_task_added=False, current_time=0, service_time=0, cost_exponent=1, eta=1, eta_first=False,  gamma=0):

    idle_actors = []
    for actor in actors:
        if not actor.is_busy():
            idle_actors.append(actor)

    if not len(idle_actors):
        return True

    for actor in idle_actors:
        actor.path = []

    pending_tasks = []
    for _task in tasks:
        if _task.is_pending():
            pending_tasks.append(_task)

    if not len(pending_tasks):
        return

    for actor in idle_actors:
        rnd_index = randint(0, len(pending_tasks)-1)
        actor.path.append(pending_tasks.pop(rnd_index))

    for actor in actors:
        actor.path.append(
            Task(-1, [0.5, 0.5], -1)
        )
    return False
