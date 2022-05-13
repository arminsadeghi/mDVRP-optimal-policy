

import numpy as np
import random
from Task import Task
from generators.generator import Generator


class BadBusGen(Generator):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.reset()

    def draw(self):
        v = []
        for i in range(self.dim):
            while True:
                n = self.gen.normal(loc=0.15, scale=0.05)
                if n >= self.min and n <= self.max:
                    break
            v.append(n)
        return v

    def draw_tasks(self, lam):

        first_time = True

        e1 = [0.75, 0.75]
        e2 = [0.75, 0.85]

        tasks = []

        odd = True

        sim_time = 1
        next_time = 1.1

        while True:
            # create one task right beside the current one
            tasks.append(Task(
                id=len(tasks),
                location=e1 if odd else e2,
                time=sim_time,
                service_time=self.service_time
            ))

            if not first_time:
                # and two tasks on the other side of the map
                # TODO: Fixed service time
                tasks.append(Task(
                    id=len(tasks),
                    location=self.draw(),
                    time=sim_time,
                    service_time=self.service_time
                ))
                tasks.append(Task(
                    id=len(tasks),
                    location=self.draw(),
                    time=sim_time,
                    service_time=self.service_time
                ))

            first_time = False

            sim_time += next_time
            next_time = self.service_time + 0.1
            odd = not odd

            if self.max_time is not None:
                if sim_time > self.max_time:
                    break
            else:
                if len(tasks) >= self.max_tasks:
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
