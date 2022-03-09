from math import sqrt
from config import DISTANCE_TOLERANCE, TICK_TIME
import pygame
from Task import Task


class Actor:
    def __init__(self, id=0, pos=[0, 0], speed=1.0, service_time=1, screen=None):
        self.id = id
        self.pos = pos
        self.next_goal = None
        self.path = []
        self.speed = speed
        self.reached_goal = False
        self.servicing = False
        self.is_free = True
        self.time_of_service = 0
        self.service_time = service_time
        self.screen = screen
        self.radius = -1
        self.travel_dist = 0

    def _move(self, sim_time):
        """move towards the goal
        """

        # if self.next_goal == None:
        if len(self.path) == 0:
            return

        self.next_goal = self.path[0]

        dir = [
            self.next_goal.location[0] - self.pos[0],
            self.next_goal.location[1] - self.pos[1]
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
                round(self.next_goal.location[0], 5),
                round(self.next_goal.location[1], 5)
            ]
            self.travel_dist += dist

            if (len(self.path) >= 1):
                print("[{:.2f}]: Arrived at service location at {}".format(sim_time, self.next_goal.location))
                self.servicing = True
                self.time_arrived = sim_time
                del self.path[0]

        return

    def tick(self, sim_time):
        """a time step
        """

        finished_task = None

        if (self.servicing == True):
            if (sim_time - self.time_arrived >= self.next_goal.service_time):
                self.servicing = False
                finished_task = self.next_goal
                self.next_goal = None
            else:
                return

        self._move(sim_time)
        return finished_task

    def is_busy(self):
        return self.servicing or len(self.path) > 1
