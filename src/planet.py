#!/usr/bin/env python3

# Attention: Do not import the ev3dev.ev3 module in this file
from dataclasses import dataclass
from enum import IntEnum, unique
from typing import List, Tuple, Dict, Union


@unique
class Direction(IntEnum):
    """ Directions in shortcut """
    NORTH = 0
    EAST = 90
    SOUTH = 180
    WEST = 270


@dataclass
class Point:
    x: int
    y: int


@dataclass
class Position:
    point: Point
    direction: Direction

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
        self.paths = {}

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
        #add start to target

        start_key = start[0]
        start_value = {start[1]: (target[0], target[1], weight)}

        if start_key in self.paths.keys():
            self.paths[start_key].update(start_value)
        else:
            self.paths.update({start_key:start_value})

        #add path from target to start

        target_key = target[0]
        target_value = {target[1]:(start[0], start[1], weight)}

        if target_key in self.paths.keys():
            self.paths[target_key].update(target_value)
        else:
            self.paths.update({target_key:target_value})





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

    def shortest_path(self, start: Tuple[int, int], target: Tuple[int, int]) -> Union[None, List[Tuple[Tuple[int, int], Direction]]]:
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
        if not(start in self.paths.keys()) or not(target in self.paths.keys()):
            return None

        '''
        distance_dict = {}
        unvisited = []
        paths = {}
        #{node:[node after, ... , recently added]}
        found_nodes = [start]

        for k in self.paths.keys():
            distance_dict.update({k: float("inf")})
            unvisited.append(k)
            paths.update({k:[]})
        distance_dict[start] = 0

        recent_node = start
        #---------------------------------------

        while target in unvisited:
            distance_unvisited = []
            for k in unvisited:
                distance_unvisited.append(k)

            minimum_distance = min(distance_unvisited)


            for k in unvisited:
                if distance_dict[k] == minimum_distance:
                    recent_node = k
                    unvisited.remove(k)
                    break

            neighbors = []
            for val in self.paths[recent_node].keys():
                elem = self.paths[recent_node][val][0]
                neighbors.append(elem)

            neighbors_copy = neighbors

            for nc in neighbors_copy:
                for k in self.paths[recent_node].values():
                    if k[2] == -1:
                        neighbors.remove(nc)
                    else:
                        if not (nc in found_nodes):
                            found_nodes.append(nc)

            for n in neighbors:
                part = 0
                for k in self.paths[recent_node].values():
                    if k[0] == n:
                        part = k[2]
                new_length = part + distance_dict[recent_node]
                old_length = distance_dict[n]
                if new_length < old_length:
                    # update distance for node n
                    # update paths list for node n
                    distance_dict[n] = new_length
                    new_paths = paths[recent_node] + [recent_node]
                    paths.update({n: new_paths})

        # write output
        node_list = paths[target]
        output = []
        for node in len(node_list):
            dire = Direction.WEST
            for key in self.paths[node_list[node]].keys():
                if self.paths[node_list[node]][key][0] == node_list[node + 1]:
                    dire = key
                    break
            element = (node,dire)
            output.append(element)

        return output
        '''

        distance_dict = {} # lists all nodes with their distance to start node
        predecessors = {} # maps a list of predecessors to a node {this node :[start, ..., this node}
        unvisited = []
        infinity = float("inf")

        #add all nodes to unvisited
        #initialize all distances with infinity
        #initialize predecessors as empty list

        for k in list(self.paths.keys()):
            unvisited.append(k)
            distance_dict.update({k: infinity})
            predecessors.update({k: []})

        #start node has distance 0
        distance_dict[start] = 0

        while target in unvisited:
            recent_node = start
            distances = []

            for node in unvisited:
                distances.append(distance_dict[node])  #create a list of all distances

            minimum_distance = min(distances)

            if minimum_distance == infinity:
                return None  #because this node is unreacheable
            else:
                for node in unvisited:
                    if distance_dict[node] == minimum_distance:
                        recent_node = node
                        break
                        #choose the node with the minimum distance as the next node to work with
            unvisited.remove(recent_node)


            for k in list(self.paths[recent_node].values()):
                if k[0] in unvisited:  # k[0] is target node, the k[0]'s are the neighbors of the recent node

                    old_weight = distance_dict[k[0]]
                    new_weight = 0
                    part = 0
                    for ky in self.paths[recent_node].values():
                        if ky[0] == k[0]:
                            part = k[2]
                    new_weight = distance_dict[recent_node] + part  #calculates the distance if you 'go over'
                                                                    # the recent node

                    if new_weight < old_weight:
                        # update predecessors and distance_dict
                        distance_dict[k[0]] = new_weight
                        predecessors[k[0]] = predecessors[recent_node] + [recent_node]

        #write output

        node_list = predecessors[target]  # predecessors of the target node
        output = []
        for num in range(len(node_list)):
            if num == len(node_list) - 1:
                last = node_list[len(node_list) - 1]  # node before target node
                direc = Direction.NORTH
                for kye in list(self.paths[last].keys()):
                    if self.paths[last][kye][0] == target:
                        direc = kye
                        break
                last_elem = (last, direc)
                output.append(last_elem)

            else:
                dire = Direction.WEST
                for key in self.paths[node_list[num]].keys():
                    if self.paths[node_list[num]][key][0] == node_list[num + 1]:
                        dire = key
                        break
                element = (node_list[num], dire)
                output.append(element)

        return output






