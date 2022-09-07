

import numpy as np
import random
from generators.generator import Generator
from Task import Task


class PingPongGen(Generator):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def draw(self):
        v = []

        for i in range(self.dim):
            while True:
                if self.gen_count > 3 and self.zone_one_count == 0:
                    n = self.max - 0.05
                else:
                    n = self.gen.normal(loc=self.dists[1][0], scale=self.dists[1][1])
                if n >= self.min and n <= self.max:
                    break
            v.append(n)

        if self.gen_count > 3 and self.zone_one_count == 0:
            self.zone_one_count += 1
        self.gen_count += 1

        return v

    def draw_tasks(self, lam):

        # TODO: Replace calls to expovariate with an appropriate replacement that uses
        #       the internal generator
        first_time = 0
        tasks = []

        odd = True

        sim_time = 1
        next_time = 0.49
        while True:
            new_task = Task(
                id=len(tasks),
                location=[1, 0] if odd else [0, 0],
                time=sim_time,
                service_time=0
            )

            tasks.append(new_task)
            sim_time += next_time
            next_time = 0.15
            odd = not odd

            if self.max_time is not None:
                if sim_time > self.max_time:
                    break
            else:
                if len(tasks) >= self.max_tasks:
                    break

        return tasks, first_time


def get_generator_fn():
    return PingPongGen
