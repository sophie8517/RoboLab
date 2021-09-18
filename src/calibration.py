from dataclasses import dataclass
import time

import ev3dev.core

from sensors import Sensors, Color


@dataclass
class CalibrationResult:
    black: Color
    white: Color
    red: Color
    blue: Color


class Calibration:
    def __init__(self, motor_left: ev3dev.core.LargeMotor, motor_right: ev3dev.core.LargeMotor, sensors: Sensors):
        self.motor_left = motor_left
        self.motor_right = motor_right
        self.sensors = sensors

    def calibrate_red_blue(self) -> tuple[Color, Color]:
        input("Set me on a blue square and press enter")
        blue = self.sensors.get_color()
        input("Set me on a red square and press enter")
        red = self.sensors.get_color()

        print(f"{red=}")
        print(f"{blue=}")
        return red, blue

    def calibrate_black_white(self) -> tuple[Color, Color]:
        input("Set next to a path and press enter")
        white: Color = self.sensors.get_color()
        black: Color = self.sensors.get_color()

        self.motor_right.speed_sp = -30
        self.motor_left.speed_sp = 30
        self.motor_right.command = "run-forever"
        self.motor_left.command = "run-forever"

        for i in range(100):
            current_color = self.sensors.get_color()
            if current_color.brightness() < black.brightness():
                black = current_color

            if current_color.brightness() > white.brightness():
                white = current_color

            time.sleep(0.1)

            if i == 45:
                self.motor_right.speed_sp = 30
                self.motor_left.speed_sp = -30
                self.motor_right.command = "run-forever"
                self.motor_left.command = "run-forever"

        self.motor_right.stop()
        self.motor_left.stop()

        print(f"{black=}")
        print(f"{white=}")
        return black, white

    def calibrate_colors(self) -> None:
        calibrate_response = input("Calibrate colors? [y/N]")
        if calibrate_response.lower().startswith("y"):
            red, blue = self.calibrate_red_blue()
            black, white = self.calibrate_black_white()
            input("Press enter to continue")
        else:
            # red = Color(r=177, g=64, b=27)
            # blue = Color(r=46, g=154, b=153)
            #
            # black = Color(r=31, g=64, b=25)
            # white = Color(r=328, g=487, b=301)

            # Foyer
            red = Color(r=171, g=69, b=27)
            blue = Color(r=52, g=191, b=153)

            black = Color(r=33, g=63, b=28)
            white = Color(r=323, g=481, b=299)

        self.sensors.black = black
        self.sensors.white = white
        self.sensors.red = red
        self.sensors.blue = blue
