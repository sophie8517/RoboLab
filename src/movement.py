import time
import traceback
from copy import deepcopy
from dataclasses import dataclass
import socket
from typing import List

from ev3dev import ev3

from calibration import Calibration
from communication import Communication
from odometry import Odometry
from planet import Direction, Position, Planet
from sensors import Sensors, SquareColor, Color
from server import DebugServer


@dataclass
class FollowLineResult:
    dx: int
    dy: int
    relative_direction: Direction
    path_blocked: bool


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
        self.calibration = Calibration(self.motor_left, self.motor_right, self.sensors)
        self.planet = Planet()
        self.odometry = Odometry()

        self.position:  Position

    def turn(self, angle: int) -> None:
        # print(f"Tun {angle} degrees...")
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
        # print("Turned")

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
        motor_ticks = []

        print("Following line...")
        barrier_on_path = False
        while True:
            current_brightness = self.sensors.get_color().brightness()
            turn = 0.5 * (current_brightness - self.sensors.black_white_diff)
            self.motor_right.speed_sp = speed - turn
            self.motor_left.speed_sp = speed + turn
            self.motor_right.command = "run-forever"
            self.motor_left.command = "run-forever"

            motor_ticks.append((self.motor_left.position, self.motor_right.position))

            if self.sensors.has_barrier():
                # TODO better turning, might not find path if barrier in curve
                barrier_on_path = True
                self.sound.beep()
                self.turn(170)

            if self.sensors.get_square_color() != SquareColor.NOT_ON_SQUARE:
                self.motor_right.stop()
                self.motor_left.stop()

                odometry_result = self.odometry.calc(motor_ticks)
                result = FollowLineResult(odometry_result.dx, odometry_result.dy, odometry_result.direction,
                                          barrier_on_path)
                print(f"Followed line with result: {result}")
                return result

    def turn_and_scan(self) -> bool:
        # print("Turn and scan...")
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
        # print(f"Turned and scanned. has_path: {has_path}")
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

        self.turn(45)

        print(f"Scanned ways, result: {result_list}")
        return result_list

    def turn_to_way(self, new_direc):

        angle = int(new_direc)
        self.turn(angle - 15)

        while abs(self.sensors.get_color().brightness() - self.sensors.black.brightness()) > 50:
            self.motor_right.speed_sp = -50
            self.motor_left.speed_sp = 50
            self.motor_right.command = "run-forever"
            self.motor_left.command = "run-forever"

        self.motor_left.stop()
        self.motor_right.stop()
        time.sleep(0.5)

    def main_loop(self):
        self.calibration.calibrate_colors()

        self.follow_line(speed=80)
        self.move_forward(4)

        ready_response = self.communication.send_ready()
        self.planet.name = ready_response.planet_name
        self.communication.client.subscribe(f"planet/{self.planet.name}/229")
        self.communication.planet = self.planet.name
        self.position = ready_response.start_position
        print("Planet Name: ", self.planet.name)
        print("Position: ", self.position)

        while True:
            follow_line_result = self.follow_line(speed=80)

            old_position = deepcopy(self.position)
            self.position.point.x += follow_line_result.dx
            self.position.point.y += follow_line_result.dy
            self.position.direction = (self.position.direction + follow_line_result.relative_direction) % 360

            if follow_line_result.path_blocked:
                weight = -1
            else:
                weight = 1
            send_path_response = self.communication.send_path(old_position, self.position.turned(),
                                                              follow_line_result.path_blocked)
            print("Send path response: ", send_path_response)
            self.planet.add_path_points(send_path_response.start_position, send_path_response.end_position,
                                        send_path_response.path_weight)

            self.move_forward(4)

            res_scan_ways = self.scan_ways()

            # TODO smart path selection
            selected_direction_relative = res_scan_ways[0]
            selected_direction_absolute = Direction((selected_direction_relative + self.position.direction) % 360)
            selected_position = Position(self.position.point, selected_direction_absolute)
            send_path_select_response = self.communication.send_path_select(selected_position)
            print("Path select response: ", send_path_select_response)
            if send_path_select_response:
                self.turn_to_way()
            else:
                self.turn_to_way(selected_direction_relative)

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
