import random
import uuid

from termcolor import cprint

import settings
from coord import Coord
from food import Food
from home import Home
from utils import distance


class Blob:
    def __init__(self, index=None, x=None, y=None, sight_distance=None, speed=None, verbose=False):
        # Basics
        self.index = index
        self.id = uuid.uuid4()
        self.x = x if x is not None else random.random() * settings.WIDTH
        self.y = y if y is not None else random.random() * settings.HEIGHT
        self.alive = True
        self.returned_home = False
        self.home = Home(self.x, self.y)
        self.num_eaten = 0
        self.verbose = verbose
        self.days_alive = 0

        # Traits
        self.sight_distance = settings.INITIAL_SIGHT_DISTANCE if sight_distance is None else sight_distance
        self.speed = settings.INITIAL_SPEED if speed is None else speed
        self.energy = settings.INITIAL_ENERGY
        self.target = Coord()

        # history (for plotting)
        self.energy_hist = []
        self.coord_hist = []

    @property
    def hue(self):
        return self.index / settings.BLOB_COUNT

    def __str__(self):
        return f"Blob {self.index} at ({self.x}, {self.y})"

    def move(self):
        if isinstance(self.target, Food) and not self.target.edible:
            self.target = Coord()
            if self.verbose >= 2:
                cprint(f'Blob {self.index} was cock blocked', 'red')
        d = distance(self.x, self.y, self.target.x, self.target.y)
        if d > 0:
            r = self.speed / d if d > self.speed else 1
            self.x += (self.target.x - self.x) * r
            self.y += (self.target.y - self.y) * r
            self.energy -= self.speed * 2
        else:
            if isinstance(self.target, Food):
                if self.verbose >= 2:
                    cprint(f'Blob {self.index} eating', 'magenta')
                if self.target.edible:
                    self.eat(self.target)
                else:
                    if self.verbose >= 2:
                        cprint(f'Blob {self.index} was cock blocked', 'red')
                    self.target = Coord()
            if isinstance(self.target, Home):
                if self.verbose >= 2:
                    cprint(f'Blob {self.index} made it home', 'green')
                self.returned_home = True
            else:
                self.target = Coord()

    def eat(self, food):
        self.num_eaten += 1
        self.energy += food.energy
        food.destroy()

    def can_see(self, item):
        return distance(self.x, self.y, item.x, item.y) <= self.sight_distance

    def die(self, reason):
        self.alive = False
        self.energy = 0
        if self.verbose >= 2:
            cprint(f"Blob {self.index} died after {self.days_alive} days from {reason}!", 'yellow')

    def mutate_gene(self, gene):
        if random.random() < settings.MUTATION_CHANCE:
            return gene + (random.random() * settings.MAX_MUTATION * random.choice([1, -1]))
        else:
            return gene

    def reproduce(self):
        if self.verbose >= 2:
            cprint(f'Blob {self.index} reproducing', 'cyan')
        if self.x in [0, settings.WIDTH]:
            c_x = self.x
            c_y = self.y + (random.random() * 3 * random.choice([1, -1]))
        else:
            c_x = self.x + (random.random() * 3 * random.choice([1, -1]))
            c_y = self.y
        return Blob(
            x=c_x,
            y=c_y,
            speed=self.mutate_gene(self.speed),
            sight_distance=self.mutate_gene(self.sight_distance)
        )

    def update(self):
        self.energy_hist.append(self.energy)
        if self.num_eaten == settings.RETURN_HOME_AFTER_EATING:
            self.target = self.home
        elif self.num_eaten > settings.MIN_RETURN_HOME_AFTER_EATING and not isinstance(self.target, Food):
            # check if home is more than our energy minus one turn (a buffer for making it home)
            if distance(self.x, self.y, self.home.x, self.home.y) <= self.energy - self.speed:
                self.target = self.home
        if self.alive and not self.returned_home:
            self.coord_hist.append(Coord(self.x, self.y))
            if self.energy > self.speed:
                self.move()
            else:
                self.die(reason='running out of energy')
