

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
        try:
            self.centralized = kwargs['centralized']
        except KeyError:
            self.centralized = False

        self.reset()

    def reassign_sectors(self):
        # divide the space into equal angles
        angles = np.linspace(0, 2*np.pi, self.sectors + 1)[:-1]
        inc = 2 * np.pi / 2000

        def calc_lines(angles):
            lines = []
            sx = self.tasks.iloc[0]['LOC_LONG']
            sy = self.tasks.iloc[0]['LOC_LAT']
            for i in range(len(angles)):
                ex = sx + np.cos(angles[i]) * 0.025
                ey = sy + np.sin(angles[i]) * 0.025
                lines.append(((sx, sy), (ex, ey)))
            return lines

        lines = calc_lines(angles=angles)

        # Positive if left, neg if right
        def side(line, px, py):
            v1, v2 = line
            return (v2[0] - v1[0]) * (py - v1[1]) - (px - v1[0]) * (v2[1] - v1[1])

        def calc_sector(lines, px, py):
            for i in range(len(lines)):
                next = (i + 1) % len(lines)
                if side(lines[i], px, py) >= 0 and side(lines[next], px, py) < 0:
                    return i

        while True:
            self.tasks['CLUSTER'] = [calc_sector(lines, px=x, py=y) for x, y in zip(self.tasks['LOC_LONG'], self.tasks['LOC_LAT'])]
            counts = self.tasks['CLUSTER'].value_counts()
            largest = counts.index[0]
            smallest = counts.index[-1]
            print(counts, largest, smallest)
            if counts[largest] - counts[smallest] <= max(1, len(self.tasks) * 0.01):
                break

            sign = -1
            for a in range(self.sectors):
                candidate = int((largest + a + 1) % self.sectors)
                angles[candidate] += sign * inc
                if candidate == smallest:
                    sign = 1

            lines = calc_lines(angles)

    def reset(self):
        # TODO: Stopgap measure to set global seed here as well since some tasks are still using the random module.
        random.seed(self.seed)
        self.gen = np.random.default_rng(seed=self.seed)

        self.tasks = pd.read_csv(self.data_source)

        # if self.centralized and self.sectors > 1:
        #     self.reassign_sectors()

        self.distance_df = pd.read_csv(".".join(self.data_source.split('.')[:-2] + ['distances', 'csv']))
        pivot_df = self.distance_df.pivot(index='SRC_INDEX', columns='DST_INDEX', values='TRAVEL_TIME')
        full_index = pivot_df.index.union(pivot_df.columns)
        self.distances = pivot_df.reindex(labels=full_index, axis=0).reindex(labels=full_index, axis=1).fillna(0.0).to_numpy()
        self.mean_distance = self.distance_df['TRAVEL_TIME'].mean()

        # get random set of streets for visual
        df_sampled = self.distance_df.sample(250)
        pivot_df = df_sampled.pivot(index='SRC_INDEX', columns='DST_INDEX', values='SCALED_WAYPOINTS')
        full_index = pivot_df.index.union(pivot_df.columns)
        self.paths = pivot_df.reindex(labels=full_index, axis=0).reindex(labels=full_index, axis=1).fillna(0).to_numpy()

        for r in range(self.paths.shape[0]):
            for c in range(self.paths.shape[1]):
                if self.paths[r, c] == 0:
                    self.paths[r, c] = None
                else:
                    locations = [loc for loc in self.paths[r, c].split(';')]
                    self.paths[r, c] = [[float(x), float(y)] for x, y in [loc.split(':') for loc in locations]]

        self.field = DataField(self.tasks, self.distances, self.centralized)

    def draw(self):
        v = []
        row_index = self.gen.integers(self.field.count, len(self.tasks))
        row = self.tasks.iloc[row_index]
        return row_index, (row['X'], row['Y']), row['CLUSTER']

    def draw_tasks(self, lam):

        # TODO: Replace calls to expovariate with an appropriate replacement that uses
        #       the internal generator
        first_time = random.expovariate(lam)
        tasks = []

        # insert the initial tasks, available at the start of the sim
        for _ in range(self.initial_tasks):
            task_index, location, cluster_id = self.draw()

            new_task = Task(
                id=len(tasks),
                location=location,
                cluster_id=cluster_id,
                time=0,
                initial_wait=self.gen.uniform()*self.max_initial_wait,
                index=task_index,
                service_time=self.gen.normal(self.service_time, 0.3*self.service_time)
            )
            tasks.append(new_task)

        sim_time = first_time
        while True:
            next_time = random.expovariate(lam)
            task_index, location, cluster_id = self.draw()
            new_task = Task(
                id=len(tasks),
                location=location,
                cluster_id=cluster_id,
                time=sim_time,
                initial_wait=0,  # no latent time -- self.gen.uniform()*self.max_initial_wait,
                index=task_index,
                # TODO: Fixing service time variance proportional to specified time -- note using 0.3 to allow a little more variation
                #       given the longer service times expected in the 'real' data case
                service_time=self.gen.normal(self.service_time, 0.3*self.service_time)
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

    def get_detailed_path(self, start_index, end_index):
        if start_index == end_index:
            return None
        waypoints = self.distance_df.loc[(self.distance_df['SRC_INDEX'] == start_index) & (
            self.distance_df['DST_INDEX'] == end_index)]['SCALED_WAYPOINTS'].values[0]
        locations = [loc for loc in waypoints.split(';')]
        return [[float(x), float(y)] for x, y in [loc.split(':') for loc in locations]]

    def get_nearest_location(self, cluster, x, y):
        closest_row = None
        closest_index = None
        closest_dist = np.inf
        local_tasks = self.tasks.loc[self.tasks['CLUSTER']==cluster]
        for index, row in local_tasks.iterrows():
            dx = x - row['X']
            dy = y - row['Y']
            dist = dx * dx + dy * dy
            if dist < closest_dist:
                closest_dist = dist
                closest_row = row
                closest_index = index
        return closest_index, [closest_row['X'], closest_row['Y']]


def get_generator_fn():
    return DataLoader


if __name__ == '__main__':

    gen_fn = get_generator_fn()
    generator = gen_fn(
        data_source="/home/bjgilhul/Downloads/requetes311_2017-2019.filtered.clustered.csv"
    )

    print('done')
