from copy import deepcopy
import imp
from sqlite3 import DataError

from matplotlib.pyplot import show
from actor import Actor
from config import *
from random import random, expovariate, seed
from Task import Task, ServiceState
import pygame
from importlib import import_module
from math import sqrt

from centroid import Field, Sector


class Simulation:
    def __init__(self, policy_name, policy_args=None, generator_name='uniform', generator_args=None, num_actors=1, pois_lambda=0.01, screen=None, service_time=SERVICE_TIME,
                 speed=ACTOR_SPEED, margin=SCREEN_MARGIN, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT,
                 max_time=MAX_SIMULATION_TIME, max_tasks=MAX_SERVICED_TASKS, show_sim=True, sectors=1, delivery_log=None):
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

        self.delivery_log = delivery_log

        # split the environment...
        self.vertices = [[0, 0], [1, 0], [1, 1], [0, 1]]
        self.centre = [0.5, 0.5]
        self.sectors = sectors
        self.field = Field(self.vertices, self.centre, self.sectors)
        self.current_sector = self.field.next_sector()

        # load the draw method
        self.load_generator(generator_name=generator_name, generator_args=generator_args)

        # load the policy
        self.load_policy(policy_name=policy_name, policy_args=policy_args)

        # preload all the the tasks
        self.reset()

    def reset(self, task_list=None):
        self.actor_list = [
            Actor(
                id=i+1,
                pos=[0.5, 0.5],
                service_time=self.service_time,
                speed=self.actor_speed,
                screen=self.screen
            ) for i in range(self.num_actors)]

        self.serviced_tasks = []
        self.sim_time = 0
        self.next_time = 0
        self.time_last_arrival = 0
        self.sim_start_time = 0
        self._max_served_time = -1
        self._curr_max_time = -1
        self._avg_served_time = 0
        self._total_travel_distance = 0
        self._max_travel_distance = 0
        self._max_queue_length = 0

        # reset the random number generator
        self.generator.reset()

        if task_list is None:
            self._draw_all_tasks()
        else:
            self.task_list = task_list

    def load_policy(self, policy_name, policy_args):
        # load the policy
        self.policy_name = "{}_policy".format(policy_name)
        policy_mod = import_module('.'+self.policy_name, package='policies')
        self._policy = policy_mod.policy
        if policy_args is not None:
            try:
                self.cost_exponent = policy_args['cost_exponent']
            except KeyError:
                self.cost_exponent = 1
            try:
                self.eta = policy_args['eta']
            except KeyError:
                self.eta = 1
            try:
                self.eta_first = policy_args['eta_first']
            except KeyError:
                self.eta = False
            try:
                self.gamma = policy_args['gamma']
            except KeyError:
                self.gamma = 1

    def load_generator(self, generator_name, generator_args):
        # load the generator
        self.generator_name = generator_name
        self.generator_args = generator_args
        gen_mod = import_module('.'+self.generator_name, package='generators')
        generator_fn = gen_mod.get_generator_fn()
        self.generator = generator_fn(**self.generator_args)

    def _get_current_max_time(self):
        """get the wait time of unserviced task
        """
        max_time = -1
        for task in self.task_list:
            if task.service_state is not ServiceState.SERVICED:
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

    def _draw_all_tasks(self):
        """
        Draw all of the tasks for the simulation according to the defined max time or max serviced tasks
        requested.  Note that we are drawing the time for the next task to be inserted, assuming that we
        are inserting one now.
        """

        self.task_list, self.next_time = self.generator.draw_tasks(self.pois_lambda)
        # create an index into the list of tasks
        self.next_task = 0

    ############################################################################
    # Plotting and drawing functions
    ############################################################################

    def _get_location_on_screen(self, location):
        return [
            self._margin + location[0]*self._env_size,
            self._margin + self._env_size - location[1]*self._env_size
        ]

    def _draw_rect(self, location, color, size):
        pygame.draw.rect(self.screen,
                         color,
                         (location[0] - size/2.0, location[1] - size/2.0, size, size))

    def _plot_tasks(self):
        """_summary_
        """
        for task in self.task_list[::-1]:

            if task.service_state is ServiceState.SERVICED:
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

        if len(self.actor_list[actor_index].path):
            pygame.draw.line(
                self.screen, (255, 255, 255),
                self._get_location_on_screen(self.actor_list[actor_index].pos),
                self._get_location_on_screen(self.actor_list[actor_index].path[0].location))

            if self.actor_list[actor_index].path[0].id != -1:
                task_loc_screen = self._get_location_on_screen(self.actor_list[actor_index].path[0].location)
                self._draw_rect(
                    location=task_loc_screen,
                    color=(0, 255, 0),
                    size=10
                )
                elapsed_time_text = self.elapsed_time_text.render(
                    str(round(self.sim_time - self.actor_list[actor_index].path[0].time, 2)), False, (255, 255, 255))
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

        if self.task_list[rval.id].service_state == ServiceState.SERVICED:
            raise ValueError("Double trouble -- Task already serviced!")

        #  set the task to be serviced
        self.task_list[rval.id].service_state = ServiceState.SERVICED
        self.task_list[rval.id].time_serviced = self.sim_time
        print("[{:.2f}]: Service done at location {}".format(self.sim_time, rval.location))
        self.serviced_tasks.append(rval.id)

        # record stats
        time = self.sim_time - rval.time
        self._avg_served_time += time
        if time > self._max_served_time:
            self._max_served_time = time

        # track update
        if self.delivery_log is not None:
            self.delivery_log.write(self.task_list[rval.id].to_string()+'\n')
            self.delivery_log.flush()

        # if the actor is now idle, move to the next sector
        if not self.actor_list[0].is_busy():
            self.current_sector = self.field.next_sector()

    def tick(self, tick_time, max_simulation_time, max_tasks):
        """[summary]
        """
        if self.screen == None and self._show_sim == True:
            print("[{:.2f}] no screen provided".format(round(self.sim_time, 2)))
            return -1

        # one clock tick for the simulation time
        self.sim_time += tick_time

        if max_simulation_time is not None:
            if self.sim_time > max_simulation_time:
                return -1
        else:
            if len(self.serviced_tasks) >= max_tasks:
                return -1

        # if the actor is idle
        if not self.actor_list[0].is_busy():

            # check if we need to update the actor's target
            if self.current_sector.is_near_centre(self.actor_list[0].pos):
                self.current_sector = self.field.next_sector()

            sector_tasks = []
            # go through the task list and assign tasks (this is going to be the slow way...)
            for _ in range(self.sectors):
                for task in self.task_list:
                    if self.sim_time < task.time:
                        break

                    if task.is_pending():
                        if self.current_sector.is_mine(task.location):
                            sector_tasks.append(task)

                if len(sector_tasks):
                    print("[{:.2f}]: Currently {} tasks pending for sector {}".format(round(self.sim_time, 2), len(sector_tasks), self.current_sector.id))
                    break

                # nothing in this sector, check the next
                self.current_sector = self.field.next_sector()

            if len(sector_tasks):
                self._policy(actors=self.actor_list, tasks=sector_tasks, current_time=self.sim_time, service_time=self.service_time,
                             cost_exponent=self.cost_exponent, eta=self.eta, eta_first=self.eta_first, gamma=self.gamma)
            else:
                target = self.centre  # self.current_sector.get_centroid()
                self.actor_list[0].path = [Task(-1, target, -1)]

        if self._show_sim:
            #  draw the limits of the environment
            pygame.draw.rect(self.screen,
                             (255,  255,  255),
                             (self._margin, self._margin, self._env_size, self._env_size), 2)

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

        for actor in self.actor_list:
            if len(actor.path) > self._max_queue_length:
                self._max_queue_length = len(actor.path)

        if self._show_sim:
            self._show_sim_info()

        return 1
