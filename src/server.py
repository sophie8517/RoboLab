import socket

import ev3dev.core


class DebugServer:
    def __init__(self, motor_left: ev3dev.core.LargeMotor, motor_right: ev3dev.core.LargeMotor):
        self.motor_left = motor_left
        self.motor_right = motor_left

    def start(self):
        print("Starting server")
        self.motor_right.stop()
        self.motor_left.stop()
        port = 65432

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind(('', port))
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
