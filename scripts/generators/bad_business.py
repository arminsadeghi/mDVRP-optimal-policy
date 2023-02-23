

import numpy as np
import random
from Task import Task
from generators.generator import Generator


class BadBusGen(Generator):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.reset()

    def draw(self, pos, stdev):
        v = []
        for i in range(self.dim):
            while True:
                n = self.gen.normal(loc=pos, scale=stdev)
                if n >= self.min and n <= self.max:
                    break
            v.append(n)
        return v

    def draw_tasks(self, lam):

        first_time = True

        tasks = []

        sim_time = 1
        next_time = self.service_time + 0.001

        while True:

            # create one task right beside the current one
            tasks.append(Task(
                id=len(tasks),
                location=self.draw(pos=0.75, stdev=0.01),
                time=sim_time,
                service_time=self.service_time
            ))

            # and two tasks on the other side of the map
            # TODO: Fixed service time
            tasks.append(Task(
                id=len(tasks),
                location=self.draw(pos=0.15, stdev=0.05),
                time=sim_time,
                service_time=self.service_time
            ))
            # tasks.append(Task(
            #     id=len(tasks),
            #     location=self.draw(pos=0.15, stdev=0.05),
            #     time=sim_time,
            #     service_time=self.service_time
            # ))

            first_time = False

            sim_time += next_time

            if self.max_time is not None:
                if sim_time > self.max_time:
                    break
            else:
                if len(tasks) >= self.total_tasks:
                    break

        return tasks, first_time

    def test(self):
        size = 100
        points = 50000
        data = np.zeros((size, size))

        self.reset()
        for i in range(points):
            x, y = self.draw()
            x = int(x * size)
            y = int(y * size)

            data[x, y] += 1

        data = (255.0 * (data / np.max(data))).astype(np.uint8)

        import matplotlib.pyplot as plt

        plt.figure()
        plt.imshow(data)
        plt.show(block=True)


def get_generator_fn():
    return BadBusGen


if __name__ == '__main__':

    gen_fn = get_generator_fn()
    generator = gen_fn(
        seed=None
    )
    generator.test()

    print('done')
