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
from planet import Direction, Position, Planet, Point
from sensors import Sensors, SquareColor, Color
from server import DebugServer
from smart_discovery import SmartDiscovery


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
        self.smart_discovery = SmartDiscovery(self.planet)

        self.position = Position(Point(-11, -11), Direction.NORTH)

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

    def move_forward(self, time_seconds: int, speed: int = 50) -> None:
        # print(f"Move forward: time_sec:{time_sec}, speed={speed}...")
        self.motor_right.speed_sp = speed
        self.motor_left.speed_sp = speed

        self.motor_right.command = "run-forever"
        self.motor_left.command = "run-forever"

        time.sleep(time_seconds)

        self.motor_right.stop()
        self.motor_left.stop()
        # print("Moved forward")

    def follow_line(self, speed: int = 80) -> FollowLineResult:
        self.motor_right.position = 0
        self.motor_left.position = 0
        motor_ticks = []

        # print("Following line...")
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
                # print(f"{result}")
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

    def scan_ways_relative(self) -> List[Direction]:
        # print("Scanning ways...")
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

        # print(f"Scanned ways, result: {result_list}")
        return result_list

    def scan_ways_absolute(self) -> List[Direction]:
        relative_directions = self.scan_ways_relative()
        absolute_directions: List[Direction] = []

        for relative_direction in relative_directions:
            absolute_directions.append(Direction((relative_direction + self.position.direction) % 360))

        return absolute_directions

    def turn_to_way_relative(self, direction_relative: Direction) -> None:
        # print(f"turn_to_way_relative({direction_relative})")
        if direction_relative == Direction.NORTH:
            return

        self.position.direction = Direction((self.position.direction + direction_relative) % 360)

        angle = int(direction_relative)
        self.turn(angle - 15)

        while abs(self.sensors.get_color().brightness() - self.sensors.black.brightness()) > 50:
            self.motor_right.speed_sp = -50
            self.motor_left.speed_sp = 50
            self.motor_right.command = "run-forever"
            self.motor_left.command = "run-forever"

        self.motor_left.stop()
        self.motor_right.stop()
        time.sleep(0.5)

    def turn_to_way_absolute(self, direction_absolute: Direction) -> None:
        # print(f"turn_to_way_abolute({direction_absolute})")
        # print(f"Cur direction: {self.position.direction}")
        direction_relative = Direction((direction_absolute - self.position.direction) % 360)
        self.turn_to_way_relative(direction_relative)

    def initial_start(self) -> None:
        self.calibration.calibrate_colors()

        self.follow_line()
        self.move_forward(4)

        ready_response = self.communication.send_ready()

        if not ready_response:
            raise Exception("No response from mothership (ready message sent)")

        self.planet.name = ready_response.planet_name
        self.communication.client.subscribe(f"planet/{self.planet.name}/229")
        self.communication.planet = self.planet.name
        self.position = ready_response.start_position
        print(f"Planet Name: {self.planet.name}")
        print(f"{self.position}")

        possible_directions_absolute = self.scan_ways_absolute()

        # don't add start line, which would go into the void
        possible_directions_absolute.remove(self.position.direction.turned())

        if not possible_directions_absolute:
            raise Exception("No possible directions")

        self.smart_discovery.add_possible_directions(self.position.point, possible_directions_absolute)

        self.turn_to_way_absolute(possible_directions_absolute[0])

    def main_loop(self) -> bool:
        follow_line_result = self.follow_line(speed=100)

        old_position = deepcopy(self.position)
        if self.position.direction == Direction.NORTH:
            self.position.point.x += follow_line_result.dx
            self.position.point.y += follow_line_result.dy
        elif self.position.direction == Direction.SOUTH:
            self.position.point.x -= follow_line_result.dx
            self.position.point.y -= follow_line_result.dy
        elif self.position.direction == Direction.WEST:
            self.position.point.x -= follow_line_result.dy
            self.position.point.y += follow_line_result.dx
        else:
            self.position.point.x += follow_line_result.dy
            self.position.point.y -= follow_line_result.dx

        self.position.direction = Direction((self.position.direction + follow_line_result.relative_direction) % 360)

        print(f"{old_position} ---> {self.position}")

        path_response = self.communication.send_path(old_position, self.position.turned(),
                                                     follow_line_result.path_blocked)

        if path_response.start_position != old_position or path_response.end_position != self.position.turned():
            print("Odometry was wrong -> got correction from mothership:")
            print("Start", path_response.start_position)
            print("End", path_response.end_position)
            self.position = path_response.end_position.turned()

        self.planet.add_path_points(path_response.start_position, path_response.end_position,
                                    path_response.path_weight)
        self.smart_discovery.remove_direction(path_response.start_position.point,
                                              path_response.start_position.direction)
        self.smart_discovery.remove_direction(path_response.end_position.point,
                                              path_response.end_position.direction)

        self.move_forward(4)

        if not self.smart_discovery.was_on_point(self.position.point):
            res_scan_ways_absolute = self.scan_ways_absolute()
            try:
                res_scan_ways_absolute.remove(self.position.direction.turned())
            except:
                print("Error???")

            self.smart_discovery.add_possible_directions(self.position.point, res_scan_ways_absolute)

        selected_direction = self.smart_discovery.next_direction(self.position.point)
        if selected_direction is None:
            return True

        selected_position = Position(self.position.point, selected_direction)
        send_path_select_response = self.communication.send_path_select(selected_position)
        if send_path_select_response:
            print(f"Better direction form mothership: {send_path_select_response}")
            # TODO check if path is blocked, mothership may send an impossible direction
            self.turn_to_way_absolute(send_path_select_response)
        else:
            print(f'selected direction: {selected_direction}')
            self.turn_to_way_absolute(selected_direction)

        return False

    def main(self) -> None:
        while True:
            try:
                self.initial_start()
                done = False
                while not done:
                    done = self.main_loop()
                print("---- DONE ----")
                self.debug_server.start()

            except KeyboardInterrupt:
                print("---- KEYBOARD INTERRUPT ----")
                self.debug_server.start()
            except Exception as e:
                print("---- ERROR ----")
                traceback.print_exc()
                self.debug_server.start()
