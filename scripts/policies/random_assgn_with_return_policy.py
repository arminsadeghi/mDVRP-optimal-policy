from random import randint
from Task import Task


def policy(actors, tasks, current_time=0, service_time=0):
    for actor in actors:
        actor.path = []

    for _task in tasks:
        if _task.serviced == True:
            continue
        rnd_index = randint(0, len(actors) - 1)
        actors[rnd_index].path.append(_task)

    for actor in actors:
        actor.path.append(
            Task(-1, [0, 0], -1)
        )
    return actors
