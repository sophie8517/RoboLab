from typing import Tuple

from planet import Point, Direction, Position, Planet


class DiscoveryComplete(Exception):
    pass




class SmartDiscovery:
    def __init__(self, position: Position, planet: Planet):
        self.position = position
        self.planet_map = planet.get_paths()
        self.planet = planet

        self.undiscovered_paths: list[Position] = []

    def add_possible_directions(self, directions: list[Direction]) -> None:
        for i in range(len(directions)):
            self.undiscovered_paths.append(Position(self.position.point, directions[i]))

    def find_undiscovered_path(self, point: Point) -> list[Direction]:
        directions = [Direction.SOUTH,Direction.NORTH, Direction.WEST, Direction.EAST]
        p =(point.x, point.y)
        keys = list(self.planet[p].keys())
        for k in keys:
            directions.remove(k)

        return directions

    def get_next_direction(self) -> list[Position]:
        #return Direction.NORTH
        # raise DiscoveryComplete("Complete")
        at_point = []
        this_point = (self.position.point.x, self.position.point.y)
        result = []
        found = 0

        for i in self.undiscovered_paths:
            if i.point == self.position.point:
                at_point.append(i.direction)

        un_discovered = self.find_undiscovered_path(self.position.point)


        if un_discovered == []:
            paths_list = []
            for node in list(self.planet.keys()):
                directions = self.find_undiscovered_path(Point(node[0], node[1]))
                if not(directions == []):
                    paths_list.append((node, directions))

            shortest_paths = []
            for elem in paths_list:
                shortest_paths.append(self.planet.shortest_path(this_point, elem[0]))

            shortest_paths_lengths = []
            for i in shortest_paths:
                shortest_paths_lengths.append(len(i))

            min_length = min(shortest_paths_lengths)

            for i in shortest_paths:
                if min_length == len(i):
                    result = shortest_paths[i]
                    found = 1
                    break

        else:
            result = [Position(self.position.point, un_discovered[0])]
            found = 1

        if(found == 0):
            raise DiscoveryComplete("Complete")











