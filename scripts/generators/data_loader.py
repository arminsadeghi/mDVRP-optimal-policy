

import numpy as np
import random
from Task import Task
import pandas as pd

from Field import DataField


class DataLoader():

    def __init__(self, **kwargs):

        self.data_source = kwargs['data_source']

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
            self.max_initial_wait = kwargs['max_initial_wait']
        except KeyError:
            self.max_initial_wait = 0
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

        self.tasks = pd.read_csv(self.data_source)

        distance_df = pd.read_csv(".".join(self.data_source.split('.')[:-2] + ['distances', 'csv']))
        pivot_df = distance_df.pivot(index='SRC_INDEX', columns='DST_INDEX', values='TRAVEL_TIME')
        full_index = pivot_df.index.union(pivot_df.columns)
        self.distances = pivot_df.reindex(labels=full_index, axis=0).reindex(labels=full_index, axis=1).fillna(0.0).to_numpy()

        if len(self.tasks) < 50:
            pivot_df = distance_df.pivot(index='SRC_INDEX', columns='DST_INDEX', values='SCALED_WAYPOINTS')
            full_index = pivot_df.index.union(pivot_df.columns)
            self.paths = pivot_df.reindex(labels=full_index, axis=0).reindex(labels=full_index, axis=1).fillna(0).to_numpy()

            # TODO: LIMITING mapping to less than 50 destinations -- gets pretty busy otherwise...
            for r in range(self.paths.shape[0]):
                for c in range(self.paths.shape[1]):
                    if self.paths[r, c] == 0:
                        self.paths[r, c] = None
                    else:
                        locations = [loc for loc in self.paths[r, c].split(';')]
                        self.paths[r, c] = [[float(x), float(y)] for x, y in [loc.split(':') for loc in locations]]

        self.field = DataField(self.tasks, self.distances)

    def draw(self):
        v = []
        row_index = self.gen.integers(self.field.count, len(self.tasks))
        row = self.tasks.iloc[row_index]
        return row_index, (row['X'], row['Y']), row['CLUSTER']

    def draw_tasks(self, lam, field=None):

        # TODO: Replace calls to expovariate with an appropriate replacement that uses
        #       the internal generator
        first_time = random.expovariate(lam)
        tasks = []

        # insert the initial tasks, available at the start of the sim
        for _ in range(self.initial_tasks):
            task_index, location, sector = self.draw()

            new_task = Task(
                id=len(tasks),
                location=location,
                sector=sector,
                time=self.gen.uniform()*self.max_initial_wait * -1,   # initial tasks are from before clock start
                index=task_index,
                # TODO: Fixing service time variance proportional to specified time
                service_time=self.gen.normal(self.service_time, 0.1*self.service_time)
            )
            tasks.append(new_task)

        sim_time = first_time
        while True:
            next_time = random.expovariate(lam)
            task_index, location, sector = self.draw()
            new_task = Task(
                id=len(tasks),
                location=location,
                sector=sector,
                index=task_index,
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

    def is_euclidean(self):
        return False


def get_generator_fn():
    return DataLoader


if __name__ == '__main__':

    gen_fn = get_generator_fn()
    generator = gen_fn(
        data_source="/home/bjgilhul/Downloads/requetes311_2017-2019.filtered.clustered.csv"
    )

    print('done')
