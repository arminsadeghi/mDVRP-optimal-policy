from math import sqrt
from config import DISTANCE_TOLERANCE, TICK_TIME
import pygame
from Task import Task, ServiceState


class Actor:
    def __init__(self, id=0, pos=[0, 0], speed=1.0, service_time=1, screen=None):
        self.id = id
        self.pos = pos
        self.path = []
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

    def distance_to(self, pos):
        dx = self.pos[0] - pos[0]
        dy = self.pos[1] - pos[1]
        return sqrt(dx*dx + dy*dy)

    def _move(self, sim_time):
        """move towards the goal
        """

        if len(self.path) == 0:
            return

        if self.current_goal is None:
            # reset the change count
            self.changes_since_last_completion = 0
            self.current_goal = self.path[0]
            self.history.append((sim_time, self.changes_since_last_completion, self.max_changes_before_completion, len(self.path)))
        else:
            if self.path[0] != self.current_goal:
                # target changed -- track it for statistics
                self.current_goal = self.path[0]
                self.changes_since_last_completion += 1
                if self.max_changes_before_completion < self.changes_since_last_completion:
                    self.max_changes_before_completion = self.changes_since_last_completion
                self.history.append((sim_time, self.changes_since_last_completion, self.max_changes_before_completion, len(self.path)))

        dir = [
            self.path[0].location[0] - self.pos[0],
            self.path[0].location[1] - self.pos[1]
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
        else:
            # arrived at the goal
            self.pos = [
                round(self.path[0].location[0], 5),
                round(self.path[0].location[1], 5)
            ]
            self.travel_dist += dist

            self.current_goal = None

            if (len(self.path) >= 1):
                print("[{:.2f}]: Arrived at service location at {}".format(sim_time, self.path[0].location))
                self.servicing = self.path.pop(0)
                self.servicing.service_state = ServiceState.IN_SERVICE
                self.time_arrived = sim_time

        return

    def tick(self, sim_time):
        """a time step
        """

        if self.servicing is None:
            self._move(sim_time)

        if self.servicing is not None:
            if (sim_time - self.time_arrived >= self.servicing.service_time):
                finished_task = self.servicing
                self.servicing = None
                return finished_task

    def is_busy(self):
        return (self.servicing is not None) or len(self.path) > 1
