

import numpy as np
import random
from generators.generator import Generator


class PathologicalGen(Generator):

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

    def reset(self):
        super().reset()
        self.zone_one_count = 0
        self.gen_count = 0

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


def get_generator_fn():
    return PathologicalGen
