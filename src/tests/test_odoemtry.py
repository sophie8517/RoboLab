#!/usr/bin/env python3
import json
import unittest

from odometry import Odometry
from planet import Direction


class TestRoboLabOdometry(unittest.TestCase):
    def setUp(self):
        self.odometry = Odometry()

    @staticmethod
    def ticks_from_file(filename: str):
        with open(f'odometry_testfiles/{filename}', 'r') as reader:
            ticks = json.load(reader)
            return ticks

    def test_straight_line(self):
        calc_result = self.odometry.calc(self.ticks_from_file("straight_line.json"))
        print(calc_result)
        self.assertEqual(calc_result.dx, 0)
        self.assertEqual(calc_result.dy, 1)
        self.assertEqual(calc_result.direction, Direction.NORTH)

    def test_straight_line_long(self):
        calc_result = self.odometry.calc(self.ticks_from_file("straight_line_long.json"))
        print(calc_result)
        self.assertEqual(calc_result.dx, 0)
        self.assertEqual(calc_result.dy, 2)
        self.assertEqual(calc_result.direction, Direction.NORTH)

    def test_curve_right(self):
        calc_result = self.odometry.calc(self.ticks_from_file("curve_right.json"))
        print(calc_result)
        self.assertEqual(calc_result.dx, 1)
        self.assertEqual(calc_result.dy, 1)
        self.assertEqual(calc_result.direction, Direction.EAST)

    def test_curve_left(self):
        calc_result = self.odometry.calc(self.ticks_from_file("curve_left.json"))
        print(calc_result)
        self.assertEqual(calc_result.dx, -1)
        self.assertEqual(calc_result.dy, 1)
        self.assertEqual(calc_result.direction, Direction.WEST)

    def test_loop_right(self):
        calc_result = self.odometry.calc(self.ticks_from_file("loop_right.json"))
        print(calc_result)
        self.assertEqual(calc_result.dx, 0)
        self.assertEqual(calc_result.dy, 0)
        self.assertEqual(calc_result.direction, Direction.WEST)

    def test_loop_left(self):
        calc_result = self.odometry.calc(self.ticks_from_file("loop_left.json"))
        print(calc_result)
        self.assertEqual(calc_result.dx, 0)
        self.assertEqual(calc_result.dy, 0)
        self.assertEqual(calc_result.direction, Direction.EAST)


if __name__ == "__main__":
    unittest.main()
