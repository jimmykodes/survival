import math


def sqr_mag(x1, y1, x2, y2):
    """
    Sqrt is expensive. Just using magnitude for filtering for closest object
    """
    return (x2 - x1) ** 2 + (y2 - y1) ** 2


def distance(x1, y1, x2, y2):
    return math.sqrt(sqr_mag(x1, y1, x2, y2))


def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))
