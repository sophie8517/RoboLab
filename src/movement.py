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

        self.position: Position

    def turn(self, angle: int) -> None:
        # print(f"Turn {angle} degrees...")
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
        time.sleep((4.76698 / 360) * abs(angle)) # 9.5, 9.445, 9.45, 9.502,  9.4426
        #4.780062796999118, 4.761925176000659, 4,758945233999839
        #mittelwert = 4.766977735666539
        self.motor_right.stop()
        self.motor_left.stop()
        # print("Turned")

    def test(self) -> float:
        t = time.perf_counter()
        while True:
            try:
                self.motor_right.speed_sp = -200
                self.motor_left.speed_sp = 200
                self.motor_right.command = "run-forever"
                self.motor_left.command = "run-forever"
            except KeyboardInterrupt:
                t2 = time.perf_counter()
                break

        self.motor_left.stop()
        self.motor_right.stop()
        t3 = t2 - t
        print(f'difference: {t3}')
        return t3



    def move_forward(self, time_sec: int, speed: int = 50) -> None:
        # print(f"Move forward: time_sec:{time_sec}, speed={speed}...")
        self.motor_right.speed_sp = speed
        self.motor_left.speed_sp = speed

        self.motor_right.command = "run-forever"
        self.motor_left.command = "run-forever"

        time.sleep(time_sec)

        self.motor_right.stop()
        self.motor_left.stop()
        # print("Moved forward")

    def follow_line(self, speed) -> FollowLineResult:
        self.motor_right.position = 0
        self.motor_left.position = 0
        motor_ticks = []
        

        #testen: 280, 120, 30
        #noch nicht: speed 280, Kp 140, Kd 10
        #verbessern: speed 280, Kp 140, Kd 20
        bwd = self.sensors.black_white_diff
        speed = 280  #180  200  180  200  240  280
        Kp = p_v     #110  120  100  100  120  160
        Kd = d_v     #  8    8   10   10   10   5
        prev_error = 0


        # print("Following line...")
        barrier_on_path = False
        while True:
            current_brightness = self.sensors.get_color().brightness()
            error = current_brightness - bwd
            d = error - prev_error
            turn = (Kp * error + Kd * d) * 0.01

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

    def follow_line4(self,p, d_v, i) -> FollowLineResult:
        self.motor_right.position = 0
        self.motor_left.position = 0
        motor_ticks = []
        #testen: 280, 120, 30
        #noch nicht: speed 280, Kp 140, Kd 10
        #verbessern: speed 280, Kp 140, Kd 20
        bwd = self.sensors.black_white_diff
        speed = 60
        #speed 40, Kp 210, Kd 80
        #speed 40, Kp 240, Kd 80
        #speed 55, Kp 300, Kd 150
        #speed 55, Kp 280, Kd 160
        #speed 50, Kp 250, Kd 80, Ki 5
        #speed 55, Kp 250, Kd 80, Ki 2
        #speed 55, Kp 250, Kd 130
        # 230 70 2 bei speed 60 -> funktioniert gut mit setzen von speed_l und speed_r
        # 260 120 0 bei speed 55


        Kp = p
        Kd = d_v
        Ki = i
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
                #the following part is for added Ki

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
        print("Turn and scan...")
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

        print(f'Scanned ways, result: {result_list}')
        return result_list

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
        direction_relative = Direction((direction_absolute - self.position.direction) % 360)
        self.turn_to_way_relative(direction_relative)

    def main_loop(self):

       self.calibration.calibrate_colors()
        r = 'y'
        while r == 'y':
            x = int(input("Kp: "))
            y = int(input("Kd: "))
            z = int(input("Ki: "))
            print(f'Kp = {x}, Kd = {y}, Ki = {z}')
            self.follow_line4(x,y,z)
            r = input("nochmal[y/n]?: ")


        '''
        
        print("Send ready message")
        ready_response = self.communication.send_ready()
        self.planet.name = ready_response.planet_name
        self.communication.client.subscribe(f"planet/{self.planet.name}/229")
        self.communication.planet = self.planet.name
        self.position = ready_response.start_position
        self.discovery = SmartDiscovery(self.position, self.planet)
        print(f"Planet Name: {self.planet.name}")
        print(f"{self.position}")

        possible_paths = self.scan_ways()
        possible_paths_absolute = []
        for i in possible_paths:
            possible_paths_absolute.append(Direction((i + self.position.direction) % 360))
        #self.discovery.add_possible_directions(self.possible_paths)
        self.planet.undiscovered_paths(self.position.point, possible_paths_absolute)
        self.paths_list = self.discovery.get_next_direction()
        

        while True:
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

            print(f"{self.position}")
            self.discovery.position = self.position

            send_path_response = self.communication.send_path(old_position, self.position.turned(),
                                                              follow_line_result.path_blocked)
            self.planet.add_path_points(send_path_response.start_position, send_path_response.end_position,
                                        send_path_response.path_weight)

            self.planet.remove_undiscovered_paths(send_path_response.start_position.point, send_path_response.start_position.direction)
            self.planet.remove_undiscovered_paths(send_path_response.end_position.point, send_path_response.end_position.direction)

            self.paths_list.remove(send_path_response.start_position)


            self.move_forward(4)

            res_scan_ways = self.scan_ways()
            res_scan_ways_absolute = []
            for i in res_scan_ways:
                res_scan_ways_absolute.append(Direction((i + self.position.direction) % 360))

            self.planet.undiscovered_paths(self.position.point, res_scan_ways_absolute)

            selected_direction = 0

            # TODO smart path selection
            if self.paths_list == []:
                self.paths_list = self.discovery.get_next_direction()
                selected_direction = self.paths_list[0].direction
            else:
                selected_direction = self.paths_list[0].direction







            #selected_direction_absolute = Direction((selected_direction_relative + self.position.direction) % 360)
            selected_position = Position(self.position.point, selected_direction)
            send_path_select_response = self.communication.send_path_select(selected_position)
            if send_path_select_response:
                print(f"Better direction form mothership: {send_path_select_response}")
                self.turn_to_way_absolute(send_path_select_response)
            else:
                print(f'selected direction: {selected_direction}')
                self.turn_to_way_absolute(selected_direction)

        '''


        #res_scan_ways = self.scan_ways()


    def main(self):
        while True:
            try:
                self.main_loop()
                print("---- DONE ----")
                self.debug_server.start()

            except KeyboardInterrupt:
                print("---- KEYBOARD INTERRUPT ----")
                self.debug_server.start()
            except Exception as e:
                print("---- ERROR ----")
                traceback.print_exc()
                self.debug_server.start()
