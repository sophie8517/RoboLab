import time
import traceback
from copy import copy
from dataclasses import dataclass
import socket
from typing import List

from ev3dev import ev3

from communication import Communication
from planet import Direction, Position, Planet
from sensors import Sensors, SquareColor, Color
from server import DebugServer


@dataclass
class FollowLineResult:
    dx: int
    dy: int
    relative_direction: Direction
    barrier: bool


class Movement:
    def __init__(self, communication: Communication):
        self.communication = communication

        self.motor_right = ev3.LargeMotor("outD")
        self.motor_right.reset()
        self.motor_right.stop_action = "brake"
        self.motor_left = ev3.LargeMotor("outA")
        self.motor_left.reset()
        self.motor_left.stop_action = "brake"
        self.sound = ev3.Sound()
        self.sensors = Sensors()

        self.debug_server = DebugServer(self.motor_left, self.motor_right)
        self.planet = Planet()

        self.position = Position

    def calibrate_red_blue(self) -> None:
        input("Set me on a blue square and press enter")
        self.sensors.blue = self.sensors.get_color()
        input("Set me on a red square and press enter")
        self.sensors.red = self.sensors.get_color()

        print(f"self.sensors.red = {self.sensors.red}")
        print(f"self.sensors.blue = {self.sensors.blue}")

    def calibrate_black_white(self) -> None:
        input("Set next to a path and press enter")
        self.sensors.white = self.sensors.get_color()
        self.sensors.black = self.sensors.get_color()

        self.motor_right.speed_sp = -30
        self.motor_left.speed_sp = 30
        self.motor_right.command = "run-forever"
        self.motor_left.command = "run-forever"

        for i in range(100):
            current_color = self.sensors.get_color()
            if current_color.brightness() < self.sensors.black.brightness():
                self.sensors.black = current_color

            if current_color.brightness() > self.sensors.white.brightness():
                self.sensors.white = current_color

            time.sleep(0.1)

            if i == 45:
                self.motor_right.speed_sp = 30
                self.motor_left.speed_sp = -30
                self.motor_right.command = "run-forever"
                self.motor_left.command = "run-forever"

        self.motor_right.stop()
        self.motor_left.stop()

        print(f"self.sensors.white = {self.sensors.white}")
        print(f"self.sensors.black = {self.sensors.black}")

    def calibrate_colors(self) -> None:
        calibrate_response = input("Calibrate colors? [y/N]")
        if calibrate_response.lower().startswith("y"):
            self.calibrate_red_blue()
            self.calibrate_black_white()
        else:
            self.sensors.red = Color(r=165, g=68, b=26)
            self.sensors.blue = Color(r=33, g=160, b=137)

            self.sensors.white = Color(r=295, g=468, b=287)
            self.sensors.black = Color(r=28, g=68, b=22)

    def turn(self, angle: int) -> None:
        print(f"Tun {angle} degrees...")
        turn_left = angle < 0
        # 19 sec -> 360 degree
        if turn_left:
            self.motor_right.speed_sp = 50
            self.motor_left.speed_sp = -50
        else:  # turn right
            self.motor_right.speed_sp = -50
            self.motor_left.speed_sp = 50
        self.motor_right.command = "run-forever"
        self.motor_left.command = "run-forever"
        time.sleep((19 / 360) * abs(angle))
        self.motor_right.stop()
        self.motor_left.stop()
        print("Turned")

    def move_forward(self, time_sec: int, speed: int = 50) -> None:
        print(f"Move forward: time_sec:{time_sec}, speed={speed}...")
        self.motor_right.speed_sp = speed
        self.motor_left.speed_sp = speed

        self.motor_right.command = "run-forever"
        self.motor_left.command = "run-forever"

        time.sleep(time_sec)

        self.motor_right.stop()
        self.motor_left.stop()
        print("Moved forward")

    def follow_line(self, speed: int = 80) -> FollowLineResult:
        self.motor_right.position = 0
        self.motor_left.position = 0
        moto_pos_list = []

        print("Following line...")
        barrier_on_path = False
        while True:
            current_brightness = self.sensors.get_color().brightness()
            turn = 0.5 * (current_brightness - self.sensors.black_white_diff)
            self.motor_right.speed_sp = speed - turn
            self.motor_left.speed_sp = speed + turn
            self.motor_right.command = "run-forever"
            self.motor_left.command = "run-forever"

            moto_pos_list.append((self.motor_left.position, self.motor_right.position))

            if self.sensors.has_barrier():
                # TODO better turning, might not find path if barrier in curve
                barrier_on_path = True
                self.sound.beep()
                self.turn(170)

            if self.sensors.get_square_color() != SquareColor.NOT_ON_SQUARE:
                self.motor_right.stop()
                self.motor_left.stop()
                result = FollowLineResult(1, 1, Direction.NORTH, barrier_on_path)
                print(f"Followed line with result: {result}")
                print(moto_pos_list)
                return result

    def turn_and_scan(self) -> bool:
        print("Turn and scan...")
        angle = 85
        total_sleep = (19 / 360) * angle
        has_path = False

        self.motor_right.speed_sp = -50
        self.motor_left.speed_sp = 50
        self.motor_right.command = "run-forever"
        self.motor_left.command = "run-forever"

        for i in range(100):
            time.sleep(total_sleep / 100)
            if abs(self.sensors.get_color().brightness() - self.sensors.black.brightness()) < 50:
                has_path = True

        self.motor_right.stop()
        self.motor_left.stop()
        time.sleep(0.5)
        print(f"Turned and scanned. has_path: {has_path}")
        return has_path

    def scan_ways(self) -> List[Direction]:
        print("Scanning ways...")
        self.turn(-45)
        result_list: List[Direction] = []

        if self.turn_and_scan():
            result_list.append(Direction.NORTH)

        if self.turn_and_scan():
            result_list.append(Direction.EAST)

        if self.turn_and_scan():
            result_list.append(Direction.SOUTH)

        if self.turn_and_scan():
            result_list.append(Direction.WEST)

        print(f"Scanned ways, result: {result_list}")
        return result_list

    def turn_to_way(self, new_direc):


        angle = int(new_direc)
        self.turn(angle-15)

        while abs(self.sensors.get_color().brightness() - self.sensors.black.brightness()) > 50:
            self.motor_right.speed_sp = -50
            self.motor_left.speed_sp = 50
            self.motor_right.command = "run-forever"
            self.motor_left.command = "run-forever"

        self.motor_left.stop()
        self.motor_right.stop()
        time.sleep(0.5)






    def main_loop(self):
        self.calibrate_colors()

        #ready_response = self.communication.send_ready()
        #self.planet.name = ready_response.planet_name
        #self.position = ready_response.start_position

        while True:
            follow_line_result = self.follow_line(speed=80)


            #if not follow_line_result.barrier:
                #old_position = copy(self.position)
                #self.position.point.x += follow_line_result.dx
                #self.position.point.y += follow_line_result.dy
                #self.position.direction = (self.position.direction + follow_line_result.relative_direction) % 360

                #start_tuple = ((old_position.point.x, old_position.point.y), old_position.direction)
                #target_tuple = ((self.position.point.x, self.position.point.y), self.position.direction)
                #self.planet.add_path(start_tuple, target_tuple, 1)

            self.move_forward(4)

            res_scan_ways = self.scan_ways()
            self.turn(45)
            l = Direction.EAST
            self.turn_to_way(l)

            # TODO smart path selection

    def main(self):
        while True:
            try:
                self.main_loop()
                print("done")
                self.debug_server.start()


            except KeyboardInterrupt:
                print("keyyyy")
                self.debug_server.start()
            except Exception as e:
                traceback.print_exc()
                self.debug_server.start()
