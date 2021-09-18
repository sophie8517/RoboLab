#!/usr/bin/env python3

# Attention: Do not import the ev3dev.ev3 module in this file
from dataclasses import dataclass
from enum import IntEnum, unique
from typing import List, Tuple, Dict, Union, Optional


@unique
class Direction(IntEnum):
    """ Directions in shortcut """
    NORTH = 0
    EAST = 90
    SOUTH = 180
    WEST = 270

    def turned(self):
        """turn 180 degree"""
        return Direction((self + 180) % 360)


@dataclass(unsafe_hash=True)
class Point:
    x: int
    y: int


@dataclass
class Position:
    point: Point
    direction: Direction

    def turned(self):
        return Position(self.point, Direction((self.direction + 180) % 360))


Weight = int
"""
Weight of a given path (received from the server)

Value:  -1 if blocked path
        >0 for all other paths
        never 0
"""


class Planet:
    """
    Contains the representation of the map and provides certain functions to manipulate or extend
    it according to the specifications
    """

    def __init__(self):
        """ Initializes the data structure """
        self.paths: Dict[Tuple[int, int], Dict[Direction, Tuple[Tuple[int, int], Direction, Weight]]] = {}
        self.name = ""

    def add_path(self, start: Tuple[Tuple[int, int], Direction], target: Tuple[Tuple[int, int], Direction],
                 weight: int):
        """
         Adds a bidirectional path defined between the start and end coordinates to the map and assigns the weight to it

        Example:
            add_path(((0, 3), Direction.NORTH), ((0, 3), Direction.WEST), 1)
        :param start: 2-Tuple
        :param target:  2-Tuple
        :param weight: Integer
        :return: void
        """

        # YOUR CODE FOLLOWS (remove pass, please!)
        # add start to target

        start_key = start[0]
        start_value = {start[1]: (target[0], target[1], weight)}

        # if start point already discovered
        if start_key in self.paths.keys():
            self.paths[start_key].update(start_value)
        else:
            self.paths.update({start_key: start_value})

        # -------------------------------------------------------
        # add path from target to start

        target_key = target[0]
        target_value = {target[1]: (start[0], start[1], weight)}

        if target_key in self.paths.keys():
            self.paths[target_key].update(target_value)
        else:
            self.paths.update({target_key: target_value})

    def add_path_points(self, start: Position, end: Position, weight: int):
        """Adds a path with our own data structure."""
        start_tuple = ((start.point.x, start.point.y), start.direction)
        target_tuple = ((end.point.x, end.point.y), end.direction)
        self.add_path(start_tuple, target_tuple, weight)

    def get_paths(self) -> Dict[Tuple[int, int], Dict[Direction, Tuple[Tuple[int, int], Direction, Weight]]]:
        """
        Returns all paths

        Example:
            {
                (0, 3): {
                    Direction.NORTH: ((0, 3), Direction.WEST, 1),
                    Direction.EAST: ((1, 3), Direction.WEST, 2),
                    Direction.WEST: ((0, 3), Direction.NORTH, 1)
                },
                (1, 3): {
                    Direction.WEST: ((0, 3), Direction.EAST, 2),
                    ...
                },
                ...
            }
        :return: Dict
        """

        # YOUR CODE FOLLOWS (remove pass, please!)
        return self.paths

    def shortest_path(self, start: Tuple[int, int], target: Tuple[int, int]) -> Union[
        None, List[Tuple[Tuple[int, int], Direction]]]:
        """
        Returns a shortest path between two nodes

        Examples:
            shortest_path((0,0), (2,2)) returns: [((0, 0), Direction.EAST), ((1, 0), Direction.NORTH)]
            shortest_path((0,0), (1,2)) returns: None
        :param start: 2-Tuple
        :param target: 2-Tuple
        :return: 2-Tuple[List, Direction]
        """

        # YOUR CODE FOLLOWS (remove pass, please!)
        '''If the start or target node (or both) are not in the map,
        then the target is unreachable and None should be returned'''
        if not (start in self.paths.keys()) or not (target in self.paths.keys()):
            return None

        # 'preparation'

        distance_dict = {}  # lists all nodes with their distance to the start node given as parameter
        predecessors = {}  # maps a list of predecessors to a node {this node :[start, ..., this node]}
        unvisited = []  # a list of unvisited nodes
        infinity = float("inf")

        '''All nodes listed as keys in self.paths are initially added to unvisited.
        The distances of all nodes are initialized with infinty, but the start node has distance 0.
        The predecessors of all nodes are initialized with an empty list.'''

        for k in list(self.paths.keys()):
            unvisited.append(k)
            distance_dict.update({k: infinity})
            predecessors.update({k: []})

        distance_dict[start] = 0

        # ------ end of preparation ----------------
        # the algorithm goes as long as the target node wasn't visited

        while target in unvisited:
            recent_node = start  # start is randomly chosen,just to initialize the variable recent_node
            distances = []  # a list that will contain the distances of all keys from distance_dict

            # distance of every unvisited node is appended to distances
            # we want to ignore the visited nodes, because there is no shorter distance for them
            for node in unvisited:
                distances.append(distance_dict[node])  # create a list of all distances

            minimum_distance = min(distances)

            if minimum_distance == infinity:
                return None  # because this node is unreachable
            else:
                for node in unvisited:
                    if distance_dict[node] == minimum_distance:
                        recent_node = node
                        break
                        # choose the first occurence of a node with the minimum distance as the next node to work with
            # remove because the currently visited node is the recent_node
            unvisited.remove(recent_node)

            for k in list(self.paths[recent_node].values()):
                # the k[0]'s are the neighbors of the recent node
                # don't ignore the neighbors when we haven't visited this node and when the path is free
                if k[0] in unvisited and not (
                        k[2] == -1):

                    old_weight = distance_dict[k[0]]
                    weights = []
                    '''if there is more than 1 edge between the k[0] node and recent node:
                            add the weight of every edge between these 2 nodes to weights
                            choose the minimum of weights as the weight you work with
                                    and save it in part'''
                    for ky in self.paths[recent_node].values():
                        if ky[0] == k[0] and ky[2] > 0:
                            weights.append(ky[2])
                    part = min(weights)

                    # calculates the distance if you 'go over' the recent node
                    new_weight = distance_dict[recent_node] + part

                    '''if the new found path to k[0] over recent node is shorter
                       -> update distance value in distance_dict
                       -> update predecessors of k[0] node: set it to predecessrs of the recent node and
                                                            append the recent node'''
                    if new_weight < old_weight:
                        distance_dict[k[0]] = new_weight
                        predecessors[k[0]] = predecessors[recent_node] + [recent_node]

        # write output

        node_list = predecessors[target]  # predecessors of the target node
        output = []
        for num in range(len(node_list)):
            #to catch the node before the target node
            if num == len(node_list) - 1:
                last = node_list[len(node_list) - 1]

                '''add the direction and weight of every edge between last and target to direcs,
                don't add the weight of a blocked path'''
                direcs = []
                for kye in list(self.paths[last].keys()):
                    if self.paths[last][kye][0] == target and self.paths[last][kye][2] > 0:
                        direction = kye
                        path_weight = self.paths[last][kye][2]
                        direcs.append((direction, path_weight))

                #set mini to the path weight of the first element in direcs
                mini = direcs[0][1]
                last_elem = (last, direcs[0][0])
                #find the direction where the weight is minimal
                for i in direcs:
                    if i[1] < mini:
                        last_elem = (last, i[0])

                output.append(last_elem)

            else:
                direcs = []
                for key in self.paths[node_list[num]].keys():
                    if self.paths[node_list[num]][key][0] == node_list[num + 1] and self.paths[node_list[num]][key][2] > 0:
                        dire = key
                        path_weight = self.paths[node_list[num]][key][2]
                        direcs.append((dire, path_weight))
                element = (node_list[num], direcs[0][0])
                mini = direcs[0][1]
                for i in direcs:
                    if i[1] < mini:
                        element = (node_list[num], i[0])

                output.append(element)

        return output

    def shortest_path_points(self, start: Point, end: Point) -> Optional[List[Position]]:
        """
        Shortest path with our own data structure.
        return None if there is no path
        return []   if there is start and end is the same???
        """
        way_points = self.shortest_path((start.x, start.y), (end.x, end.y))
        if way_points is None:
            return None

        position_list: List[Position] = []
        for way_point in way_points:
            point = Point(way_point[0][0], way_point[0][1])
            position_list.append(Position(point, way_point[1]))

        return position_list

    def length_of_path(self, path: List[Position]) -> int:
        """Returns the length of a path"""
        length = 0
        for position in path:
            if self.paths[(position.point.x, position.point.y)][position.direction][2] == -1:
                return -1
            else:
                length += self.paths[(position.point.x, position.point.y)][position.direction][2]
        return length

    def is_blocked(self, position: Position):
        """Checks if a path is blocked"""
        point_tuple = (position.point.x, position.point.y)
        if point_tuple not in self.paths:
            return False

        if position.direction not in self.paths[point_tuple]:
            return False

        if self.paths[point_tuple][position.direction][2] != -1:
            return False

        return True
