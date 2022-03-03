from actor import Actor
from config import *
from random import random, expovariate
import time
from Task import Task
import pygame
from Policy import base_policy

class Simulation:
    def __init__(self, num_actors =1, pois_lambda = 0.01, screen=None):
        self.num_actors = num_actors
        self.actor_list = [
            Actor(
                id=i+1, 
                pos=[0,0], 
                service_time=SERVICE_TIME,
                speed=ACTOR_SPEED,
                screen=screen
            ) for i in range(num_actors)]

        self.pois_lambda = pois_lambda
        self.task_list=[]
        self.serviced_tasks=[]
        self.sim_time = 0
        self.time_last_arrival = 0
        self.next_time = expovariate(self.pois_lambda)
        self.screen = screen
        self.sim_time_text = pygame.font.SysFont('dejavuserif', 15)
        self.elapsed_time_text = pygame.font.SysFont('dejavuserif', 10)
        self.sim_start_time = 0
        self._margin = MARGIN
        self._env_size =  SCREEN_WIDTH - self._margin


        self._max_served_time = -1
        self._curr_max_time = -1
        self._avg_served_time = 0

    
    def _get_current_max_time(self):
        max_time = -1
        for task in self.task_list:
            time = self.sim_time - task.time
            if time > max_time:
                max_time = time
        
        self._curr_max_time = max_time

    def _draw_task(self):
        print("[{0}] New task arrived!".format(round(self.sim_time, 2)))
        self.next_time = expovariate(self.pois_lambda)
        new_task = Task(
            [2*random() - 1, 2*random() - 1],
            self.sim_time,
        )
        self.task_list.append(new_task)      
        self.time_last_arrival = self.sim_time
        self._assign_new_task(new_task)

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
            (location[0] - size/2.0, location[1]- size/2.0, size, size))

    def  _draw_actor_path(self, actor):
        path = actor.path
        for task in path:
            task_loc_screen = self._get_location_on_screen(task.location)
            self._draw_rect(
                location = task_loc_screen,
                color = (255, 0, 0),
                size=10
            )
            elapsed_time_text = self.elapsed_time_text.render(
            str(round(self.sim_time - task.time, 2)), False, (255, 255, 255))
            self.screen.blit(elapsed_time_text, (task_loc_screen[0] + 20, task_loc_screen[1]))

        for _i in range(len(path) - 1):
            pygame.draw.line(
                self.screen, (255, 255, 255), 
                self._get_location_on_screen(path[_i].location), 
                self._get_location_on_screen(path[_i+1].location))

        if actor.next_goal != None:
            if path != []:
                pygame.draw.line(
                    self.screen, (255, 255, 255), 
                    self._get_location_on_screen(actor.next_goal.location), 
                    self._get_location_on_screen(path[0].location))
            pygame.draw.line(
                self.screen, (255, 255, 255), 
                self._get_location_on_screen(actor.pos), 
                self._get_location_on_screen(actor.next_goal.location))


    def tick(self):
        """[summary]
        """
        if (self.sim_time - self.time_last_arrival > self.next_time):
            self._draw_task()

        pygame.draw.rect(self.screen, 
            (255,  255,  255), 
            (self._margin, self._margin, self._env_size, self._env_size), 2)

        self.sim_time += TICK_TIME

        sim_time_text = self.sim_time_text.render("Simulation Time:" + str(self.sim_time), False, (255, 255, 255))
        self.screen.blit(sim_time_text, (10, 0))
        

        if not(self.screen == None):
            for actor_index in range(len(self.actor_list)):
                actor = self.actor_list[actor_index]

                rval = actor.tick(self.sim_time)

                if rval != None:
                    self.serviced_tasks.append(rval)
                    time = rval.service_time - rval.time
                    self._avg_served_time += time

                    if time > self._max_served_time: 
                        self._max_served_time = time
                    



                sim_time_text = self.sim_time_text.render(
                "Actor " + str(actor_index + 1) + " Pos: " + str(round(actor.pos[0], 2)) + "," \
                    + str(round(actor.pos[1], 2)), False, (255, 255, 255))
                self.screen.blit(sim_time_text, (10, 20 + actor_index*20))

                actor_loc_screen = self._get_location_on_screen(actor.pos)
                self._draw_rect(
                    location = actor_loc_screen,
                    color = (255, 255, 255),
                    size=20
                )

                self._draw_actor_path(actor)

                                  
                
                if actor.next_goal != None:
                    task_loc_screen = self._get_location_on_screen(actor.next_goal.location)
                    self._draw_rect(
                        location = task_loc_screen,
                        color = (0, 255, 0),
                        size=10
                    )
                    elapsed_time_text = self.elapsed_time_text.render(
                    str(round(self.sim_time - actor.next_goal.time, 2)), False, (255, 255, 255))
                    self.screen.blit(elapsed_time_text, (task_loc_screen[0] + 20, task_loc_screen[1]))

            num_tasks_serviced_text = self.sim_time_text.render(
                "# serviced tasks: " + str(len(self.serviced_tasks)), False, (255, 255, 255))
            self.screen.blit(num_tasks_serviced_text, (SCREEN_WIDTH/2.0, 0))


            max_service_time_text = self.sim_time_text.render(
                "max time: " + str(self._max_served_time), False, (255, 255, 255))
            self.screen.blit(max_service_time_text, (SCREEN_WIDTH/2.0, 20))

            self._get_current_max_time()
            current_max_service_time_text = self.sim_time_text.render(
                "curr max time: " + str(self._curr_max_time), False, (255, 255, 255))
            self.screen.blit(current_max_service_time_text, (SCREEN_WIDTH/2.0, 40))
