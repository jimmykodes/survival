from coord import Coord


class Home(Coord):
    def __str__(self):
        return f"Home at ({self.x}, {self.y})"
