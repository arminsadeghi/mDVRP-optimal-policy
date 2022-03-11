import numpy as np


class UniformGen:

    def __init__(self, **kwargs):
        try:
            self.min = kwargs['min']
        except KeyError:
            self.min = 0
        try:
            self.max = kwargs['max']
        except KeyError:
            self.max = 1
        try:
            self.seed = kwargs['seed']
        except KeyError:
            self.seed = None
        try:
            self.dim = kwargs['dim']
        except KeyError:
            self.dim = 2

        self.reset()

    def reset(self):
        self.gen = np.random.default_rng(seed=self.seed)

    def draw(self):
        v = []
        for i in range(self.dim):
            v.append(self.gen.uniform(self.min, self.max))
        return v


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
