import numpy as np
import random
from Task import Task


class Generator:

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
        try:
            self.max_time = kwargs['max_time']
        except KeyError:
            self.max_time = None
        try:
            self.initial_tasks = kwargs['initial_tasks']
        except KeyError:
            self.initial_tasks = 0
        try:
            self.total_tasks = kwargs['total_tasks']
        except KeyError:
            self.total_tasks = 1000
        try:
            self.service_time = kwargs['service_time']
        except KeyError:
            self.service_time = 0

        self.reset()

    def reset(self):
        # TODO: Stopgap measure to set global seed here as well since some tasks are still using the random module.
        random.seed(self.seed)
        self.gen = np.random.default_rng(seed=self.seed)

    def draw(self):
        pass

    def draw_tasks(self, lam, field):

        # TODO: Replace calls to expovariate with an appropriate replacement that uses
        #       the internal generator
        first_time = random.expovariate(lam)
        tasks = []

        # insert the initial tasks, available at the start of the sim
        for _ in range(self.initial_tasks):
            location = self.draw()
            for sector in field.sectors:
                if sector.contains(location):
                    sector = sector.id
                    break

            new_task = Task(
                id=len(tasks),
                location=self.draw(),
                sector=sector,
                time=0,
                # TODO: Fixing service time variance proportional to specified time
                service_time=self.gen.normal(self.service_time, 0.1*self.service_time)
            )
            tasks.append(new_task)

        sim_time = first_time
        while True:
            next_time = random.expovariate(lam)
            location = self.draw()
            for sector in field.sectors:
                if sector.contains(location):
                    sector = sector.id
                    break
            new_task = Task(
                id=len(tasks),
                location=location,
                sector=sector,
                time=sim_time,
                # TODO: Fixing service time variance proportional to specified time
                service_time=self.gen.normal(self.service_time, 0.1*self.service_time)
            )
            tasks.append(new_task)
            sim_time += next_time

            if self.max_time is not None:
                if sim_time > self.max_time:
                    break
            else:
                if len(tasks) >= self.total_tasks:
                    break

        return tasks, first_time

    def poisson(self, lam):
        return self.gen.poisson(lam=lam)

    def normal(self, loc, scale):
        return self.gen.normal(loc=loc, scale=scale)

    def is_euclidean(self):
        return True
