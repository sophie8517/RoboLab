import math
from dataclasses import dataclass
from enum import Enum

from ev3dev import ev3


@dataclass
class Color:
    r: int
    g: int
    b: int

    def brightness(self) -> int:
        return int((self.r + self.g + self.b) / 3)

    def diff(self, other_color):
        return math.sqrt(
            math.pow(self.r - other_color.r, 2) + math.pow(self.g - other_color.g, 2) + math.pow(self.b - other_color.b,
                                                                                                 2))


class SquareColor(Enum):
    NOT_ON_SQUARE = 0
    BLUE = 1
    RED = 2


class Sensors:
    def __init__(self):
        self.color_sensor = ev3.ColorSensor()
        self.color_sensor.mode = 'RGB-RAW'

        self.ultrasonic_sensor = ev3.UltrasonicSensor()
        self.ultrasonic_sensor.mode = 'US-DIST-CM'
        self.ultrasonic_sensor.mode = 'US-SI-CM'

        self.black = Color
        self.white = Color

        self.blue = Color
        self.red = Color

    def get_color(self) -> Color:
        current_color = self.color_sensor.bin_data("hhh")
        return Color(current_color[0], current_color[1], current_color[2])

    @property
    def black_white_diff(self) -> float:
        return (self.white.brightness() - self.black.brightness()) / 2

    def get_square_color(self) -> SquareColor:
        diff_red = self.get_color().diff(self.red)
        diff_blue = self.get_color().diff(self.blue)

        if diff_red < 40:
            return SquareColor.RED
        if diff_blue < 40:
            return SquareColor.BLUE
        return SquareColor.NOT_ON_SQUARE

    def has_barrier(self) -> bool:
        return self.ultrasonic_sensor.distance_centimeters < 20
