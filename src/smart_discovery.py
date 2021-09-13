from typing import Tuple, Optional, List

from planet import Point, Direction, Planet


class SmartDiscovery:
    def __init__(self, planet: Planet):
        self.planet = planet
        self.undiscovered_paths: dict[Point, List[Direction]] = {}

    def add_possible_directions(self, point: Point, directions: list[Direction]) -> None:
        if point not in self.undiscovered_paths:
            self.undiscovered_paths[point] = directions
        else:
            print("Point already discovered -> not adding undiscovered paths")

    def next_direction(self, point: Point) -> Optional[Direction]:
        # undiscovered path at current point
        if point in self.undiscovered_paths:
            direction = self.undiscovered_paths[point][0]
            self.undiscovered_paths[point].remove(direction)
            return direction

        # everything discovered at current point -> path to nearest undiscovered point
        possible_next_ways: List[Tuple[int, Direction]] = []
        for point_with_undiscovered_paths in self.undiscovered_paths.items():
            if not point_with_undiscovered_paths[1]:
                continue  # skip points, where all paths are discovered
            path = self.planet.shortest_path_points(point, point_with_undiscovered_paths[0])
            if path is None:
                continue
            print("Path", path)
            length = self.planet.length_of_path(path)
            print("Length", length)
            possible_next_ways.append((length, path[0].direction))

        if not possible_next_ways:
            return None

        # sort all paths
        possible_next_ways.sort(key=lambda my_path: my_path[0])

        return possible_next_ways[0][1]

    def remove_direction(self, point: Point, direction: Direction) -> None:
        if point not in self.undiscovered_paths:
            print("Cant remove direction of non existing point")
            return

        if direction not in self.undiscovered_paths[point]:
            print("Already not an undiscovered path")
            return

        self.undiscovered_paths[point].remove(direction)

        return
