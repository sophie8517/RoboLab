import time
from dataclasses import dataclass
from typing import List

import ev3dev.ev3 as ev3

from planet import Direction


@dataclass
class Color:
    r: int
    g: int
    b: int

    def brightness(self) -> int:
        return int((self.r + self.g + self.b) / 3)


@dataclass
class FollowLineResult:
    dx: int
    dy: int
    barrier: bool


class Movement:
    def __init__(self):
        self.color_sensor = ev3.ColorSensor()
        self.color_sensor.mode = 'RGB-RAW'

        self.ultrasonic_sensor = ev3.UltrasonicSensor()
        self.ultrasonic_sensor.mode = 'US-DIST-CM'
        self.ultrasonic_sensor.mode = 'US-SI-CM'

        self.motor_right = ev3.LargeMotor("outD")
        self.motor_right.reset()
        self.motor_right.stop_action = "brake"
        self.motor_left = ev3.LargeMotor("outA")
        self.motor_left.reset()
        self.motor_left.stop_action = "brake"

        self.black = Color
        self.white = Color

        self.blue = Color
        self.red = Color

    @property
    def black_white_diff(self) -> float:
        return (self.white.brightness() - self.black.brightness()) / 2

    def get_color(self) -> Color:
        current_color = self.color_sensor.bin_data("hhh")
        return Color(current_color[0], current_color[1], current_color[2])

    def calibrate_red_blue(self) -> None:
        input("Set me on a blue square and press enter")
        self.blue = self.get_color()
        input("Set me on a red square and press enter")
        self.red = self.get_color()

        print(f"self.red = {self.red}")
        print(f"self.blue = {self.blue}")

    def calibrate_black_white(self) -> None:
        self.white = self.get_color()
        self.black = self.get_color()

        self.motor_right.speed_sp = -30
        self.motor_left.speed_sp = 30
        self.motor_right.command = "run-forever"
        self.motor_left.command = "run-forever"

        for i in range(100):
            current_color = self.get_color()
            if current_color.brightness() < self.black.brightness():
                self.black = current_color

            if current_color.brightness() > self.white.brightness():
                self.white = current_color

            time.sleep(0.1)

            if i == 45:
                self.motor_right.speed_sp = 30
                self.motor_left.speed_sp = -30
                self.motor_right.command = "run-forever"
                self.motor_left.command = "run-forever"

        self.motor_right.stop()
        self.motor_left.stop()

        print(f"self.white = {self.white}")
        print(f"self.black = {self.black}")

    def follow_line(self, speed: int = 80):
        while True:
            current_brightness = self.get_color().brightness()
            turn = 0.2 * (current_brightness - self.black_white_diff)
            self.motor_right.speed_sp = speed - turn
            self.motor_left.speed_sp = speed + turn
            self.motor_right.command = "run-forever"
            self.motor_left.command = "run-forever"

        # return FollowLineResult(1, 1, False)

    def scan_ways(self) -> List[Direction]:
        # TODO
        pass

    def main_loop(self):
        # self.calibrate_black_white()
        self.white = Color(r=279, g=450, b=273)
        self.black = Color(r=23, g=57, b=21)

        self.follow_line()

        # self.calibrate_red_blue()

        # while True:
        #    self.follow_line()
        #   self.scan_ways()
        # send ready message to mothership

        # follow line
        # find all paths on edge
        # send position to mothership
        #
        print("done")
