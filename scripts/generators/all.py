import numpy as np
from generators.generator import Generator
from generators.uniform import UniformGen
from Task import Task


class AllGen(UniformGen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def draw_tasks(self, lam):

        first_time = 0
        tasks = []

        assert(self.max_tasks > 0)
        for i in range(0, self.max_tasks):
            new_task = Task(
                id=len(tasks),
                location=super().draw(),
                time=0,
                # TODO: Fixing service time variance proportional to specified time
                service_time=self.gen.normal(self.service_time, 0.1*self.service_time)
            )
            tasks.append(new_task)

        return tasks, first_time


def get_generator_fn():
    return AllGen


if __name__ == '__main__':

    size = 100
    points = 50000
    data = np.zeros((size, size))
    gen_fn = get_generator_fn()
    uniform_generator = gen_fn(
        min=-1,
        max=1,
        dim=2,
        seed=None
    )

    for i in range(points):
        x, y = uniform_generator.draw()
        x = int(min(max((x+1) / 2 * size, 0), size-1))
        y = int(min(max((y+1) / 2 * size, 0), size-1))

        data[x, y] += 1

    data = (255.0 * (data / np.max(data))).astype(np.uint8)

    import matplotlib.pyplot as plt

    plt.figure()
    plt.imshow(data)
    plt.show(block=True)

    print('done')
