from math import sqrt, atan2
from config import DISTANCE_TOLERANCE, TICK_TIME
import pygame
from Task import Task, ServiceState


class Actor:
    def __init__(self, id=0, pos=[0, 0], sector=None, depot=[0.5, 0.5], speed=1.0, service_time=1, euclidean=True, screen=None):
        self.id = id
        self.pos = pos
        self.depot = depot
        self.sector = sector
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

    def assign(self, sector, depot=None):
        self.sector = sector
        if depot is None:
            self.depot = self.sector.get_centroid()
        else:
            self.depot = depot

    def distance_to(self, pos):
        dx = self.pos[0] - pos[0]
        dy = self.pos[1] - pos[1]
        return sqrt(dx*dx + dy*dy)

    def near(self, pos, tolerance=DISTANCE_TOLERANCE):
        return self.distance_to(pos) <= tolerance

    def _move(self, sim_time):
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

        if (dist > self.speed*TICK_TIME):
            self.pos = [
                round(self.pos[0] + dir[0]*self.speed*1.0/dist*TICK_TIME, 5),
                round(self.pos[1] + dir[1]*self.speed*1.0/dist*TICK_TIME, 5)
            ]
            self.travel_dist += self.speed * TICK_TIME

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
                self.servicing = self.path.pop(0)
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

            if self.last_task is None:
                last_pos = self.depot
            else:
                last_pos = self.last_task.location

            dir = [
                self.path[0][0].location[0] - last_pos[0],
                self.path[0][0].location[1] - last_pos[1]
            ]

            self.pos = [
                round(last_pos[0] + dir[0]*self.ratio_complete, 5),
                round(last_pos[1] + dir[1]*self.ratio_complete, 5)
            ]

            # moving -- update the orientation
            self.orientation = atan2(dir[1], dir[0])

    def tick(self, sim_time):
        """a time step
        """

        if self.servicing is None:
            if self.euclidean:
                self._move(sim_time)
            else:
                self._travel(sim_time)

        if self.servicing is not None:
            if (sim_time - self.time_arrived >= self.servicing.service_time):
                finished_task = self.servicing
                self.servicing = None
                return finished_task

    def is_busy(self):
        return (self.servicing is not None) or len(self.path) > 1

    def get_depot(self):
        return self.depot
