from config import SERVICE_TIME
import numpy as np
from enum import Enum


class ServiceState(Enum):
    WAITING = 0
    ASSIGNED = 1
    IN_SERVICE = 2
    SERVICED = 3


class Task:
    def __init__(self, id, location, time, service_time=SERVICE_TIME):
        self.id = id
        self.location = location
        self.time = time
        self.service_state = ServiceState.WAITING
        self.time_serviced = -1
        self.service_time = service_time

    def is_pending(self):
        if self.service_state == ServiceState.WAITING or self.service_state == ServiceState.ASSIGNED:
            return True
        return False

    def wait_time(self):
        if self.time_serviced == -1:
            raise DataError("Task service not complete!")

        return self.time_serviced - self.time
