from copy import deepcopy
from typing import Tuple, Optional, List, Dict, Set

from planet import Point, Direction, Planet, Position


class SmartDiscovery:
    """To explore the whole planet"""
    def __init__(self, planet: Planet):
        self.planet = planet
        self.paths: Dict[Point, Dict[Direction, bool]] = {}
        self.discovered_points: List[Point] = []

    def has_point_undiscovered_paths(self, point: Point):
        """Returns True, if the point has undiscovered paths."""
        my_point = deepcopy(point)

        if my_point not in self.paths:
            return True

        for direction in self.paths[my_point]:
            if not self.paths[my_point][direction]:
                return True

        return False

    def add_scan_result(self, point: Point, directions: list[Direction]) -> None:
        """Adds the result of a point scan to the internal data structure."""
        my_point = deepcopy(point)
        my_directions = deepcopy(directions)

        if my_point not in self.discovered_points:
            self.discovered_points.append(my_point)

        if my_point not in self.paths:  # Point is new
            self.paths[my_point] = {}
            for direction in my_directions:
                self.paths[my_point][direction] = False
            return

        for direction in my_directions:
            if direction not in self.paths[my_point]:
                self.paths[my_point][direction] = False

    def add_discovered_path(self, start_: Position, end_: Position) -> None:
        """Adds discovered paths to the internal data structure.
        It marks some paths as discovered."""
        start = deepcopy(start_)
        end = deepcopy(end_)
        if start.point not in self.paths:
            self.paths[start.point] = {
                start.direction: True
            }
        else:
            self.paths[start.point][start.direction] = True

        if end.point not in self.paths:
            self.paths[end.point] = {
                end.direction: True
            }
        else:
            self.paths[end.point][end.direction] = True

    def next_direction(self, point: Point) -> Optional[Direction]:
        """Returns the direction of the shortest path to the nearest undiscovered path.
        If everything is discovered, return None."""
        my_point = deepcopy(point)

        if my_point not in self.paths:
            return None

        # undiscovered path at current point
        for direction in self.paths[my_point]:
            if self.paths[my_point][direction]:  # is True -> already discovered
                continue
            self.paths[my_point][direction] = False  # mark discovered
            return direction  # False -> not discovered

        # everything discovered at current point -> path to nearest undiscovered point
        possible_next_ways: List[Tuple[int, Direction]] = []
        for undiscovered_point in self.get_all_points_with_undiscovered_paths():
            path = self.planet.shortest_path_points(my_point, undiscovered_point)
            if path is None or path == []:
                continue
            length = self.planet.length_of_path(path)
            possible_next_ways.append((length, path[0].direction))

        if not possible_next_ways:
            return None

        # sort all paths
        possible_next_ways.sort(key=lambda my_path: my_path[0])

        return possible_next_ways[0][1]

    def mark_discovered(self, point: Point, direction: Direction) -> None:
        """Marks a direction at a point as discovered."""
        my_point = deepcopy(point)
        my_direction = deepcopy(direction)
        if my_point not in self.paths:
            return

        if my_direction not in self.paths[my_point]:
            return

        self.paths[my_point][my_direction] = True
        return

    def is_discovered_point(self, point: Point) -> bool:
        """Checks if a given point is discovered."""
        return point in self.discovered_points

    def get_all_points_with_undiscovered_paths(self) -> Set[Point]:
        """Returns a set ot points with undiscovered paths"""
        points: Set[Point] = set()
        for point in self.paths:
            if point not in self.discovered_points:
                if len(self.paths[point]) != 4:
                    points.add(deepcopy(point))
            for direction in self.paths[point]:
                if self.paths[point][direction]:  # is true -> direction discovered
                    continue
                points.add(deepcopy(point))
        return points
