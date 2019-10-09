import math


def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))
