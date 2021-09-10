#!/usr/bin/env python3

# Attention: Do not import the ev3dev.ev3 module in this file
import json
import logging
import platform
import queue
import ssl
import re
import time
# Fix: SSL certificate problem on macOS
from dataclasses import dataclass
from typing import Any, Optional, List

import paho
import paho.mqtt.client as client
from planet import Position, Point, Direction

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

    def __init__(self, mqtt_client: client.Client, logger: logging.Logger, ) -> None:
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
        self.topic = 'explorer/229'
        self.planet = "planetWithNoName"
        self.client.username_pw_set('229', password='o4CzKPpAgl')  # Your group credentials
        self.client.connect('mothership.inf.tu-dresden.de', port=8883)
        self.client.subscribe(self.topic, qos=1)  # Subscribe to topic explorer/xxx
        self.client.subscribe("planet/" + self.planet + "/229")
        # self.client.loop_start()

        self.logger = logger
        self.que = queue.Queue()

    # DO NOT EDIT THE METHOD SIGNATURE
    def on_message(self, client: paho.mqtt.client.Client, data, message):
        """
        Handles the callback if any message arrived
        :param client: paho.mqtt.client.Client
        :param data: Object
        :param message: Object
        :return: void
        """
        payload = json.loads(message.payload.decode('utf-8'))
        self.logger.debug(json.dumps(payload, indent=2))
        self.que.put(message)
        # YOUR CODE FOLLOWS (remove pass, please!)
        # TODO
        
        # check msg content if type is "planet". If so call send ready

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
        self.client.publish(topic, message)

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

    ######################
    # Send to mothership #
    ######################

    def send_testplanet(self, planet_name: str) -> str:
        message = {
            "from": "client",
            "type": "testplanet",
            "payload": {
                "planetName": planet_name
            }
        }
        message_to_send = json.dumps(message, indent=2)
        self.send_message(self.topic, message_to_send)


        while not(self.que.empty()):
            received_msg = self.que.get(timeout=10)
            if received_msg["type"] == "notice":
                msg_contains_planet_name = received_msg["payload"]["message"]
                # use regex to extract planet name
                result = re.split('\\s', msg_contains_planet_name)
                return result[2]

    def send_ready(self) -> SendReadyResponse:
        ready_msg = {
            "from": "client",
            "type": "ready"
        }
        ready_msg = json.dumps(ready_msg, indent=2)
        self.send_message(self.topic, ready_msg)
        while not(self.que.empty()):
            message = json.load(self.que.get(timeout=10))
            if message["type"] == "planet":
                position = Position(message["payload"]["startX"], message["payload"]["startY"])
                ready_response = SendReadyResponse(message["payload"]["planetName"], position)
                return ready_response

        return None

    def send_path(self, start_position: Position, end_position: Position, path_blocked: bool) -> SendPathResponse:
        startx = start_position.point.x
        starty = start_position.point.y
        endx = end_position.point.x
        endy = end_position.point.y
        start_direction = start_position.direction
        end_direction = end_position.direction

        response = {
            "from": "client",
            "type": "path",
            "payload": {
                "startX": startx,
                "startY": starty,
                "startDirection": start_direction,
                "endX": endx,
                "endY": endy,
                "endDirection": end_direction,
                "pathStatus": "free"
            }
        }
        if path_blocked:
            response["payload"]["endX"] = startx
            response["payload"]["endY"] = starty
            response["payload"]["pathStatus"] = "blocked"
            response["payload"]["endDirection"] = start_direction
        topic = "planet/" + self.planet + "/229"
        response = json.dumps(response, indent=2)
        self.send_message(topic, response)
        return SendPathResponse(Position(Point(startx, starty), start_direction),
                                Position(Point(endx, endy), end_direction))

    def send_path_select(self, position: Position) -> Direction:
        msg = {
            "from": "client",
            "type": "pathSelect",
            "payload": {
                "startX": position.point.x,
                "startY": position.point.y,
                "startDirection": position.direction
            }
        }
        msg = json.dumps(msg, indent=2)
        #topic = "planet/" + self.planet + "/229"
        self.client.publish(self.topic, msg)
        while not(self.que.empty()):
            message = self.que.get()
            if message["type"] == "pathSelect":
                return Direction(int(message["payload"]["startDirection"]))

    def send_exploration_completed(self, text: str) -> bool:
        msg = {
            "from": "client",
            "type": "explorationCompleted",
            "payload": {
                "message": text
            }
        }
        msg = json.dumps(msg, indent=2)
        self.send_message(self.topic, msg)
        return self.current_mission_completed()

    def send_target_reached(self, text: str) -> bool:
        msg = {
            "from": "client",
            "type": "targetReached",
            "payload": {
                "message": text
            }
        }
        msg = json.dumps(msg, indent=2)
        self.send_message(self.topic, msg)
        return self.current_mission_completed()

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
    def vaidate_json(self, message: Any):
        try:
            json.dump(message, indent=2)
            return True
        except ValueError as err:
            self.send_message(self.topic, "JSON format error")
            return False

    def filter_messages_on_type(self, type: str) -> [dict]:
        result = []
        while self.que:
            msg = self.que.get()
            if msg["type"] is type:
                result.append(msg)
        return result

    def current_mission_completed(self) -> bool:
        while not(self.que.empty()):
            mothership_msg = self.que.get(timeout=10)
            if mothership_msg["type"] == "done":
                self.logger.debug("Mother ship: ".format(mothership_msg["payload"]["message"]))
                return True
        return False


    def on_connect(self, client):
        self.logger.debug("{}Connected to the broker".format(client))

    def on_disconnect(self, userdata, rc=0):
        logging.debug("DisConnected result code "+str(rc))
        self.client.loop_stop()

