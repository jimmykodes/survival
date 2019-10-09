import random
import settings


class Food:
    def __init__(self):
        # self.x = clamp(random.normalvariate(.5, .25) * settings.WIDTH, 0, settings.WIDTH)
        # self.y = clamp(random.normalvariate(.5, .25) * settings.HEIGHT, 0, settings.HEIGHT)
        self.x = random.random() * settings.WIDTH
        self.y = random.random() * settings.HEIGHT
        self.edible = True
        self.energy = settings.FOOD_ENERGY

    def destroy(self):
        self.edible = False

    def __str__(self):
        return f"Food at ({self.x}, {self.y})"
