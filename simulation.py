import colorsys
import math
import multiprocessing
import os
import statistics
import time

import cairo
from termcolor import cprint

import settings
from blob import Blob
from coord import Coord
from food import Food
from home import Home
from utils import sqr_mag


class Simulation:
    def __init__(self, verbose=0, draw=False, multiprocess=False):
        self.verbose = verbose
        self.food = []
        self.blobs = []
        self.next_blob_index = 0
        self.generate_blobs()
        self.start_time = None
        self.end_time = None
        self.multiprocess = multiprocess
        self.draw = draw

    @property
    def blobs_remaining(self):
        return filter(lambda blob: blob.alive, self.blobs)

    @property
    def food_remaining(self):
        return filter(lambda f: f.edible, self.food)

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
                nearest = min(self.food_remaining, key=lambda f: sqr_mag(f.x, f.y, blob.x, blob.y))
                if blob.can_see(nearest):
                    blob.target = nearest
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

    def day(self, day_number):
        for _ in range(settings.DAY_LENGTH):
            if self.multiprocess:
                self.queue_update()
            else:
                self.update()
        if self.draw:
            self.draw_day(day_number)
        for b in self.blobs:
            b.coord_hist = []
        new_blobs = []
        for blob in self.blobs_remaining:
            if not blob.returned_home or blob.num_eaten < settings.SURVIVAL_THRESHOLD:
                blob.die(reason='not making it home', color='yellow')
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
            if len(list(self.blobs_remaining)) == 0:
                cprint(f'All blobs died by day {i + 1}', 'red')
                self.end_time = time.time()
                return
            self.generate_food()
            self.day(i)
            if self.verbose >= 1:
                print(f"Day {i + 1}:")
                print(f"  - Blobs Remaining: {len(list(self.blobs_remaining))}")
        self.end_time = time.time()

    def stats(self, run_number):
        days_alive = [blob.days_alive for blob in self.blobs]
        blob_speed = [blob.speed for blob in self.blobs]
        surviving_blob_speed = [blob.speed for blob in self.blobs_remaining]
        blob_sight_distance = [blob.sight_distance for blob in self.blobs]
        surviving_blob_sight_distance = [blob.sight_distance for blob in self.blobs_remaining]
        if run_number is None:
            print('Simulation Statistics')
            print('=====================')
            cprint(f'{len(list(self.blobs_remaining))} Blobs survived', 'green')
            print(f'Simulation Run Time: {self.end_time - self.start_time:.2f}')
            print()
            print('Starting Blob Statistics')
            print('========================')
            print(f'Speed: {settings.INITIAL_SPEED}')
            print(f'Sight Distance: {settings.INITIAL_SIGHT_DISTANCE}')
            print()
            print('Overall Blob Statistics')
            print('=======================')
            print(f'Max days alive: {max(days_alive)}')
            print(f'Max speed: {max(blob_speed):.2f}')
            print(f'Min speed: {min(blob_speed):.2f}')
            print(f'Max sight_distance: {max(blob_sight_distance):.2f}')
            print(f'Min sight_distance: {min(blob_sight_distance):.2f}')
            print()
            print('Surviving Blob Statistics')
            print('=========================')
            if self.blobs_remaining:
                print(f'Oldest Surviving Blob: {max(self.blobs_remaining, key=lambda b: b.days_alive).days_alive}')
                print(f'Max speed: {max(surviving_blob_speed):.2f}')
                print(f'Min speed: {min(surviving_blob_speed):.2f}')
                print(f'Average speed: {statistics.mean(surviving_blob_speed):.2f}')
                print(f'Max sight_distance: {max(surviving_blob_sight_distance):.2f}')
                print(f'Min sight_distance: {min(surviving_blob_sight_distance):.2f}')
                print(f'Average sight_distance: {statistics.mean(surviving_blob_sight_distance):.2f}')
        else:
            data = f'''
            Simulation Statistics
            =====================
            {len(list(self.blobs_remaining))} Blobs survived
            Simulation Run Time: {self.end_time - self.start_time:.2f}
            
            Starting Blob Statistics
            ========================
            Speed: {settings.INITIAL_SPEED}
            Sight Distance: {settings.INITIAL_SIGHT_DISTANCE}

            Overall Blob Statistics
            =======================
            Max days alive: {max(days_alive)}
            Max speed: {max(blob_speed):.2f}
            Min speed: {min(blob_speed):.2f}
            Max sight_distance: {max(blob_sight_distance):.2f}
            Min sight_distance: {min(blob_sight_distance):.2f}
            '''
            if self.blobs_remaining:
                data += f'''
                Surviving Blob Statistics
                =========================
                Oldest Surviving Blob: {max(self.blobs_remaining, key=lambda b: b.days_alive).days_alive}
                Max speed: {max(surviving_blob_speed):.2f}
                Min speed: {min(surviving_blob_speed):.2f}
                Average speed: {statistics.mean(surviving_blob_speed):.2f}
                Max sight_distance: {max(surviving_blob_sight_distance):.2f}
                Min sight_distance: {min(surviving_blob_sight_distance):.2f}
                Average sight_distance: {statistics.mean(surviving_blob_sight_distance):.2f}
                '''
            with open(f'run_number_{run_number}.txt', 'w+') as f:
                f.write(data)

    def draw_day(self, day_number):
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
                if not b.coord_hist:
                    continue
                ctx.set_source_rgba(*colorsys.hls_to_rgb(b.hue, .5, 1), .6)
                ctx.move_to(b.coord_hist[0].x, b.coord_hist[0].y)
                for p in b.coord_hist:
                    ctx.line_to(p.x, p.y)
                ctx.stroke()
            surface.write_to_png(os.path.join(settings.IMAGE_DIR, f'day_number_{day_number}.png'))
