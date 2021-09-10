#!/usr/bin/env python3

# Attention: Do not import the ev3dev.ev3 module in this file
import json
import logging
import platform
import queue
import ssl
import time
import uuid
from dataclasses import dataclass
from typing import Any, Optional, List

import paho.mqtt.client as mqtt

from planet import Position, Point, Direction

# Fix: SSL certificate problem on macOS
if all(platform.mac_ver()):
    from OpenSSL import SSL


@dataclass
class SendPathResponse:
    start_position: Position
    end_position: Position
    path_blocked: bool
    path_weight: int


@dataclass
class SendReadyResponse:
    planet_name: str
    start_position: Position


@dataclass
class PathUnveiledResponse:
    start_position: Position
    end_position: Position
    path_blocked: bool
    path_weight: int


class Communication:
    """
    Class to hold the MQTT client communication
    Feel free to add functions and update the constructor to satisfy your requirements and
    thereby solve the task according to the specifications
    """

    def __init__(self, mqtt_client: mqtt.Client, logger: logging.Logger) -> None:
        """
        Initializes communication module, connect to server, subscribe, etc.
        :param mqtt_client: paho.mqtt.client.Client
        :param logger: logging.Logger
        """
        # DO NOT CHANGE THE SETUP HERE
        self.client = mqtt_client
        self.client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        self.client.on_message = self.safe_on_message_handler
        # Add your client setup here
        self.group = 229
        self.topic = f'explorer/{self.group}'
        self.planet = "planetWithNoName"
        self.client.username_pw_set(self.group, password='o4CzKPpAgl')  # Your group credentials
        self.client.connect('mothership.inf.tu-dresden.de', port=8883)
        self.client.subscribe(self.topic, qos=1)  # Subscribe to topic explorer/xxx
        # self.client.subscribe(f"planet/{self.planet}/229")
        self.client.loop_start()

        self.logger = logger
        self.que = queue.Queue()

    # DO NOT EDIT THE METHOD SIGNATURE
    def on_message(self, client: mqtt.Client, data, message):
        """
        Handles the callback if any message arrived
        :param client: paho.mqtt.client.Client
        :param data: Object
        :param message: Object
        :return: void
        """
        payload = json.loads(message.payload.decode('utf-8'))
        self.logger.debug(json.dumps(payload, indent=2))
        # YOUR CODE FOLLOWS (remove pass, please!)

        if payload["from"] != "server":
            return
        self.que.put(payload)

    # DO NOT EDIT THE METHOD SIGNATURE
    #
    # In order to keep the logging working you must provide a topic string and
    # an already encoded JSON-Object as message.
    def send_message(self, topic: str, message: Any) -> None:
        """
        Sends given message to specified channel
        :param topic: String
        :param message: Object
        :return: void
        """

        self.logger.debug('Send to: ' + topic)
        self.logger.debug(json.dumps(message, indent=2))

        # YOUR CODE FOLLOWS (remove pass, please!)
        self.client.publish(topic, json.dumps(message))

    # DO NOT EDIT THE METHOD SIGNATURE OR BODY
    #
    # This helper method encapsulated the original "on_message" method and handles
    # exceptions thrown by threads spawned by "paho-mqtt"
    def safe_on_message_handler(self, client, data, message):
        """
        Handle exceptions thrown by the paho library
        :param client: paho.mqtt.client.Client
        :param data: Object
        :param message: Object
        :return: void
        """
        try:
            self.on_message(client, data, message)
        except:
            import traceback
            traceback.print_exc()
            raise

    @property
    def planet_topic(self):
        if not self.planet:
            raise Exception("No planet name")
        return f"planet/{self.planet}/{self.group}"

    ######################
    # Send to mothership #
    ######################

    def send_testplanet(self, planet_name: str) -> None:
        msg = {
            "from": "client",
            "type": "testplanet",
            "payload": {
                "planetName": planet_name
            }
        }
        self.send_message(self.topic, msg)

    def send_ready(self) -> SendReadyResponse:
        message = {
            "from": "client",
            "type": "ready"
        }
        self.send_message(self.topic, message)

        time.sleep(1)

        response = self.que.get(timeout=10)
        if response["type"] != "planet":
            raise Exception("Invalid mothership response")

        payload = response["payload"]

        position = Position(Point(payload["startX"], payload["startY"]), Direction(payload["startOrientation"]))
        ready_response = SendReadyResponse(payload["planetName"], position)
        return ready_response

    def send_path(self, start_position: Position, end_position: Position, path_blocked: bool) -> SendPathResponse:
        if path_blocked:
            path_status = "blocked"
        else:
            path_status = "free"

        message = {
            "from": "client",
            "type": "path",
            "payload": {
                "startX": start_position.point.x,
                "startY": start_position.point.y,
                "startDirection": start_position.direction,
                "endX": end_position.point.x,
                "endY": end_position.point.y,
                "endDirection": end_position.direction,
                "pathStatus": path_status
            }
        }
        self.send_message(self.planet_topic, message)

        time.sleep(1)

        response = self.que.get(timeout=10)

        if response["type"] != "path":
            raise Exception("Invalid mothership response")

        payload = response["payload"]

        start_position_response = Position(Point(payload["startX"], payload["startY"]),
                                           Direction(payload["startDirection"]))
        end_position_response = Position(Point(payload["endX"], payload["endY"]), Direction(payload["endDirection"]))
        if payload["pathStatus"] == "free":
            path_blocked = False
        else:
            path_blocked = True
        path_weight = payload["pathWeight"]
        return SendPathResponse(start_position_response, end_position_response, path_blocked, path_weight)

    def send_path_select(self, position: Position) -> Direction:
        message = {
            "from": "client",
            "type": "pathSelect",
            "payload": {
                "startX": position.point.x,
                "startY": position.point.y,
                "startDirection": position.direction
            }
        }
        self.client.publish(self.planet_topic, message)

        time.sleep(1)

        response = self.que.get(timeout=10)

        if response["type"] != "pathSelect":
            raise Exception("Invalid mothership response")

        return Direction(response["payload"]["startDirection"])

    def send_target_reached(self, text: str) -> None:
        message = {
            "from": "client",
            "type": "targetReached",
            "payload": {
                "message": text
            }
        }
        self.send_message(self.topic, message)

        time.sleep(1)

        response = self.que.get(timeout=10)
        self.que.

        if response["type"] != "done":
            raise Exception("Invalid mothership response")

    def send_exploration_completed(self, text: str) -> None:
        message = {
            "from": "client",
            "type": "explorationCompleted",
            "payload": {
                "message": text
            }
        }
        self.send_message(self.topic, message)

        time.sleep(1)

        response = self.que.get(timeout=10)

        if response["type"] != "done":
            raise Exception("Invalid mothership response")

    ###########################
    # Receive from mothership #
    ###########################

    def receive_path_unveiled(self) -> List[PathUnveiledResponse]:
        paths_messages = self.filter_messages_on_type("pathUnveiled")
        paths_unveiled = []
        for msg in paths_messages:
            payload = msg["payload"]
            path = PathUnveiledResponse(Position(Point(payload["startX"],
                                                       payload["startY"]),
                                                 payload["startDirection"]),
                                        Position(Point(payload["endX"],
                                                       payload["endY"]),
                                                 payload["endDirection"]),
                                        payload["pathStatus"],
                                        payload["pathWeight"])
            paths_unveiled.append(path)
        return paths_unveiled

    def receive_target(self) -> Optional[Point]:

        target = self.filter_messages_on_type("target")[0]
        if target:
            point = Point(target["payload"]["targetX"], target["payload"]["targetY"])
            return point
        return None

    #########################
    # helper method         #
    #########################
    def filter_messages_on_type(self, type: str) -> [dict]:
        result = []
        while self.que:
            msg = self.que.get()
            if msg["type"] is type:
                result.append(msg)
        return result


if __name__ == '__main__':
    logger = logging.getLogger('RoboLab')
    client_id = '229-' + str(uuid.uuid4())  # Replace YOURGROUPID with your group ID
    client = mqtt.Client(client_id=client_id,  # Unique Client-ID to recognize our program
                         clean_session=True,  # We want a clean session after disconnect or abort/crash
                         protocol=mqtt.MQTTv311  # Define MQTT protocol version
                         )

    c = Communication(client, logger)
    print(c.send_ready())
