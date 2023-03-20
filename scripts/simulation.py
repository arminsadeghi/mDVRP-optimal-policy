from copy import deepcopy

from matplotlib.pyplot import show
from actor import Actor
from config import *
from random import random, expovariate, seed
from Task import Task, ServiceState
import pygame
from importlib import import_module
from math import sqrt, exp
import numpy as np

from Field import Field, Sector
import colorsys


class Simulation:
    def __init__(self, policy_name, policy_args=None, generator_name='uniform', generator_args=None, num_actors=1, pois_lambda=0.01, screen=None, service_time=SERVICE_TIME,
                 speed=ACTOR_SPEED, margin=SCREEN_MARGIN, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT,
                 max_time=MAX_SIMULATION_TIME, max_tasks=MAX_SERVICED_TASKS, record_data=False, centralized=False, delivery_log=None):
        self.actor_speed = speed
        self.pois_lambda = pois_lambda
        self.screen = screen
        self.record_data = record_data
        if screen is not None or record_data:
            self.sim_time_text = pygame.font.SysFont('dejavuserif', 15)
            self.elapsed_time_text = pygame.font.SysFont('dejavuserif', 10)
            self.status_font = pygame.font.SysFont('roboto', STATUS_FONT_SIZE)

        self.service_time = service_time
        self._xmargin = margin * 0.5
        self._ymargin = margin * 0.5
        self._screen_width = screen_width
        self._env_size = screen_width - margin
        self._border_offset = 10
        self.max_time = max_time
        self.max_tasks = max_tasks

        self.delivery_log = delivery_log

        # load the draw method
        self.load_generator(generator_name=generator_name, generator_args=generator_args)

        self.centralized = centralized
        if generator_args['data_source'] is None:
            self.num_actors = num_actors
            self.field = None
        else:
            self.field = self.generator.field

            self.num_clusters = self.field.count
            self.num_actors = self.field.count

        # art objects
        self.actor_image = pygame.image.load('assets/car.svg')
        self.actor_image = pygame.transform.scale(self.actor_image, (ACTOR_IMAGE_SIZE, ACTOR_IMAGE_SIZE))

        # load the policy
        self.load_policy(policy_name=policy_name, policy_args=policy_args)

        # preload all the the tasks
        self.reset()

    def reset(self, task_list=None):

        self.actor_list = []
        for i in range(self.num_actors):
            if self.field is None:
                pos = [0.5, 0.5]
                depot = pos
                cluster_id = 0
            else:
                cluster_id = i
                pos = self.field.clusters[cluster_id].get_centroid()
                depot = pos

            self.actor_list.append(Actor(
                id=i+1,
                pos=pos,
                cluster_id=cluster_id,
                depot=depot,
                service_time=self.service_time,
                speed=self.actor_speed,
                euclidean=self.generator.is_euclidean(),
                screen=self.screen,
                path_fn=self.get_detailed_path,
                location_fn=self.get_nearest_location
            ))

        self.serviced_tasks = []
        self.sim_time = 0.
        self.next_time = 0.
        self.time_last_arrival = 0.
        self.sim_start_time = 0.
        self._max_served_time = -1
        self._curr_max_time = -1
        self._avg_served_time = 0.0
        self._total_travel_distance = 0
        self._max_travel_distance = 0
        self._max_queue_length = 0
        self.ticks = 0

        # reset the random number generator
        self.generator.reset()

        if task_list is None:
            self._draw_all_tasks()
        else:
            self.task_list = task_list

        self.rho = round(self.service_time * self.pois_lambda, 2)

    def load_policy(self, policy_name, policy_args):
        # load the policy
        self.policy_args = policy_args
        self.policy_name = "{}_policy".format(policy_name)
        policy_mod = import_module('.'+self.policy_name, package='policies')
        self._policy = policy_mod.get_policy(args=policy_args)

    def load_generator(self, generator_name, generator_args):
        # load the generator
        self.generator_name = generator_name
        self.generator_args = generator_args
        gen_mod = import_module('.'+self.generator_name, package='generators')
        generator_fn = gen_mod.get_generator_fn()
        self.generator = generator_fn(**self.generator_args)

    def get_detailed_path(self, start_index, end_index):
        if self.generator is None:
            return None
        return self.generator.get_detailed_path(start_index=start_index, end_index=end_index)

    def get_nearest_location(self, cluster_id, location):
        return self.generator.get_nearest_location(cluster_id, *location)

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

    def calculate_variance(self):
        """
        Calculate the variance in wait time across
        all completed tasks
        """
        if not len(self.serviced_tasks):
            return 0.0

        mean = self._avg_served_time / len(self.serviced_tasks)
        variance = 0
        for task_index in self.serviced_tasks:
            variance += (self.task_list[task_index].wait_time() - mean) ** 2

        return variance / (len(self.serviced_tasks))

    def calculate_sd(self):
        """
        Calculate the standard deviation in wait time across
        all completed tasks
        """
        return sqrt(self.calculate_variance())

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
            self._xmargin + location[0]*self._env_size,
            self._ymargin + self._env_size - location[1]*self._env_size
        ]

    def _draw_rect(self, location, color, size):
        pygame.draw.rect(self.screen,
                         color,
                         (location[0] - size/2.0, location[1] - size/2.0, size, size))

    def _draw_task(self, location, color, size, outlines=False):
        if not outlines:
            pygame.draw.circle(self.screen,
                               color,
                               (location[0], location[1]), size, 0)
        else:
            pygame.draw.circle(self.screen,
                               SCREEN_OUTLINE_COLOUR,
                               (location[0], location[1]), size, 2)

    # Quick image rotation
    #   https://stackoverflow.com/questions/4183208/how-do-i-rotate-an-image-around-its-center-using-pygame
    @staticmethod
    def blitRotateCenter(surf, image, topleft, angle):
        rotated_image = pygame.transform.rotate(image, np.rad2deg(angle))
        new_rect = rotated_image.get_rect(center=image.get_rect(topleft=topleft).center)
        surf.blit(rotated_image, new_rect)

    def _draw_actor(self, actor):
        x = self._xmargin + actor.pos[0]*self._env_size - ACTOR_IMAGE_SIZE//2
        y = self._ymargin + self._env_size - actor.pos[1]*self._env_size - ACTOR_IMAGE_SIZE//2
        Simulation.blitRotateCenter(surf=self.screen, image=self.actor_image, topleft=(x, y), angle=actor.orientation)

    def _plot_tasks(self):
        """_summary_
        """

        INITIAL_TASK_SIZE = 10

        max_lateness = 2000.0
        for task in self.task_list[::-1]:

            if task.service_state is ServiceState.SERVICED:
                continue

            if task.time <= self.sim_time:
                task_loc_screen = self._get_location_on_screen(task.location)
                lateness = min(max_lateness, self.sim_time - task.time + task.initial_wait)

                hue = 120.0/360.0 * (max_lateness - lateness) / max_lateness
                r, g, b = colorsys.hls_to_rgb(h=hue, l=0.5, s=0.99)
                r = int(r * 255)
                g = int(g * 255)
                b = int(b * 255)
                a = 50

                self._draw_task(
                    location=task_loc_screen,
                    color=(r, g, b, a),
                    size=INITIAL_TASK_SIZE + sqrt(lateness),
                    outlines=False
                )

        # TODO: transparancy isn't working for me -- workaround
        for task in self.task_list[::-1]:
            if task.service_state is ServiceState.SERVICED:
                continue

            if task.time <= self.sim_time:
                lateness = min(max_lateness, self.sim_time - task.time + task.initial_wait)

                task_loc_screen = self._get_location_on_screen(task.location)
                self._draw_task(
                    location=task_loc_screen,
                    color=(r, g, b, a),
                    size=INITIAL_TASK_SIZE + sqrt(lateness),
                    outlines=True
                )

    def _draw_status(self):

        if not len(self.serviced_tasks):
            avg = 0
        else:
            avg = self._avg_served_time/len(self.serviced_tasks)
        total_str = f'Serviced: {len(self.serviced_tasks)}'
        avg_str = f"Average Wait: {avg:5.2f}"
        # var_str = f"Variance: {self.calculate_variance():5.2f}"
        var_str = f"Max Wait: {self._max_served_time:5.2f}"

        text_width, text_height = self.status_font.size(avg_str)

        x_avg_offset = self._env_size + self._xmargin - text_width - STATUS_XMARGIN*2
        y_avg_offset = self._env_size + self._ymargin - text_height * 3 - STATUS_YMARGIN*4

        pygame.draw.rect(self.screen,
                         SCREEN_BACKGROUND_COLOUR,
                         (x_avg_offset-STATUS_XMARGIN, y_avg_offset-STATUS_YMARGIN, text_width + STATUS_XMARGIN*2, text_height * 3 + STATUS_YMARGIN * 3), 0)
        pygame.draw.rect(self.screen,
                         SCREEN_OUTLINE_COLOUR,
                         (x_avg_offset-STATUS_XMARGIN, y_avg_offset-STATUS_YMARGIN, text_width + STATUS_XMARGIN*2, text_height * 3 + STATUS_YMARGIN * 3), 2)

        text = self.status_font.render(total_str, False, STATUS_FONT_COLOUR)
        self.screen.blit(text, (x_avg_offset+STATUS_XMARGIN/3, y_avg_offset))
        text = self.status_font.render(avg_str, False, STATUS_FONT_COLOUR)
        self.screen.blit(text, (x_avg_offset+STATUS_XMARGIN/3, y_avg_offset+text_height+STATUS_YMARGIN*0.8))
        text = self.status_font.render(var_str, False, STATUS_FONT_COLOUR)
        self.screen.blit(text, (x_avg_offset+STATUS_XMARGIN/3, y_avg_offset+text_height*2+STATUS_YMARGIN*1.6))

    def _draw_actor_depot(self, actor):
        pos = self._get_location_on_screen(actor.depot)

        pygame.draw.rect(self.screen,
                         DEPOT_BACKGROUND_COLOUR,
                         (pos[0]-DEPOT_SIZE//2, pos[1]-DEPOT_SIZE//2, DEPOT_SIZE, DEPOT_SIZE), 0)
        pygame.draw.rect(self.screen,
                         DEPOT_OUTLINE_COLOUR,
                         (pos[0]-DEPOT_SIZE//2, pos[1]-DEPOT_SIZE//2, DEPOT_SIZE, DEPOT_SIZE), 0)

    def _draw_actor_path(self, actor):
        path = actor.path
        actor_loc_screen = self._get_location_on_screen(actor.pos)

        if len(actor.complete_path) > 1:
            pygame.draw.line(
                self.screen, ACTOR_COMPLETE_PATH_COLOUR,
                actor_loc_screen,
                self._get_location_on_screen(actor.complete_path[0].location), ACTOR_PATH_WIDTH)

            last_task = actor.complete_path[0]
            for task in actor.complete_path[1:-1]:
                pygame.draw.line(
                    self.screen, ACTOR_COMPLETE_PATH_COLOUR,
                    self._get_location_on_screen(last_task.location),
                    self._get_location_on_screen(task.location), ACTOR_PATH_WIDTH)
                last_task = task

        #     # draw the complete path of the actor by looking up the waypoints and stuff -- always starting from
        #     # the actor's depot
        #     try:
        #         path = []
        #         last_index = actor.path_start_index
        #         if last_index is not None:
        #             for task in actor.complete_path:
        #                 leg = self.generator.paths[last_index, task.index]
        #                 if leg is not None:
        #                     for point in leg:
        #                         path.append(self._get_location_on_screen(point))
        #                 path.append(self._get_location_on_screen(task.location))
        #                 last_index = task.index

        #         if len(path) > 2:
        #             pygame.draw.lines(self.screen, color=ACTOR_PATH_COLOUR, closed=False, points=path, width=ACTOR_PATH_WIDTH)

        #     except AttributeError:
        #         # probably no data for intersections in the database -- ignore it all
        #         pass

        if len(path) > 1:
            pygame.draw.line(
                self.screen, ACTOR_PATH_COLOUR,
                actor_loc_screen,
                self._get_location_on_screen(actor.path[0][0].location), ACTOR_PATH_WIDTH)

            last_task = actor.path[0][0]
            for task, _ in actor.path[1:-1]:
                if task.id < 0:
                    continue
                pygame.draw.line(
                    self.screen, ACTOR_PATH_COLOUR,
                    self._get_location_on_screen(last_task.location),
                    self._get_location_on_screen(task.location), ACTOR_PATH_WIDTH)
                last_task = task

    def _draw_all_roads(self):
        try:
            paths = self.generator.paths
        except AttributeError:
            return  # Nothing to draw

        for path_set in paths:
            for path in path_set:
                if path is None:
                    continue
                screen_path = []
                for point in path:
                    screen_path.append(self._get_location_on_screen(point))
                pygame.draw.lines(self.screen, BACKGROUND_PATH_COLOUR, closed=False, points=screen_path, width=BACKGROUND_PATH_WIDTH)

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
        # sim_time_text = self.sim_time_text.render(
        #     "Actor {:d} - Pos: ({:03.2f}{:03.2f}) - Dist: {: 5.3f}".format(actor_index + 1, actor.pos[0], actor.pos[1], actor.travel_dist), False, (255, 255, 255))
        # self.screen.blit(sim_time_text, (10, 40 + actor_index*20))

    def plot_initial_conditions(self):

        import matplotlib.pyplot as plt
        import matplotlib.path as mpath
        import matplotlib.patches as mpatches

        # width as measured in inkscape
        width = 8  # 3.487
        height = width / 1.5

        plt.rc('font', family='serif', serif='Times')
        plt.rc('text', usetex=True)
        plt.rc('xtick', labelsize=12)
        plt.rc('ytick', labelsize=12)
        plt.rc('axes', labelsize=12)

        scale = 1000.0

        fig, ax = plt.subplots()
        ax.set_xlim((-20, scale+100))
        ax.set_ylim((-20, scale+100))
        ax.axis('off')
        ax.axis('equal')

        edge_colour = [c/255.0 for c in BACKGROUND_PATH_COLOUR]

        self._draw_all_roads()
        try:
            paths = self.generator.paths
            for path_set in paths:
                for path in path_set:
                    if path is None:
                        continue
                    screen_path = [(path[0][0]*scale, path[0][1]*scale)]
                    screen_codes = [mpath.Path.MOVETO]
                    for point in path[1:]:
                        screen_path.append((point[0]*scale, point[1]*scale))
                        screen_codes.append(mpath.Path.LINETO)

                    screen_path = mpath.Path(screen_path, screen_codes)
                    patch = mpatches.PathPatch(screen_path, edgecolor=edge_colour, facecolor='none', lw=BACKGROUND_PATH_WIDTH)
                    ax.add_patch(patch)
        except AttributeError:
            pass

        # self._plot_tasks()
        INITIAL_TASK_SIZE = 10
        max_lateness = 600.0
        for task in self.task_list[::-1]:

            if task.service_state is ServiceState.SERVICED:
                continue

            if task.time <= self.sim_time:
                lateness = min(max_lateness, self.sim_time - task.time)

                hue = 120.0/360.0 * (max_lateness - lateness) / max_lateness
                r, g, b = colorsys.hls_to_rgb(h=hue, l=0.5, s=0.99)

                circle = mpatches.Circle((task.location[0]*scale, task.location[1]*scale), INITIAL_TASK_SIZE +
                                         sqrt(lateness) * 2, ec=(0, 0, 0, 0.5), fc=(r, g, b, 0.5))
                ax.add_patch(circle)

        for actor in self.actor_list:
            try:

                # self._draw_actor_path(actor)
                if len(actor.complete_path) > 1:

                    # draw the complete path of the actor by looking up the waypoints and stuff -- always starting from
                    # the actor's depot
                    screen_path = []
                    screen_codes = []

                    edge_colour = [c/255.0 for c in ACTOR_PATH_COLOUR]

                    last_index = actor.path_start_index
                    if last_index is not None:
                        for task in actor.complete_path:
                            leg = self.generator.paths[last_index, task.index]
                            if leg is not None:
                                for point in leg:
                                    screen_path.append((point[0]*scale, point[1]*scale))
                                    screen_codes.append(mpath.Path.LINETO)
                            last_index = task.index

                        screen_codes[0] = mpath.Path.MOVETO

                    if len(screen_path):
                        screen_path = mpath.Path(screen_path, screen_codes)
                        patch = mpatches.PathPatch(screen_path, facecolor='none', edgecolor=edge_colour, lw=ACTOR_PATH_WIDTH)
                        ax.add_patch(patch)
            except AttributeError:
                pass
            except IndexError:
                pass  # trying to draw a road that isn't in the sample set

            # self._draw_actor_depot(actor)
            edge_colour = [c/255.0 for c in DEPOT_OUTLINE_COLOUR]
            face_colour = [c/255.0 for c in DEPOT_BACKGROUND_COLOUR]
            rect = mpatches.Rectangle((actor.depot[0]*scale-DEPOT_SIZE//2, actor.depot[1]*scale-DEPOT_SIZE//2),
                                      width=DEPOT_SIZE, height=DEPOT_SIZE, ec=edge_colour, fc=face_colour)
            ax.add_patch(rect)

            # self._draw_actor(actor)

        fig.set_size_inches(width, height)
        fig.savefig(f'initial_conditions.pdf')

        plt.show(block=True)

    ##################################################################################
    # Simulator step functions
    ##################################################################################

    def _tick_each_actor(self, actor_index, tick_time):
        """step of simulation for each actor

        Args:
            actor_index (_type_): the index of the actor
        """
        rval = self.actor_list[actor_index].tick(round(self.sim_time, 2), tick_time)

        if rval == None:
            # TODO: Removing this for now -- skipping the time means the clock gets out of sync
            #       when comparing multiple runs
            #
            # # TODO: SKIP CLOCK FORWARD BECAUSE WE ASSUME ONLY ONE AGENT
            # #       skip forward in time -- we're not doing anything until this service is complete
            # if self.actor_list[actor_index].servicing is not None:
            #     time_ticks = int(self.actor_list[actor_index].servicing.service_time / tick_time)
            #     self.sim_time += time_ticks * tick_time
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
        time = rval.wait_time()
        self._avg_served_time += time
        if time > self._max_served_time:
            self._max_served_time = time

        # track update
        if self.delivery_log is not None:
            self.delivery_log.write(self.task_list[rval.id].to_string()+'\n')
            self.delivery_log.flush()

    def tick(self, tick_time, max_simulation_time, max_tasks):
        """[summary]
        """

        # one clock tick for the simulation time
        self.sim_time += tick_time
        self.ticks += 1

        if max_simulation_time is not None:
            if self.sim_time > max_simulation_time:
                return -1
        else:
            if len(self.serviced_tasks) >= max_tasks:
                return -1

        # update the current pending task count
        while self.next_task < len(self.task_list) and self.sim_time >= self.task_list[self.next_task].time:
            if self.next_task > len(self.task_list) - 1:
                break
            print("[{:.2f}]: New task arrived at location {}".format(round(self.sim_time, 2), self.task_list[self.next_task].location))
            self.next_task += 1

        # TODO: The selection of the next policy, and the target of the Actor(s) should really be in the policy, not here in
        #       the simulation code.
        for actor in self.actor_list:

            # # TODO: HACK for DC Batch -- shortcut for everything else -- will break things if continous planning is required -- should
            # #       make this an auto-detect option
            # if actor.is_busy():
            #     continue

            cluster_tasks = []
            for task in self.task_list:
                if self.sim_time < task.time:
                    break

                if not task.is_pending():
                    continue

                if self.field is None or actor.cluster_id == task.cluster_id:
                    cluster_tasks.append(task)

            if len(cluster_tasks):
                # print("[{:.2f}]: Currently {} tasks pending for cluster {}".format(round(self.sim_time, 2), len(cluster_tasks), actor.cluster_id))
                self._policy(actor=actor, tasks=cluster_tasks, field=self.field, current_time=self.sim_time)

        self._total_travel_distance = 0
        for actor_index in range(len(self.actor_list)):
            self._tick_each_actor(actor_index, tick_time)
            self._total_travel_distance += self.actor_list[actor_index].travel_dist
            if self.actor_list[actor_index].travel_dist > self._max_travel_distance:
                self._max_travel_distance = self.actor_list[actor_index].travel_dist

        for actor in self.actor_list:
            if len(actor.path) > self._max_queue_length:
                self._max_queue_length = len(actor.path)

        if self.screen is not None:
            #  draw the limits of the environment
            self.screen.fill(SCREEN_BACKGROUND_COLOUR)

            # draw the map if there is one
            self._draw_all_roads()

            self._plot_tasks()

            #  draw the limits of the environment
            pygame.draw.rect(self.screen,
                             SCREEN_OUTLINE_COLOUR,
                             (self._xmargin-self._border_offset,
                              self._ymargin-self._border_offset,
                              self._env_size+self._border_offset*2,
                              self._env_size+self._border_offset*2), 2)

            # bar_cube_size = 20
            # num_waiting = self.next_task - len(self.serviced_tasks)
            # pygame.draw.rect(self.screen,
            #                  (255,  0,  0),
            #                  (self._xmargin-self._border_offset-1.5*bar_cube_size, self._ymargin-self._border_offset + self._env_size+self._border_offset*2 - num_waiting * bar_cube_size, bar_cube_size, bar_cube_size*num_waiting), 0)

            for actor in self.actor_list:
                self._draw_actor_path(actor)
                self._draw_actor_depot(actor)
                self._draw_actor(actor)

            self._draw_status()

            if self.sim_time == tick_time:
                self.plot_initial_conditions()

            if self.record_data:
                eta_str = str(self.policy_args['eta']) + ('ef' if self.policy_args['eta_first'] else 'e')
                pygame.image.save(
                    self.screen, f"images/screen_{self.policy_name}_{self.policy_args['sectors']}s_{eta_str}_{self.policy_args['cost_exponent']}p_{self.pois_lambda}l_{self.ticks:06d}.png")

        # if self._show_sim:
        #     self._show_sim_info()

        return 1
