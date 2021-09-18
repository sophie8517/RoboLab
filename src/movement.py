import time
from copy import deepcopy
from dataclasses import dataclass
from typing import List, Optional

from ev3dev import ev3
from ev3dev.core import Sound

from calibration import Calibration
from communication import Communication
from odometry import Odometry
from planet import Direction, Position, Planet, Point
from sensors import Sensors, SquareColor
from smart_discovery import SmartDiscovery


@dataclass
class FollowLineResult:
    dx: int
    dy: int
    relative_direction: Direction
    path_blocked: bool


class Movement:
    """Responsible class for moving the robot and the main logic"""

    def __init__(self, communication: Communication):
        self.communication = communication

        self.motor_right = ev3.LargeMotor("outD")
        self.motor_right.reset()
        self.motor_right.stop_action = "brake"
        self.motor_left = ev3.LargeMotor("outA")
        self.motor_left.reset()
        self.motor_left.stop_action = "brake"
        self.sound = ev3.Sound()
        Sound.set_volume(100)

        self.sensors = Sensors()
        self.calibration = Calibration(self.motor_left, self.motor_right, self.sensors)
        self.planet = Planet()
        self.odometry = Odometry()
        self.smart_discovery = SmartDiscovery(self.planet)

        self.position = Position(Point(-11, -11), Direction.NORTH)
        self.target: Optional[Point] = None

    def turn(self, angle: int) -> None:
        """Turns right an specified angle with the speed_sp of 200.
        A negative value will turn left."""
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

    def move_forward(self, time_seconds: int, speed: int = 50) -> None:
        """Moved the robot forward with specified time and speed."""
        self.motor_right.speed_sp = speed
        self.motor_left.speed_sp = speed

        self.motor_right.command = "run-forever"
        self.motor_left.command = "run-forever"

        time.sleep(time_seconds)

        self.motor_right.stop()
        self.motor_left.stop()

    def follow_line(self) -> FollowLineResult:
        """Follows a line and returning the result of the odometry and if there was a barrier."""
        self.motor_right.position = 0
        self.motor_left.position = 0
        motor_ticks = []

        bwd = self.sensors.black_white_diff
        speed = 50

        k_p = 252
        k_d = 85
        k_i = 4
        prev_error = 0
        intgr = 0
        speed_l = speed
        speed_r = speed

        black_brightness = self.sensors.black.brightness()

        barrier_on_path = False
        while True:
            speed_l = 50
            speed_r = 50
            current_brightness = self.sensors.get_color().brightness()
            error = current_brightness - bwd
            d = error - prev_error
            intgr += error
            turn = (k_p * error + k_d * d + k_i * intgr) * 0.001
            prev_error = error

            if turn > 50:
                turn = 45
                speed_r = 40
                speed_l = 45
            if turn < -50:
                turn = -45
                speed_l = 40
                speed_r = 45

            self.motor_right.duty_cycle_sp = speed_r - turn
            self.motor_left.duty_cycle_sp = speed_l + turn
            self.motor_right.command = "run-direct"
            self.motor_left.command = "run-direct"

            motor_ticks.append((self.motor_left.position, self.motor_right.position))

            if self.sensors.has_barrier():
                # TODO better turning, might not find path if barrier in curve
                barrier_on_path = True
                self.sound.beep()
                self.turn(45)

                while abs(self.sensors.get_color().brightness() - black_brightness) > 50:
                    self.motor_right.speed_sp = -80
                    self.motor_left.speed_sp = 80
                    self.motor_right.command = "run-forever"
                    self.motor_left.command = "run-forever"

            if self.sensors.get_square_color() != SquareColor.NOT_ON_SQUARE:
                self.motor_right.stop()
                self.motor_left.stop()

                # filename = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                # with open(f"/home/robot/{filename}.json", "w") as file:
                #     file.write(json.dumps(motor_ticks))

                odometry_result = self.odometry.calc(motor_ticks)
                result = FollowLineResult(odometry_result.dx, odometry_result.dy, odometry_result.direction,
                                          barrier_on_path)
                return result

    def turn_and_scan(self) -> bool:
        """Turns ca. 90 degrees and return true if there was a line."""
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
        return has_path

    def scan_ways(self) -> List[Direction]:
        """Calls scan_ways_absolute and calculates absolute directions."""
        self.turn(-45)
        relative_directions: List[Direction] = []

        if self.turn_and_scan():
            relative_directions.append(Direction.NORTH)

        if self.turn_and_scan():
            relative_directions.append(Direction.EAST)

        if self.turn_and_scan():
            relative_directions.append(Direction.SOUTH)

        if self.turn_and_scan():
            relative_directions.append(Direction.WEST)

        self.turn(40)

        absolute_directions: List[Direction] = []

        for relative_direction in relative_directions:
            absolute_directions.append(Direction((relative_direction + self.position.direction) % 360))

        return absolute_directions

    def turn_to_way(self, direction_absolute: Direction) -> None:
        print(f"{direction_absolute=}")
        """Turns to an absolute direction."""

        direction_relative = Direction((direction_absolute - self.position.direction) % 360)

        self.position.direction = direction_absolute

        print(f"{self.position.direction=}")

        print(f"{direction_relative=}")

        angle = int(direction_relative)

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

    def initial_start(self) -> None:
        """Should by called once to drive to first point.
        Sends ready message and scans first point."""
        self.calibration.calibrate_colors()

        black_brightness = self.sensors.black.brightness()
        while abs(self.sensors.get_color().brightness() - black_brightness) > 50:
            self.motor_right.speed_sp = -80
            self.motor_left.speed_sp = 80
            self.motor_right.command = "run-forever"
            self.motor_left.command = "run-forever"

        self.follow_line()
        self.move_forward(1, speed=200)

        ready_response = self.communication.send_ready()

        if not ready_response:
            raise Exception("No response from mothership (ready message sent)")

        self.planet.name = ready_response.planet_name
        self.communication.client.subscribe(f"planet/{self.planet.name}/229")
        self.communication.planet = self.planet.name
        self.position = ready_response.start_position
        print(f"{self.planet.name=}")
        print(f"{self.position=}")

        possible_directions_absolute = self.scan_ways()

        # don't add start line, which would go into the void
        possible_directions_absolute.remove(self.position.direction.turned())

        if not possible_directions_absolute:
            raise Exception("No possible directions")

        self.smart_discovery.add_scan_result(self.position.point, possible_directions_absolute)
        better_direction = self.communication.send_path_select(
            Position(self.position.point, possible_directions_absolute[0]))

        if better_direction is not None:
            self.turn_to_way(better_direction)
        else:
            self.turn_to_way(possible_directions_absolute[0])

    def get_next_direction(self) -> Optional[Direction]:
        """Calculate next direction. If there is a reachable target return direction to target.
        If no reachable target, return direction to closest undiscovered path.
        Returns None, if everything is discovered."""

        if self.target is not None:  # there is a target
            target_path = self.planet.shortest_path_points(self.position.point, self.target)
            if target_path is None or target_path == []:  # target not reachable
                print("Target not reachable")
            else:  # target reachable -> return direction
                return target_path[0].direction

        # no reachable target -> next direction from smart discovery
        return self.smart_discovery.next_direction(self.position.point)

    def got_path_unveiled(self) -> None:
        """Checks if we got path unveiled messages.
        If we got some, save them in planet and smart discovery."""
        unveiled_paths = self.communication.receive_path_unveiled()
        if unveiled_paths is not None:
            for unveiled_path in unveiled_paths:
                self.planet.add_path_points(unveiled_path.start_position, unveiled_path.end_position,
                                            unveiled_path.path_weight)
                self.smart_discovery.add_discovered_path(unveiled_path.start_position, unveiled_path.end_position)

    def got_target(self) -> None:
        """Checks if we got a target message.
        If we got one, set this as new target."""
        target_message = self.communication.receive_target()
        if target_message is not None:
            print(f"Target from mothership: {target_message}")
            self.target = target_message

    def do_follow_line_update_position(self) -> None:
        """Follows a line and updated position based on odometry result.
        Sends this position to mothership and checks for mothership correction.
        Add the (corrected) path to planet and smart_discovery."""
        follow_line_result = self.follow_line()

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

    def main_loop(self) -> bool:
        """Follow line, scan paths, communicate, move to next direction.
        Returns True, if done."""
        self.do_follow_line_update_position()

        self.move_forward(1, 200)
        #
        # Traget reached??
        #
        if self.target is not None and self.position.point == self.target:

            Sound.play('/home/robot/smb_stage_clear.wav').wait()
            response = self.communication.send_target_reached("Daaaa")
            self.target = None
            if response:
                print(f"Response from mothership: {response}")
                return True

        self.got_path_unveiled()
        self.got_target()

        if not self.smart_discovery.is_discovered_point(self.position.point):
            Sound.play('/home/robot/smb_coin.wav').wait()
            res_scan_ways_absolute = self.scan_ways()
            try:
                res_scan_ways_absolute.remove(self.position.direction.turned())
            except:
                print("Error???")

            self.smart_discovery.add_scan_result(self.position.point, res_scan_ways_absolute)

        next_direction = self.get_next_direction()
        print(f"{next_direction=}")
        if next_direction is None:
            print("Complete, everything discovered")
            Sound.play('/home/robot/smb_stage_clear.wav').wait()
            response = self.communication.send_exploration_completed("Färdsch!")
            if response is not None:
                print(f"From mothership: {response}")
            else:
                print("No response")
            return True

        mothership_direction = self.communication.send_path_select(Position(self.position.point, next_direction))
        if mothership_direction is not None:
            print(f"Better direction form mothership: {mothership_direction}")
            next_direction = mothership_direction

        self.turn_to_way(next_direction)

        # time.sleep(3)
        Sound.tone(1000, 100).wait()

        self.got_path_unveiled()
        self.got_target()

        return False

    def main(self) -> None:
        """Entry point into movement."""
        self.initial_start()
        done = False
        while not done:
            done = self.main_loop()
        print("---- DONE ----")
