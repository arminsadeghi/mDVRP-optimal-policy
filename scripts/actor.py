from math import sqrt, atan2
from config import DISTANCE_TOLERANCE
import pygame
from Task import Task, ServiceState
import numpy as np


class Actor:
    def __init__(self, id=0, pos=[0, 0], cluster_id=None, depot=[0.5, 0.5], speed=1.0, service_time=1, path_fn=None, location_fn=None, euclidean=True, screen=None):
        self.id = id
        self.pos = pos
        self.depot = depot
        self.cluster_id = cluster_id
        self.path = []
        self.complete_path = []
        self.speed = speed
        self.reached_goal = False
        self.servicing = None
        self.is_free = True
        self.time_of_service = 0
        self.service_time = service_time
        self.screen = screen
        self.radius = -1
        self.travel_dist = 0
        self.current_goal = None
        self.changes_since_last_completion = 0
        self.max_changes_before_completion = 0
        self.history = []
        self.history.append((0, self.changes_since_last_completion, self.max_changes_before_completion, len(self.path)))
        self.orientation = 0
        self.last_task = None
        self.euclidean = euclidean
        self.path_start_index = None
        self.current_sector = 0

        # variables/state to track position on the current detailed path (in map space)
        self.detailed_path = None
        self.path_fn = path_fn
        self.location_fn = location_fn

    def assign(self, cluster, depot=None):
        self.cluster_id = cluster.id
        if depot is None:
            self.depot = cluster.get_centroid()
        else:
            self.depot = depot

    @staticmethod
    def distance_to(a, b):
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return sqrt(dx*dx + dy*dy)

    def near(self, pos, tolerance=DISTANCE_TOLERANCE):
        return self.distance_to(self.pos, pos) <= tolerance

    def _move(self, sim_time, tick_time):
        """move towards the goal
        """

        if len(self.path) == 0:
            return

        if self.current_goal is None:
            # reset the change count
            self.changes_since_last_completion = 0
            self.current_goal, _ = self.path[0]
            self.history.append((sim_time, self.changes_since_last_completion, self.max_changes_before_completion, len(self.path)))
        else:
            if self.path[0][0] != self.current_goal:
                # target changed -- track it for statistics
                self.current_goal, _ = self.path[0]
                self.changes_since_last_completion += 1
                if self.max_changes_before_completion < self.changes_since_last_completion:
                    self.max_changes_before_completion = self.changes_since_last_completion
                self.history.append((sim_time, self.changes_since_last_completion, self.max_changes_before_completion, len(self.path)))

        dir = [
            self.current_goal.location[0] - self.pos[0],
            self.current_goal.location[1] - self.pos[1]
        ]

        dist = sqrt(
            dir[0]*dir[0] + dir[1]*dir[1]
        )

        if (dist > self.speed*tick_time):
            self.pos = [
                round(self.pos[0] + dir[0]*self.speed*1.0/dist*tick_time, 5),
                round(self.pos[1] + dir[1]*self.speed*1.0/dist*tick_time, 5)
            ]
            self.travel_dist += self.speed * tick_time

            # moving -- update the orientation
            self.orientation = atan2(dir[1], dir[0])

        else:
            # arrived at the goal
            self.pos = [
                round(self.path[0][0].location[0], 5),
                round(self.path[0][0].location[1], 5)
            ]
            self.travel_dist += dist

            self.current_goal = None

            if (len(self.path) >= 1):
                print("[{:.2f}]: Arrived at service location at {}".format(sim_time, self.path[0][0].location))
                self.servicing, _ = self.path.pop(0)
                self.servicing.service_state = ServiceState.IN_SERVICE
                self.time_arrived = sim_time

        return

    def _travel(self, sim_time):
        """
        If the environment is non-euclidean, we can only use expected travel times instead of using distance calculations.
        """
        if len(self.path) == 0:
            return

        if self.current_goal is None:
            self.current_goal, self.travel_time = self.path[0]
            if self.path_fn is not None:
                if self.last_task is None:
                    # use the depot as the src
                    src_idx = self.cluster_id
                else:
                    src_idx = self.last_task.index
                self.detailed_path = self.path_fn(src_idx, self.current_goal.index)
                if self.detailed_path is not None:
                    self.path_distances = []
                    last_pt = self.detailed_path[0]
                    for pt in self.detailed_path[1:]:
                        self.path_distances.append(self.distance_to(pt, last_pt))
                        last_pt = pt
                    self.path_total_distance = sum(self.path_distances)

            self.start_time = sim_time
            self.ratio_complete = 0

        if sim_time - self.start_time >= self.travel_time:
            # arrived at the goal
            self.pos = [
                round(self.path[0][0].location[0], 5),
                round(self.path[0][0].location[1], 5)
            ]
            self.travel_dist += self.travel_time

            try:
                self.last_task, _ = self.path.pop(0)
            except IndexError:
                self.last_task = None

            if (len(self.path)):
                print("[{:.2f}]: Arrived at service location at {}".format(sim_time, self.path[0][0].location))
                self.servicing = self.last_task
                self.servicing.service_state = ServiceState.IN_SERVICE
                self.time_arrived = sim_time

            self.current_goal = None
            self.ratio_complete = 0

        else:
            # still travelling, extrapolate
            self.ratio_complete = (sim_time - self.start_time) / self.travel_time

            if self.detailed_path is not None:
                distance_complete = self.path_total_distance * self.ratio_complete
                distance = 0
                for index, segment_distance in enumerate(self.path_distances):
                    if distance + segment_distance > distance_complete:
                        dir = [
                            self.detailed_path[index+1][0] - self.detailed_path[index][0],
                            self.detailed_path[index+1][1] - self.detailed_path[index][1],
                        ]

                        segment_ratio = (distance_complete - distance) / segment_distance

                        self.pos = [
                            round(self.detailed_path[index][0] + dir[0]*segment_ratio, 5),
                            round(self.detailed_path[index][1] + dir[1]*segment_ratio, 5)
                        ]

                        # moving -- update the orientation
                        self.orientation = atan2(dir[1], dir[0])
                        break
                    distance += segment_distance

    def tick(self, sim_time, tick_time):
        """a time step
        """

        if self.servicing is None:
            if self.euclidean:
                self._move(sim_time, tick_time)
            else:
                self._travel(sim_time)

        if self.servicing is not None:
            if (sim_time - self.time_arrived >= self.servicing.service_time):
                finished_task = self.servicing
                self.servicing = None
                return finished_task

    def is_busy(self):
        return (self.servicing is not None) or len(self.path) > 1

    def get_nearest_location(self):
        return self.location_fn(self.cluster_id, self.pos)

    def get_depot(self):
        return self.depot
