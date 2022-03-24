import numpy as np
import random
from generators.generator import Generator


class UniformGen(Generator):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def draw(self):
        v = []
        for i in range(self.dim):
            v.append(self.gen.uniform(self.min, self.max))
        return v

    def poisson(self, lam):
        return self.gen.poisson(lam=lam)

    def normal(self, loc, scale):
        return self.gen.normal(loc=loc, scale=scale)


def get_generator_fn():
    return UniformGen


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
