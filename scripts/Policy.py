from random import randint

def base_policy(self, actors, tasks):
    for _task in tasks:
        rnd_index = randint(0, len(self.actors) - 1)
        self.actors[rnd_index].path.append(_task)
    return self.actors
