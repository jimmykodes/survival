import random
import settings
from utils import clamp


class Food:
    def __init__(self):
        self.x = clamp(random.normalvariate(.5, .28) * settings.WIDTH - 50, 0, settings.WIDTH - 50)
        self.y = clamp(random.normalvariate(.5, .28) * settings.HEIGHT - 50, 0, settings.HEIGHT - 50)
        self.edible = True
        self.energy = settings.FOOD_ENERGY

    def destroy(self):
        self.edible = False

    def __str__(self):
        return f"Food at ({self.x}, {self.y})"
