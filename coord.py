import random

import settings


class Coord:
    def __init__(self, x=None, y=None):
        self.x = x if x is not None else random.random() * settings.WIDTH
        self.y = y if y is not None else random.random() * settings.HEIGHT

    def __str__(self):
        return f"Coord at ({self.x}, {self.y})"
