#!/usr/bin/env python3

# Attention: Do not import the ev3dev.ev3 module in this file
import json
import logging
import platform
import queue
import ssl

# Fix: SSL certificate problem on macOS
from dataclasses import dataclass
from typing import Any, Optional, List

import paho.mqtt.client

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

    def __init__(self, mqtt_client: paho.mqtt.client.Client, logger: logging.Logger,) -> None:
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
        self.planet: str
        self.client.username_pw_set('229', password='o4CzKPpAgl')  # Your group credentials
        self.client.connect('mothership.inf.tu-dresden.de', port=8883)
        self.client.subscribe(self.topic, qos=1)  # Subscribe to topic explorer/xxx
        self.client.loop_start()

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
        # TODO?
        self.que.put(message)

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

    def send_testplanet(self, planet_name: str) -> None:
        # TODO
        message = {
            "from": "client",
            "type": "testplanet",
            "payload": {
                "planetName": planet_name
            }
        }
        message_to_send = json.dumps(message, indent=2)
        self.send_message(self.topic, message_to_send)

    def send_ready(self) -> SendReadyResponse:
        ready_msg = {
            "from": "client",
            "type": "ready"
        }
        message = json.load(self.que.get(timeout=10))
        if message["type"] == "planet":
            ready_msg = json.dumps(ready_msg, indent=2)
            self.send_message(self.topic, ready_msg)
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
                        "startX": startx ,
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
        return SendPathResponse(Position(Point(startx, starty), start_direction), Position(Point(endx, endy), end_direction))

    def send_path_select(self, position: Position) -> Direction:
        #TODO
        pass

    def send_exploration_completed(self, text: str) -> None:
        # TODO
        pass

    def send_target_reached(self, text: str) -> None:
        # TODO
        pass

    ###########################
    # Receive from mothership #
    ###########################

    def receive_path_unveiled(self) -> List[PathUnveiledResponse]:
        # TODO
        pass

    def receive_target(self) -> Optional[Point]:
        # TODO
        pass
