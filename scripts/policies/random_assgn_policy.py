from random import randint
from Task import Task

def rnd_assgn_policy_return(actors, tasks):
    for actor in actors:
        actor.path = []

    for _task in tasks:
        if _task.serviced == True:
            continue
        rnd_index = randint(0, len(actors) - 1)
        actors[rnd_index].path.append(_task)
    
    for actor in actors:
        actor.path.append(
            Task(-1, [0,0], -1)
        )
    return actors


def rnd_assgn_policy_no_return(actors, tasks):
    for actor in actors:
        actor.path = []

    for _task in tasks:
        if _task.serviced == True:
            continue
        rnd_index = randint(0, len(actors) - 1)
        actors[rnd_index].path.append(_task)
    
    return actors

