

import numpy as np
import random
from Task import Task
from generators.generator import Generator


class BimodelGaussGen(Generator):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.dists = kwargs['distributions']
        if len(self.dists) != 2:
            raise ValueError("Bad mix of variables -- must be two gaussians!")

        try:
            self.mix = kwargs['mix']
        except KeyError:
            self.mix = 0.5

        self.reset()

    def draw(self):
        v = []
        mix = self.gen.uniform()
        for i in range(self.dim):
            while True:
                if mix < self.mix:
                    n = self.gen.normal(loc=self.dists[0][0], scale=self.dists[0][1])
                else:
                    n = self.gen.normal(loc=self.dists[1][0], scale=self.dists[1][1])
                if n >= self.min and n <= self.max:
                    break
            v.append(n)
        return v

    def test(self):
        size = 100
        points = 50000
        data = np.zeros((size, size))

        self.reset()
        for i in range(points):
            x, y = binomial_generator.draw()
            x = int(min(max((x+1) / 2 * size, 0), size-1))
            y = int(min(max((y+1) / 2 * size, 0), size-1))

            data[x, y] += 1

        data = (255.0 * (data / np.max(data))).astype(np.uint8)

        import matplotlib.pyplot as plt

        plt.figure()
        plt.imshow(data)
        plt.show(block=True)


def get_generator_fn():
    return BimodelGaussGen


if __name__ == '__main__':

    gen_fn = get_generator_fn()
    binomial_generator = gen_fn(
        distributions=[
            [0.5, 0.25],
            [-0.5, 0.25]
        ],
        min=-1,
        max=1,
        dim=2,
        seed=None
    )

    print('done')
