# !/usr/bin/env python3
import json
import math
from dataclasses import dataclass

from planet import Direction


@dataclass
class CalculatePreciseResult:
    dx_cm: float
    dy_cm: float
    s_cm: float
    angle_degree: float


@dataclass
class CalculateResult:
    dx: int
    dy: int
    direction: Direction


class Odometry:
    def __init__(self):
        """
        Initializes odometry module
        """

        # YOUR CODE FOLLOWS (remove pass, please!)
        #############
        # Constants #
        #############
        self.distance_per_tick = 14.5 / 300
        self.wheel_distance = 15.6

    def calculate_precise(self, motor_ticks: list[tuple[int, int]]) -> CalculatePreciseResult:
        dx = 0
        dy = 0
        s_ges = 0
        gamma_rad = 0

        ticks_delta: list[tuple[int, int]] = []
        last_element = motor_ticks.pop(0)
        for i in motor_ticks:
            ticks_delta.append((i[0] - last_element[0], i[1] - last_element[1]))
            last_element = i

        length_delta: list[tuple[float, float]] = []

        for i in ticks_delta:
            dl = i[0] * self.distance_per_tick
            dr = i[1] * self.distance_per_tick
            alpha = (dl - dr) / self.wheel_distance
            beta = alpha / 2
            if alpha != 0:
                s = ((dr + dl) / alpha) * math.sin(beta)
            else:
                s = dr
            dx += math.sin(gamma_rad + beta) * s
            dy += math.cos(gamma_rad + beta) * s
            s_ges += s
            gamma_rad += alpha
            length_delta.append((s, alpha))

        return CalculatePreciseResult(dx, dy, s_ges, math.degrees(gamma_rad))

    @staticmethod
    def calculate_grid(dx_cm: float, dy_cm: float, angle_degree: float) -> CalculateResult:
        dx = round(dx_cm / 50)
        dy = round(dy_cm / 50)
        angle = round(angle_degree / 90) * 90
        angle = angle % 360
        direction = Direction(angle)
        return CalculateResult(dx, dy, direction)

    def calc(self, motor_ticks: list[tuple[int, int]]) -> CalculateResult:
        my_precise_result = self.calculate_precise(motor_ticks)
        return self.calculate_grid(my_precise_result.dx_cm, my_precise_result.dy_cm, my_precise_result.angle_degree)


if __name__ == '__main__':
    o = Odometry()

    with open('../odometrie_json/zwei_mal_45_cm_gerade.json', 'r') as reader:
        ticks = json.load(reader)

    precise_result = o.calculate_precise(ticks)
    print(precise_result)

    grid_result = o.calculate_grid(precise_result.dx_cm, precise_result.dy_cm, precise_result.angle_degree)
    print(grid_result)
