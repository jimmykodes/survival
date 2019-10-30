import random

import settings
from utils import clamp


class Coord:
    def __init__(self, x=None, y=None):
        self.x = x if x is not None else clamp(random.normalvariate(.5, .25) * settings.WIDTH, 0, settings.WIDTH)
        self.y = y if y is not None else clamp(random.normalvariate(.5, .25) * settings.HEIGHT, 0, settings.HEIGHT)

    def __str__(self):
        return f"Coord at ({self.x}, {self.y})"
