import colorsys
import math
import multiprocessing
import statistics
import time

import cairo
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from termcolor import cprint

import settings
from blob import Blob
from coord import Coord
from food import Food
from home import Home
from utils import distance


class Simulation:
    def __init__(self, verbose=0, multiprocess=False):
        self.verbose = verbose
        self.food = []
        self.blobs = []
        self.next_blob_index = 0
        self.generate_blobs()
        self.start_time = None
        self.end_time = None
        self.multiprocess = multiprocess

    @property
    def blobs_remaining(self):
        return list(filter(lambda blob: blob.alive, self.blobs))

    @property
    def food_remaining(self):
        return list(filter(lambda f: f.edible, self.food))

    def generate_food(self):
        self.food = [Food() for _ in range(settings.FOOD_COUNT)]

    def generate_blobs(self):
        for i in range(settings.BLOB_COUNT):
            if i + 1 < settings.BLOB_COUNT / 2:
                x = 0 if i + 1 < settings.BLOB_COUNT / 4 else settings.WIDTH
                self.blobs.append(Blob(self.next_blob_index, x=x, verbose=self.verbose))
            else:
                y = 0 if i + 1 < (settings.BLOB_COUNT / 4) * 3 else settings.HEIGHT
                self.blobs.append(Blob(self.next_blob_index, y=y, verbose=self.verbose))
            self.next_blob_index += 1

    def _thread(self, blob, out_queue=None):
        if blob.alive:
            if not isinstance(blob.target, Food) or not isinstance(blob.target, Home):
                v_food = list(filter(lambda f: blob.can_see(f), self.food_remaining))
                if v_food:
                    nearest_food = min(v_food, key=lambda f: distance(f.x, f.y, blob.x, blob.y))
                    blob.target = nearest_food
        blob.update()
        if out_queue:
            out_queue.put(blob)
        return

    def queue_update(self):
        # TODO: figure out how to pass self.food as shared array
        queue = multiprocessing.Queue()
        processes = []
        blobs = []
        for blob in self.blobs:
            p = multiprocessing.Process(target=self._thread, args=(blob, queue))
            processes.append(p)
            p.start()

        for process in processes:
            process.join()
            blobs.append(queue.get())

        for process in processes:
            process.close()

        # while not queue.empty():
        #     blobs.append(queue.get())
        self.blobs = blobs

    def update(self):
        for blob in self.blobs:
            self._thread(blob)

    def add_blob(self, blob):
        if blob.index is None:
            blob.index = self.next_blob_index
            self.next_blob_index += 1
        blob.verbose = self.verbose
        self.blobs.append(blob)

    def day(self):
        for _ in range(settings.DAY_LENGTH):
            if self.multiprocess:
                self.queue_update()
            else:
                self.update()
        new_blobs = []
        for blob in self.blobs_remaining:
            if not blob.returned_home or blob.num_eaten < settings.SURVIVAL_THRESHOLD:
                blob.die(reason='not making it home')
                continue
            elif blob.num_eaten >= settings.REPRODUCTION_THRESHOLD:
                new_blobs.append(blob.reproduce())
            blob.days_alive += 1
            blob.returned_home = False
            blob.num_eaten = 0
            blob.target = Coord()
            blob.energy = settings.INITIAL_ENERGY

        for blob in new_blobs:
            self.add_blob(blob)

    def run(self, days):
        self.start_time = time.time()
        for i in range(days):
            if len(self.blobs_remaining) == 0:
                cprint(f'All blobs died by day {i + 1}', 'red')
                self.end_time = time.time()
                return
            self.generate_food()
            self.day()
            if self.verbose >= 1:
                print(f"Day {i + 1}:")
                print(f"  - Blobs Remaining: {len(self.blobs_remaining)}")
        self.end_time = time.time()

    def stats(self):
        days_alive = [blob.days_alive for blob in self.blobs]
        blob_speed = [blob.speed for blob in self.blobs]
        surviving_blob_speed = [blob.speed for blob in self.blobs_remaining]
        blob_sight_distance = [blob.sight_distance for blob in self.blobs]
        surviving_blob_sight_distance = [blob.sight_distance for blob in self.blobs_remaining]
        print('Simulation Statistics')
        print('=====================')
        cprint(f'{len(self.blobs_remaining)} Blobs survived', 'green')
        print(f'Simulation Run Time: {self.end_time - self.start_time:.2f}')
        print(f'Max days alive: {max(days_alive)}')
        print(f'Average days alive: {statistics.mean(days_alive):.2f}')
        print(f'Max Blob speed: {max(blob_speed):.2f}')
        print(f'Min Blob speed: {min(blob_speed):.2f}')
        if self.blobs_remaining:
            print(f'Average Surviving Blob Speed: {statistics.mean(surviving_blob_speed):.2f}')
        print(f'Max sight_distance: {max(blob_sight_distance):.2f}')
        print(f'Min sight_distance: {min(blob_sight_distance):.2f}')
        if self.blobs_remaining:
            print(f'Average Surviving Blob Sight Distance: {statistics.mean(surviving_blob_sight_distance):.2f}')

    def draw(self):
        with cairo.ImageSurface(cairo.FORMAT_ARGB32, settings.WIDTH, settings.HEIGHT) as surface:
            ctx = cairo.Context(surface)
            ctx.set_source_rgba(0.4, 0.4, 0.4, 1)
            ctx.rectangle(0, 0, settings.WIDTH, settings.HEIGHT)
            ctx.fill()
            ctx.set_source_rgba(37 / 255, 75 / 255, 0, 1)
            for f in self.food:
                ctx.arc(f.x, f.y, 4, 0, math.tau)
                ctx.fill()
            for b in self.blobs:
                ctx.set_source_rgba(*colorsys.hls_to_rgb(b.hue, .5, 1), 1)
                fp = b.coord_hist[0]
                ctx.rectangle(fp.x - 4, fp.y - 4, 8, 8)
                ctx.fill()
                ctx.new_path()
                ctx.set_source_rgba(*colorsys.hls_to_rgb(b.hue, .5, 1), .6)
                ctx.move_to(fp.x, fp.y)
                for p in b.coord_hist:
                    ctx.line_to(p.x, p.y)
                ctx.stroke()
                lp = b.coord_hist[-1]
                if b.alive:
                    ctx.set_source_rgba(*colorsys.hls_to_rgb(b.hue, .5, 1), 1)
                else:
                    ctx.set_source_rgba(0, 0, 0, 1)
                ctx.arc(lp.x, lp.y, 4, 0, math.tau)
                ctx.fill()
            surface.write_to_png('sim.png')
        print(len(self.blobs_remaining), 'blobs survived')

    def plot_energy_hist(self):
        plt.figure(figsize=(10, 10))
        for i, blob in enumerate(self.blobs):
            plt.subplot(settings.BLOB_COUNT, 1, i + 1)
            sns.lineplot(data=pd.DataFrame(data=blob.energy_hist))
        plt.show()
