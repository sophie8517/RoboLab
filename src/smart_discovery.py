from planet import Point, Direction, Position


class DiscoveryComplete(Exception):
    pass


class SmartDiscovery:
    def __init__(self, position: Position):
        self.position = position

        self.undiscovered_paths: list[Position] = []

    def add_possible_directions(self, directions: list[Direction]) -> None:
        self.undiscovered_paths.append(Position)
        pass

    def get_next_direction(self) -> Direction:
        return Direction.NORTH
        # raise DiscoveryComplete("Complete")


