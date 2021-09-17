import json
import time
import traceback
from copy import deepcopy
from dataclasses import dataclass
import socket
from datetime import datetime
from typing import List, Optional

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
        self.target: Optional[Point] = None

    def turn(self, angle: int) -> None:
        # print(f"Tun {angle} degrees...")
        turn_left = angle < 0
        # 19 sec -> 360 degree
        if turn_left:
            self.motor_right.speed_sp = 200
            self.motor_left.speed_sp = -200
        else:  # turn right
            self.motor_right.speed_sp = -200
            self.motor_left.speed_sp = 200
        self.motor_right.command = "run-forever"
        self.motor_left.command = "run-forever"
        time.sleep((4.76698 / 360) * abs(angle))
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

    def follow_line(self) -> FollowLineResult:
        self.motor_right.position = 0
        self.motor_left.position = 0
        motor_ticks = []
        # testen: 280, 120, 30
        # noch nicht: speed 280, Kp 140, Kd 10
        # verbessern: speed 280, Kp 140, Kd 20
        bwd = self.sensors.black_white_diff
        speed = 60
        # speed 40, Kp 210, Kd 80
        # speed 40, Kp 240, Kd 80
        # speed 55, Kp 300, Kd 150
        # speed 55, Kp 280, Kd 160
        # speed 50, Kp 250, Kd 80, Ki 5
        # speed 55, Kp 250, Kd 80, Ki 2
        # speed 55, Kp 250, Kd 130
        # 230 70 2 bei speed 60 -> funktioniert gut mit setzen von speed_l und speed_r
        # 260 120 0 bei speed 55
        # 290 70 2 bei speed 60 mit prev error berechnung
        # 310 60 2 bei speed 60 mit prev error berechnung, besser als vorher
        # 308 55 2 noch besser
        Kp = 308
        Kd = 55
        Ki = 2
        prev_error = 0
        intgr = 0
        speed_l = speed
        speed_r = speed

        black_brightness = self.sensors.black.brightness()

        # print("Following line...")
        barrier_on_path = False
        while True:
            speed_l = 60
            speed_r = 60
            current_brightness = self.sensors.get_color().brightness()
            error = current_brightness - bwd
            d = error - prev_error
            intgr += error
            turn = (Kp * error + Kd * d + Ki * intgr) * 0.001
            prev_error = error

            if turn > 40:
                turn = 40
                speed_r = 50
            if turn < -40:
                turn = -40
                speed_l = 50

            self.motor_right.duty_cycle_sp = speed_r - turn
            self.motor_left.duty_cycle_sp = speed_l + turn
            self.motor_right.command = "run-direct"
            self.motor_left.command = "run-direct"

            motor_ticks.append((self.motor_left.position, self.motor_right.position))

            if self.sensors.has_barrier():
                # TODO better turning, might not find path if barrier in curve
                barrier_on_path = True
                self.sound.beep()
                self.turn(170)
                # the following part is for added Ki

                while abs(self.sensors.get_color().brightness() - black_brightness) > 50:
                    self.motor_right.speed_sp = -80
                    self.motor_left.speed_sp = 80
                    self.motor_right.command = "run-forever"
                    self.motor_left.command = "run-forever"

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
        total_sleep = (4.76698 / 360) * angle
        has_path = False

        self.motor_right.speed_sp = -200
        self.motor_left.speed_sp = 200
        self.motor_right.command = "run-forever"
        self.motor_left.command = "run-forever"

        for i in range(25):
            time.sleep(total_sleep / 25)
            if abs(self.sensors.get_color().brightness() - self.sensors.black.brightness()) < 50:
                has_path = True

        self.motor_right.stop()
        self.motor_left.stop()
        time.sleep(0.2)
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

        self.turn(40)

        # print(f"Scanned ways, result: {result_list}")
        return result_list

    def scan_ways_absolute(self) -> List[Direction]:
        relative_directions = self.scan_ways_relative()
        absolute_directions: List[Direction] = []

        for relative_direction in relative_directions:
            absolute_directions.append(Direction((relative_direction + self.position.direction) % 360))

        return absolute_directions

    def turn_to_way_relative(self, direction: Direction) -> None:
        #self.position.direction = Direction((self.position.direction + direction) % 360)

        angle = int(direction)

        if angle > 180:

            angle = angle - 20
            angle = -(360 - angle)
        else:
            angle = angle - 15

        self.turn(angle)

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

        self.smart_discovery.add_scan_result(self.position.point, possible_directions_absolute)
        better_direction = self.communication.send_path_select(
            Position(self.position.point, possible_directions_absolute[0]))

        if better_direction is not None:
            self.turn_to_way_absolute(better_direction)
        else:
            self.turn_to_way_absolute(possible_directions_absolute[0])

    def get_next_direction(self) -> Optional[Direction]:
        if self.target is not None:
            target_path = self.planet.shortest_path_points(self.position.point, self.target)
            if target_path is None or target_path == []:
                print("Target not reachable")
                selected_direction = self.smart_discovery.next_direction(self.position.point)
                if selected_direction is None:
                    print("Complete, everything discovered")
                    response = self.communication.send_exploration_completed("Färdsch!")
                    if response is not None:
                        print(f"From mothership: {response}")
                    else:
                        print("No response")
                    return None
            else:
                selected_direction = target_path[0].direction
                print(f"Direction to target: {selected_direction}")
        else:  # no target
            selected_direction = self.smart_discovery.next_direction(self.position.point)
            if selected_direction is None:
                print("Complete, everything discovered")
                response = self.communication.send_target_reached("Färdsch!")
                if response is not None:
                    print(f"From mothership: {response}")
                else:
                    print("No response")
                return None

        selected_position = Position(self.position.point, selected_direction)
        mothership_direction = self.communication.send_path_select(selected_position)
        print(f"{mothership_direction}")
        if mothership_direction is not None:
            print(f"Better direction form mothership: {mothership_direction}")
            selected_direction = mothership_direction

        print(f"Selected direction: {selected_direction}")
        return selected_direction

    def got_path_unveiled(self) -> None:
        unveiled_paths = self.communication.receive_path_unveiled()
        if unveiled_paths is not None:
            print("Paths unveiled:")
            print(unveiled_paths)
            for unveiled_path in unveiled_paths:
                self.planet.add_path_points(unveiled_path.start_position, unveiled_path.end_position,
                                            unveiled_path.path_weight)
                self.smart_discovery.add_discovered_path(unveiled_path.start_position, unveiled_path.end_position)

    def got_target(self) -> None:
        target_message = self.communication.receive_target()
        if target_message is not None:
            print(f"Target from mothership: {target_message}")
            self.target = target_message

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
        self.smart_discovery.mark_discovered(path_response.start_position.point,
                                             path_response.start_position.direction)
        self.smart_discovery.mark_discovered(path_response.end_position.point,
                                             path_response.end_position.direction)

        self.move_forward(4)
        #
        # Traget reached??
        #
        if self.target is not None and self.position.point == self.target:
            response = self.communication.send_target_reached("Daaaa")
            self.target = None
            if response:
                print(f"Response from mothership: {response}")
                return True

        self.got_path_unveiled()
        self.got_target()

        if not self.smart_discovery.is_discovered_point(self.position.point):
            res_scan_ways_absolute = self.scan_ways_absolute()
            try:
                res_scan_ways_absolute.remove(self.position.direction.turned())
            except:
                print("Error???")

            self.smart_discovery.add_scan_result(self.position.point, res_scan_ways_absolute)

        next_direction = self.get_next_direction()
        if next_direction is None:
            return True
        self.turn_to_way_absolute(next_direction)

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
