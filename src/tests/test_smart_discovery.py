import unittest

from planet import Planet, Point, Direction, Position
from smart_discovery import SmartDiscovery


class TestRoboLabSmartDiscovery(unittest.TestCase):
    def setUp(self):
        self.planet = Planet()
        self.smart_discovery = SmartDiscovery(self.planet)

    def test_simple_next_direction(self):
        my_point = Point(1, 1)
        self.smart_discovery.add_possible_directions(my_point, [Direction.NORTH, Direction.WEST])
        self.assertEqual(self.smart_discovery.next_direction(my_point), Direction.NORTH)

        self.smart_discovery.remove_direction(my_point, Direction.NORTH)

        self.assertEqual(self.smart_discovery.next_direction(my_point), Direction.WEST)

        self.assertIsNone(self.smart_discovery.next_direction(my_point))

    def test_remove_direction(self):
        start_point = Point(1, 1)
        end_point = Point(3, 3)

        self.planet.add_path_points(Position(start_point, Direction.WEST), Position(end_point, Direction.EAST), 12)

        self.smart_discovery.add_possible_directions(end_point, [Direction.NORTH])

        self.assertEqual(self.smart_discovery.next_direction(start_point), Direction.WEST)

        self.smart_discovery.remove_direction(end_point, Direction.NORTH)

        self.assertIsNone(self.smart_discovery.next_direction(start_point))

    def test_multiple_paths(self):
        start_point = Point(1, 1)
        end_point = Point(10, 10)
        middle_point = Point(5, 5)

        self.planet.add_path_points(Position(start_point, Direction.NORTH), Position(end_point, Direction.SOUTH), 15)

        self.planet.add_path_points(Position(start_point, Direction.WEST), Position(middle_point, Direction.EAST), 1)
        self.planet.add_path_points(Position(middle_point, Direction.WEST), Position(end_point, Direction.EAST), 3)

        self.smart_discovery.add_possible_directions(end_point, [Direction.NORTH])

        self.assertEqual(self.smart_discovery.next_direction(start_point), Direction.WEST)