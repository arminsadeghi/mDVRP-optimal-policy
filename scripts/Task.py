from sqlite3 import DataError
from config import SERVICE_TIME
import numpy as np


class Task:
    def __init__(self, id, location, time, service_time=SERVICE_TIME):
        self.id = id
        self.location = location
        self.time = time
        self.serviced = False
        self.time_serviced = -1
        self.service_time = service_time

    def wait_time(self):
        if self.time_serviced == -1:
            raise DataError("Task service not complete!")

        return self.time_serviced - self.time
