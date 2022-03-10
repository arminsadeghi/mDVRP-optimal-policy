from copy import deepcopy
import imp
from sqlite3 import DataError

from matplotlib.pyplot import show
from actor import Actor
from config import *
from random import random, expovariate
from Task import Task
import pygame
from importlib import import_module
from math import sqrt


class Simulation:
    def __init__(self, policy_name, num_actors=1, pois_lambda=0.01, screen=None, service_time=SERVICE_TIME,
                 speed=ACTOR_SPEED, margin=SCREEN_MARGIN, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT,
                 max_time=MAX_SIMULATION_TIME, max_tasks=MAX_SERVICED_TASKS, show_sim=True):
        self.num_actors = num_actors
        self.actor_speed = speed
        self.pois_lambda = pois_lambda
        self.screen = screen
        self._show_sim = show_sim
        if show_sim == True:
            self.sim_time_text = pygame.font.SysFont('dejavuserif', 15)
            self.elapsed_time_text = pygame.font.SysFont('dejavuserif', 10)

        self.service_time = service_time
        self._margin = margin
        self._screen_width = screen_width
        self._env_size = screen_width - self._margin
        self.max_time = max_time
        self.max_tasks = max_tasks

        # load the policy
        self.load_policy(policy_name=policy_name)

        # preload all the the tasks
        self.reset()

    def reset(self, task_list=None):
        self.actor_list = [
            Actor(
                id=i+1,
                pos=[0, 0],
                service_time=self.service_time,
                speed=self.actor_speed,
                screen=self.screen
            ) for i in range(self.num_actors)]

        self.serviced_tasks = []
        self.sim_time = 0
        self.next_time = expovariate(self.pois_lambda)
        self.time_last_arrival = 0
        self.sim_start_time = 0
        self._max_served_time = -1
        self._curr_max_time = -1
        self._avg_served_time = 0
        self._total_travel_distance = 0
        self._max_travel_distance = 0

        self._policy_refresh_required = False

        if task_list is None:
            self._draw_all_tasks(max_time=self.max_time, max_tasks=self.max_tasks)
        else:
            self.task_list = task_list

    def load_policy(self, policy_name):
        # load the policy
        self.policy_name = "{}_policy".format(policy_name)
        policy_mod = import_module('.'+self.policy_name, package='policies')
        self._policy = policy_mod.policy

    def _get_current_max_time(self):
        """get the wait time of unserviced task
        """
        max_time = -1
        for task in self.task_list:
            if task.serviced == True:
                continue
            time = self.sim_time - task.time
            if time > max_time:
                max_time = time
            else:
                # future tasks -- can stop looking
                break
        self._curr_max_time = max_time

    def calculate_sd(self):
        """
        Calculate the standard deviation in wait time across
        all completed tasks
        """
        mean = self._avg_served_time / len(self.serviced_tasks)
        variance = 0
        adjustment = 0
        for task_index in self.serviced_tasks:
            try:
                variance += (self.task_list[task_index].wait_time() - mean) ** 2
            except DataError as e:
                pass  # ignore those tasks that (for whatever reason) haven't completed
                adjustment += 1

        return sqrt(variance / (len(self.serviced_tasks) - adjustment))

    def _draw_all_tasks(self, max_time=None, max_tasks=MAX_SERVICED_TASKS):
        """
        Draw all of the tasks for the simulation according to the defined max time or max serviced tasks
        requested.  Note that we are drawing the time for the next task to be inserted, assuming that we
        are inserting one now.
        """

        self.task_list = []
        sim_time = self.next_time
        while True:
            next_time = expovariate(self.pois_lambda)
            new_task = Task(
                id=len(self.task_list),
                location=[2*random() - 1, 2*random() - 1],
                time=sim_time,
            )
            self.task_list.append(new_task)
            sim_time += next_time

            if max_time is not None:
                if sim_time > max_time:
                    break
            else:
                if len(self.task_list) >= max_tasks:
                    break

        # create an index into the list of tasks
        self.next_task = 0

    ############################################################################
    # Plotting and drawing functions
    ############################################################################

    def _get_location_on_screen(self, location):
        return [
            self._margin + location[0]*(self._env_size)/2.0 + self._env_size/2.0,
            self._margin - location[1]*self._env_size/2.0 + self._env_size/2.0
        ]

    def _draw_rect(self, location, color, size):
        pygame.draw.rect(self.screen,
                         color,
                         (location[0] - size/2.0, location[1] - size/2.0, size, size))

    def _plot_tasks(self):
        """_summary_
        """
        for task in self.task_list[::-1]:

            if task.serviced:
                continue

            task_loc_screen = self._get_location_on_screen(task.location)

            if task.time > self.sim_time:
                b = 40 + int(215.0 * 1.0 / max(1, task.time - self.sim_time))
                g = 0
                r = 0
            else:
                r = 255
                g = 0
                b = 0

            self._draw_rect(
                location=task_loc_screen,
                color=(r, g, b),
                size=10
            )
            elapsed_time_text = self.elapsed_time_text.render(
                str(round(self.sim_time - task.time, 2)), False, (r, g, b))
            self.screen.blit(elapsed_time_text, (task_loc_screen[0] + 20, task_loc_screen[1]))

    def _draw_actor_path(self, actor_index):
        path = self.actor_list[actor_index].path

        actor_loc_screen = self._get_location_on_screen(self.actor_list[actor_index].pos)
        self._draw_rect(
            location=actor_loc_screen,
            color=(255, 255, 255),
            size=20
        )

        for _i in range(len(path) - 1):
            pygame.draw.line(
                self.screen, (255, 255, 255),
                self._get_location_on_screen(path[_i].location),
                self._get_location_on_screen(path[_i+1].location))

        if self.actor_list[actor_index].next_goal != None:
            if path != []:
                pygame.draw.line(
                    self.screen, (255, 255, 255),
                    self._get_location_on_screen(self.actor_list[actor_index].next_goal.location),
                    self._get_location_on_screen(path[0].location))
            pygame.draw.line(
                self.screen, (255, 255, 255),
                self._get_location_on_screen(self.actor_list[actor_index].pos),
                self._get_location_on_screen(self.actor_list[actor_index].next_goal.location))

        if self.actor_list[actor_index].next_goal != None:
            task_loc_screen = self._get_location_on_screen(self.actor_list[actor_index].next_goal.location)
            self._draw_rect(
                location=task_loc_screen,
                color=(0, 255, 0),
                size=10
            )
            elapsed_time_text = self.elapsed_time_text.render(
                str(round(self.sim_time - self.actor_list[actor_index].next_goal.time, 2)), False, (255, 255, 255))
            self.screen.blit(elapsed_time_text, (task_loc_screen[0] + 20, task_loc_screen[1]))

    def _show_sim_info(self):
        try:
            sim_policy_text = self.sim_time_text.render("Current Policy: {}".format(self.policy_name), False, (255, 255, 255))
            self.screen.blit(sim_policy_text, (10, 0))

            # show the simulation time
            sim_time_text = self.sim_time_text.render("Simulation Time:" + str(self.sim_time), False, (255, 255, 255))
            self.screen.blit(sim_time_text, (10, 20))

            num_tasks_serviced_text = self.sim_time_text.render(
                "# serviced tasks: " + str(len(self.serviced_tasks)), False, (255, 255, 255))
            self.screen.blit(num_tasks_serviced_text, (self._screen_width/2.0, 0))

            max_service_time_text = self.sim_time_text.render(
                "max time: " + str(self._max_served_time), False, (255, 255, 255))
            self.screen.blit(max_service_time_text, (self._screen_width/2.0, 20))

            if len(self.serviced_tasks) != 0:
                max_service_time_text = self.sim_time_text.render(
                    "avg time: " + str(self._avg_served_time/len(self.serviced_tasks)), False, (255, 255, 255))
                self.screen.blit(max_service_time_text, (self._screen_width/2.0, 60))

            self._get_current_max_time()
            current_max_service_time_text = self.sim_time_text.render(
                "curr max time: " + str(self._curr_max_time), False, (255, 255, 255))
            self.screen.blit(current_max_service_time_text, (self._screen_width/2.0, 40))
        except Exception as e:
            print("Error in showing simulation info", e)
            pass

    def _show_actor_pos(self, actor_index):
        """show the position of the actor

        Args:
            actor_index (_type_): _description_
        """
        actor = self.actor_list[actor_index]
        sim_time_text = self.sim_time_text.render(
            "Actor {:d} - Pos: ({:03.2f}{:03.2f}) - Dist: {: 5.3f}".format(actor_index + 1, actor.pos[0], actor.pos[1], actor.travel_dist), False, (255, 255, 255))
        self.screen.blit(sim_time_text, (10, 40 + actor_index*20))

    ##################################################################################
    # Simulator step functions
    ##################################################################################

    def _tick_each_actor(self, actor_index):
        """step of simulation for each actor

        Args:
            actor_index (_type_): the index of the actor
        """
        rval = self.actor_list[actor_index].tick(round(self.sim_time, 2))

        if rval == None:
            return

        if rval.id == -1:
            return

        #  set the task to be serviced
        self.task_list[rval.id].serviced = True
        self.task_list[rval.id].time_serviced = self.sim_time
        print("[{:.2f}]: Service done at location {}".format(self.sim_time, rval.location))
        self.serviced_tasks.append(rval.id)

        # record stats
        time = self.sim_time - rval.time
        self._avg_served_time += time
        if time > self._max_served_time:
            self._max_served_time = time

    def tick(self, tick_time, max_simulation_time, max_tasks):
        """[summary]
        """
        if self.screen == None and self._show_sim == True:
            print("[{:.2f}] no screen provided".format(round(self.sim_time, 2)))
            return -1

        if self._policy_refresh_required or (self.next_task < len(self.task_list) and self.sim_time >= self.task_list[self.next_task].time):
            while self.next_task < len(self.task_list) and self.sim_time >= self.task_list[self.next_task].time:
                if self.next_task > len(self.task_list) - 1:
                    break
                print("[{:.2f}]: New task arrived at location {}".format(round(self.sim_time, 2), self.task_list[self.next_task].location))
                self.next_task += 1

            self._policy_refresh_required = self._policy(actors=self.actor_list, tasks=self.task_list[:self.next_task],
                                                         current_time=self.sim_time, service_time=self.service_time)

        if self._show_sim:
            #  draw the limits of the environment
            pygame.draw.rect(self.screen,
                             (255,  255,  255),
                             (self._margin, self._margin, self._env_size, self._env_size), 2)

        # one clock tick for the simulation time
        self.sim_time += tick_time

        if max_simulation_time is not None:
            if self.sim_time > max_simulation_time:
                return -1
        else:
            if len(self.serviced_tasks) >= max_tasks:
                return -1

        if self._show_sim:
            self._plot_tasks()

        self._total_travel_distance = 0
        for actor_index in range(len(self.actor_list)):
            self._tick_each_actor(actor_index)
            self._total_travel_distance += self.actor_list[actor_index].travel_dist
            if self.actor_list[actor_index].travel_dist > self._max_travel_distance:
                self._max_travel_distance = self.actor_list[actor_index].travel_dist

            if self._show_sim:
                self._draw_actor_path(actor_index)
                self._show_actor_pos(actor_index)

        if self._show_sim:
            self._show_sim_info()

        return 1
