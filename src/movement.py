import time
from dataclasses import dataclass
import socket
from typing import List

from ev3dev import ev3

from communication import Communication
from planet import Direction
from sensors import Sensors, SquareColor, Color


@dataclass
class FollowLineResult:
    dx: int
    dy: int
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

    def calibrate_red_blue(self) -> None:
        input("Set me on a blue square and press enter")
        self.sensors.blue = self.sensors.get_color()
        input("Set me on a red square and press enter")
        self.sensors.red = self.sensors.get_color()

        print(f"self.sensors.red = {self.sensors.red}")
        print(f"self.sensors.blue = {self.sensors.blue}")

    def calibrate_black_white(self) -> None:
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

    def turn(self, angle: int):
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

    def move_forward(self, time_sec: int, speed: int = 50):
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
        print("Following line...")
        barrier_on_path = False
        while True:
            current_brightness = self.sensors.get_color().brightness()
            turn = 0.2 * (current_brightness - self.sensors.black_white_diff)
            self.motor_right.speed_sp = speed - turn
            self.motor_left.speed_sp = speed + turn
            self.motor_right.command = "run-forever"
            self.motor_left.command = "run-forever"

            if self.sensors.has_barrier():
                # TODO better turning, might not find path if barrier in curve
                barrier_on_path = True
                self.sound.beep()
                self.turn(170)

            if self.sensors.get_square_color() != SquareColor.NOT_ON_SQUARE:
                self.motor_right.stop()
                self.motor_left.stop()
                result = FollowLineResult(1, 1, barrier_on_path)
                print(f"Followed line with result: {result}")
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

    def start_server(self):
        print("Starting server")
        self.motor_right.stop()
        self.motor_left.stop()
        PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('', PORT))
            while True:
                data: str = s.recv(1024).decode()
                print(f"Got socket data: {data}")
                if data == 's':
                    self.motor_right.stop()
                    self.motor_left.stop()
                elif data.startswith('f#'):
                    speed = int(data.split('#')[1])
                    self.motor_right.speed_sp = speed
                    self.motor_left.speed_sp = speed
                    self.motor_right.command = "run-forever"
                    self.motor_left.command = "run-forever"
                elif data.startswith('b#'):
                    speed = int(data.split('#')[1])
                    self.motor_right.speed_sp = -speed
                    self.motor_left.speed_sp = -speed
                    self.motor_right.command = "run-forever"
                    self.motor_left.command = "run-forever"
                elif data.startswith('l#'):
                    speed = int(data.split('#')[1])
                    self.motor_right.speed_sp = speed
                    self.motor_left.speed_sp = -speed
                    self.motor_right.command = "run-forever"
                    self.motor_left.command = "run-forever"
                elif data.startswith('r#'):
                    speed = int(data.split('#')[1])
                    self.motor_right.speed_sp = -speed
                    self.motor_left.speed_sp = speed
                    self.motor_right.command = "run-forever"
                    self.motor_left.command = "run-forever"
                elif data == 'restart':
                    self.motor_right.stop()
                    self.motor_left.stop()
                    return


    def main_loop(self):
        while True:
            try:
                # self.calibrate_black_white()
                self.sensors.white = Color(r=286, g=451, b=289)
                self.sensors.black = Color(r=31, g=69, b=22)

                # self.calibrate_red_blue()
                self.sensors.red = Color(r=142, g=57, b=23)
                self.sensors.blue = Color(r=34, g=158, b=138)

                # self.communication.send_ready()

                res_follow_line = self.follow_line()

                self.move_forward(4)

                res_scan_ways = self.scan_ways()
            except KeyboardInterrupt:
                self.start_server()
            except Exception as e:
                self.start_server()

            # while True:
            #    self.follow_line()
            #   self.scan_ways()
            # send ready message to mothership

            # follow line
            # find all paths on edge
            # send position to mothership
            #
            print("done")
            self.start_server()
