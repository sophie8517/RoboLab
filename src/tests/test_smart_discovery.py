import unittest

from planet import Planet, Point, Direction, Position
from smart_discovery import SmartDiscovery


class TestRoboLabSmartDiscovery(unittest.TestCase):
    def setUp(self):
        self.planet = Planet()
        self.smart_discovery = SmartDiscovery(self.planet)
        self.test_points = [Point(1, 5), Point(1, 6), Point(2, 4), Point(2, 6), Point(2, 8), Point(3, 4),
                            Point(3, 5), Point(3, 6), Point(3, 7), Point(0, 3)
                            ]
        north = Direction.NORTH
        east = Direction.EAST
        south = Direction.SOUTH
        west = Direction.WEST

        self.smart_discovery.discovered_points.append(self.test_points[1])
        self.smart_discovery.discovered_points.append(self.test_points[2])
        self.smart_discovery.discovered_points.append(self.test_points[5])
        self.smart_discovery.discovered_points.append(self.test_points[6])
        self.smart_discovery.discovered_points.append(self.test_points[7])

        self.smart_discovery.paths = {self.test_points[2]: {west: True, east: True}, # (2, 4)
                                      self.test_points[0]: {south: True, east: False}, # (1, 5)
                                      self.test_points[5]: {west: True}, # (3, 4)
                                      self.test_points[6]: {east: True}, # (3, 5)
                                      self.test_points[8]: {east: True, north: False, south: False}, # (3, 7)
                                      self.test_points[9]: {east: True, west: False} # (0, 3)
                                      }

    def test_has_point_undiscovered_paths(self):
        self.assertTrue(self.smart_discovery.has_point_undiscovered_paths(Point(1, 5)))
        self.assertTrue(self.smart_discovery.has_point_undiscovered_paths(Point(3, 7)))
        self.assertFalse(self.smart_discovery.has_point_undiscovered_paths(Point(3, 5)), "Expected to get 'Fasle'")

    def test_add_scan_result(self):
        # points to add: Point(-2, 2),  Point(-3, -1)
        dir_list_1 = [Direction.NORTH, Direction.SOUTH, Direction.WEST]
        dir_list_2 = [Direction.NORTH, Direction.EAST]

        self.smart_discovery.add_scan_result(Point(-2, 2), dir_list_1)
        self.smart_discovery.add_scan_result(Point(-3, -1), dir_list_2)

        dir_discovery_1 = self.smart_discovery.paths[Point(-2, 2)]
        dir_discovery_2 = list(self.smart_discovery.paths[Point(-3, -1)].keys())

        self.assertIsNotNone(dir_discovery_1, "expected list of directions")
        self.assertEqual(dir_list_2, dir_discovery_2, "Expected equal lists ")

        self.assertEqual(len(dir_list_1), len(dir_discovery_1), "Expected length: 3")
        self.assertEqual(len(dir_list_2), len(dir_discovery_2), "Expected length: 2")

    def test_add_discovered_path(self):
        # case 1: start and end points not in paths. Numbers in variable names specify x and y
        start28 = self.test_points[4]
        end26 = self.test_points[3]
        end16 = self.test_points[1]
        self.smart_discovery.add_discovered_path(Position(start28, Direction.SOUTH),
                                                 Position(end26, Direction.NORTH))
        self.assertTrue(start28 in self.smart_discovery.paths, "Expected 'True'")
        self.assertTrue(end26 in self.smart_discovery.paths, "Expected 'True'")
        self.assertIsNotNone(self.smart_discovery.paths[end26])

        # case 2: start point in paths
        self.smart_discovery.add_discovered_path(Position(start28, Direction.WEST),
                                                 Position(end16, Direction.NORTH))
        self.assertEqual(2, len(self.smart_discovery.paths[start28]), " Expected length: 2")

        # case 3: start and end points in paths
        directions = [Direction.SOUTH, Direction.WEST]
        dir_of_smart_recovery = list(self.smart_discovery.paths[start28].keys())
        self.assertEqual(directions, dir_of_smart_recovery, "Results are not Equal. Expected:".format(directions))

    def test_next_direction(self):

        my_point = Point(1, 1)
        self.smart_discovery.add_scan_result(my_point, [Direction.NORTH, Direction.WEST])
        self.assertEqual(self.smart_discovery.next_direction(my_point), Direction.NORTH)

        self.smart_discovery.mark_discovered(my_point, Direction.NORTH)

        self.assertEqual(self.smart_discovery.next_direction(my_point), Direction.WEST)

        self.smart_discovery.mark_discovered(my_point, Direction.WEST)

        self.assertIsNone(self.smart_discovery.next_direction(my_point))

    def test_mark_discovered(self):

        self.assertFalse(self.smart_discovery.paths[self.test_points[0]][Direction.EAST])
        self.assertFalse(self.smart_discovery.paths[self.test_points[8]][Direction.SOUTH])

        self.smart_discovery.mark_discovered(self.test_points[0], Direction.EAST)
        self.smart_discovery.mark_discovered(self.test_points[8], Direction.SOUTH)

        self.assertTrue(self.smart_discovery.paths[self.test_points[0]][Direction.EAST])
        self.assertTrue(self.smart_discovery.paths[self.test_points[8]][Direction.SOUTH])

    def test_is_discovered_point(self):
        self.assertTrue(self.smart_discovery.is_discovered_point(self.test_points[1]), "Expected result: 'True'")
        self.assertTrue(self.smart_discovery.is_discovered_point(self.test_points[7]), "Expected result: 'True'")
        self.assertFalse(self.smart_discovery.is_discovered_point(self.test_points[8]), "Expected result: 'False'")

    def test_get_all_points_with_undiscovered_paths(self):
        expected = {self.test_points[0], self.test_points[8], self.test_points[9]}
        result = self.smart_discovery.get_all_points_with_undiscovered_paths()
        self.assertEqual(expected, result, "Set are not equal")
