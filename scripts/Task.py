from config import SERVICE_TIME
import numpy as np
from enum import Enum


class ServiceState(Enum):
    WAITING = 0
    ASSIGNED = 1
    IN_SERVICE = 2
    SERVICED = 3


class Task:
    def __init__(self, id, location, time, initial_wait=0, cluster_id=0, index=None, service_time=SERVICE_TIME):
        self.id = id
        self.location = location
        self.cluster_id = cluster_id
        self.time = time
        self.initial_wait = initial_wait
        self.index = index
        self.service_state = ServiceState.WAITING
        self.time_serviced = -1
        self.service_time = service_time

    def is_pending(self):
        if self.service_state == ServiceState.WAITING or self.service_state == ServiceState.ASSIGNED:
            return True
        return False

    def is_waiting(self):
        if self.service_state == ServiceState.WAITING:
            return True
        return False

    def to_string(self):
        return f'{self.id},{self.location[0]},{self.location[1]},{self.time},{self.time_serviced},{self.initial_wait}'

    def wait_time(self):
        if self.time_serviced == -1:
            raise ValueError("Task service not complete!")

        return self.time_serviced - self.time + self.initial_wait
