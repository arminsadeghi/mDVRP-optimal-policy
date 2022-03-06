import imp

from matplotlib.pyplot import show
from actor import Actor
from config import *
from random import random, expovariate, seed
from Task import Task
import pygame
from importlib import import_module

seed(10)


class Simulation:
    def __init__(self, policy_name, num_actors=1, pois_lambda=0.01, screen=None, service_time=SERVICE_TIME,
                 speed=ACTOR_SPEED, margin=SCREEN_MARGIN, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT,
                 show_sim=True):
        self.num_actors = num_actors
        self.actor_list = [
            Actor(
                id=i+1,
                pos=[0, 0],
                service_time=service_time,
                speed=speed,
                screen=screen
            ) for i in range(num_actors)]

        self.pois_lambda = pois_lambda
        self.task_list = []
        self.serviced_tasks = []
        self.sim_time = 0
        self.time_last_arrival = 0
        self.next_time = expovariate(self.pois_lambda)
        self.screen = screen
        self._show_sim = show_sim
        if show_sim == True:
            self.sim_time_text = pygame.font.SysFont('dejavuserif', 15)
            self.elapsed_time_text = pygame.font.SysFont('dejavuserif', 10)

        self.sim_start_time = 0
        self.service_time = service_time
        self._margin = margin
        self._screen_width = screen_width
        self._env_size = screen_width - self._margin

        # load the policy
        self.policy_name = "{}_policy".format(policy_name)
        policy_mod = import_module('.'+self.policy_name, package='policies')
        self._policy = policy_mod.policy

        self._max_served_time = -1
        self._curr_max_time = -1
        self._avg_served_time = 0

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
        self._curr_max_time = max_time

    def _draw_task(self):
        """draw the task according to Poisson arrival process
        """
        self.next_time = expovariate(self.pois_lambda)
        new_task = Task(
            id=len(self.task_list),
            location=[2*random() - 1, 2*random() - 1],
            time=self.sim_time,
        )
        self.task_list.append(new_task)
        self.time_last_arrival = self.sim_time

        print("[{:.2f}]: New task arrived at location {}".format(round(self.sim_time, 2), new_task.location))

    def _assign_new_task(self, new_task):
        """[summary]

        Args:
            new_task ([type]): [description]
        """
        self.actor_list[0].path.append(new_task)

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
        for task in self.task_list:

            if task.serviced == True:
                continue

            task_loc_screen = self._get_location_on_screen(task.location)
            self._draw_rect(
                location=task_loc_screen,
                color=(255, 0, 0),
                size=10
            )
            elapsed_time_text = self.elapsed_time_text.render(
                str(round(self.sim_time - task.time, 2)), False, (255, 255, 255))
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

        self.serviced_tasks.append(rval.id)
        time = rval.service_time - rval.time
        self._avg_served_time += time

        if time > self._max_served_time:
            self._max_served_time = time

        self._avg_served_time += time

        #  set the task to be serviced
        self.task_list[rval.id].serviced = True
        print("[{:.2f}]: Service done at location {}".format(self.sim_time, rval.location))

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
        except:
            print("Error in showing simulation info")
            pass

    def _show_actor_pos(self, actor_index):
        """show the position of the actor

        Args:
            actor_index (_type_): _description_
        """
        actor = self.actor_list[actor_index]
        sim_time_text = self.sim_time_text.render(
            "Actor " + str(actor_index + 1) + " Pos: " + str(round(actor.pos[0], 2)) + ","
            + str(round(actor.pos[1], 2)), False, (255, 255, 255))
        self.screen.blit(sim_time_text, (10, 40 + actor_index*20))

    def tick(self, tick_time, max_simulation_time):
        """[summary]
        """
        if (self.sim_time - self.time_last_arrival > self.next_time):
            self._draw_task()
            self.actor_list = self._policy(self.actor_list, self.task_list, self.sim_time, self.service_time)

        if self._show_sim == True:
            #  draw the limits of the environment
            pygame.draw.rect(self.screen,
                             (255,  255,  255),
                             (self._margin, self._margin, self._env_size, self._env_size), 2)

        # one clock tick for the simulation time
        self.sim_time += tick_time

        # if self.sim_time > MAX_SIMULATION_TIME:
        #     return -1

        if len(self.serviced_tasks) >= MAX_SERVICED_TASKS:
            return -1

        if self._show_sim:
            self._plot_tasks()

        if self.screen == None and self._show_sim == True:
            print("[{:.2f}] no screen provided".format(round(self.sim_time, 2)))
            return

        for actor_index in range(len(self.actor_list)):
            self._tick_each_actor(actor_index)
            if self._show_sim == True:
                self._draw_actor_path(actor_index)
                self._show_actor_pos(actor_index)

        if self._show_sim:
            self._show_sim_info()

        return 1
