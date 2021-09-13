#!/usr/bin/env python3
import unittest.mock
import paho.mqtt.client as mqtt
import uuid

import planet
from src.communication import Communication
from planet import Position, Point


class TestRoboLabCommunication(unittest.TestCase):

    @unittest.mock.patch('logging.Logger')
    def setUp(self, mock_logger):
        """
        Instantiates the communication class
        """
        client_id = '229' + str(uuid.uuid4())  # Replace YOURGROUPID with your group ID
        self.client = mqtt.Client(client_id=client_id,  # Unique Client-ID to recognize our program
                                  clean_session=False,  # We want to be remembered
                                  protocol=mqtt.MQTTv311  # Define MQTT protocol version
                                  )

        # Initialize your data structure here
        self.communication = Communication(self.client, mock_logger, True)
        self.communication.planet = "Gromit"
        self.communication.topic = "comtest/229"
        self.communication.client.subscribe(self.communication.topic)
        self.correct = "Correct"
        self.incorrect = "Incorrect"

        # self.communication.client.subscribe("planet/Gromit/229")
        # self.communication.send_ready()

    # self.communication.client.unsubscribe("explorer/229")

        # self.communication.client.subscribe(self.test_topic)

        # self.planets = {
        #     "Gromit-M3": Position(Point(-1, 2), planet.Direction.NORTH),
        #     "Chadwick": Position(Point(1, 10), planet.Direction.NORTH),
        #     "Mehl-M1": Position(Point(3, 4), planet.Direction.WEST),
        #     "Cake": Position(Point(-12, -2), planet.Direction.EAST),
        #     "Candle": Position(Point(19, -2), planet.Direction.NORTH),
        #     "Caramel": Position(Point(1, -2), planet.Direction.NORTH),
        #     "Cheesecake": Position(Point(6, -2), planet.Direction.NORTH),
        #     "Cherry": Position(Point(6, -2), planet.Direction.NORTH),
        #     "Chia": Position(Point(-9, -1), planet.Direction.NORTH),
        #     "Chocolate": Position(Point(-12, -2), planet.Direction.EAST),
        #     "Cinnamon": Position(Point(23, -2), planet.Direction.EAST),
        #     "Citron": Position(Point(-3, -2), planet.Direction.SOUTH),
        #     "Coca": Position(Point(12, -2), planet.Direction.NORTH),
        #     "Coconut": Position(Point(0, 0), planet.Direction.NORTH),
        #     "Cookie": Position(Point(-6, -2), planet.Direction.NORTH),
        #     "Cream": Position(Point(15, -2), planet.Direction.NORTH),
        #     "Gromit-E": Position(Point(-2, 1), planet.Direction.NORTH),
        #     "Gromit-T": Position(Point(-1, -2), planet.Direction.NORTH),
        #     "Gromit-TT": Position(Point(-1, -2), planet.Direction.NORTH),
        #     "Gromit-W": Position(Point(2, -1), planet.Direction.WEST),
        #     "Gromit": Position(Point(-1, -2), planet.Direction.NORTH),
        #     "Mehl": Position(Point(3, 4), planet.Direction.WEST),
        #     "Reis": Position(Point(69, 69), planet.Direction.SOUTH),
        #     "Gromit-M1": Position(Point(-1, -2), planet.Direction.NORTH),
        #     "Gromit-M2": Position(Point(-1, -2), planet.Direction.NORTH),
        #     "Gromit-M3": Position(Point(-1, -2), planet.Direction.NORTH),
        #     "Fassaden-M1": Position(Point(5, 0), planet.Direction.NORTH),
        #     "Fassaden": Position(Point(5, 0), planet.Direction.NORTH),
        #     "Ibem": Position(Point(-1, 0), planet.Direction.NORTh),
        #     "Mebi": Position(Point(-1, 0), planet.Direction.NORTH),
        #     "Mebi-T20": Position(Point(-1, 0), planet.Direction.NORTH),
        #     "Kuehlelement": Position(Point(-14, -3), planet.Direction.EAST),
        #     "Boseman": Position(Point(6, 5), planet.Direction.SOUTH),
        #     "Anin": Position(Point(15, 2), planet.Direction.NORTH),
        #     "Nailik": Position(Point(17, 2), planet.Direction.NORTH),
        #     "Leinad": Position(Point(13, 2), planet.Direction.WEST),
        #
        # }

    def test_message_ready(self):
        """
        This test should check the syntax of the message type "ready"
        """
        self.communication.send_ready()
        confirmation_message = self.communication.get_first_response_by_type("syntax")["payload"] # from "explorer/229"
        print("Confirmation message: ", confirmation_message)

        # self.communication.client.publish(self.communication.topic, json.dumps(ready_msg)) # publish it to "comtest/229"
        # time.sleep(2)
        # dbg_payload = self.communication.get_first_response_by_type("syntax")["payload"]
        # self.assertEqual("Correct", dbg_payload["message"], "\"ready\" message contains formatting failure")

    def test_message_path(self):
        """
        This test should check the syntax of the message type "path"
        """

        # test on planet Gromit
        # self.communication.send_ready(self.communication.topic, self.communication.planet_topic)
        start_position = Position(Point(-1, -2), planet.Direction.NORTH)
        end_position = Position(Point(-1, -1), planet.Direction.SOUTH)
        is_blocked = False
        # time.sleep(3)
        self.communication.send_path(start_position, end_position, is_blocked)

    # client_message = self.communication.get_first_response_by_type("path")
        # self.communication.client.publish(self.dbg_topic, json.dumps(client_message))
        confirm_msg = self.communication.get_first_response_by_type("syntax")["payload"]
        print("Confirmation message ", confirm_msg)
        self.assertEqual(self.correct, confirm_msg["message"])

    def test_message_path_invalid(self):
        """
        This test should check the syntax of the message type "path" with errors/invalid data
        """
        start_position = Position(Point(-1, 1), planet.Direction.NORTH)
        end_position = Position(Point(-2, 2), planet.Direction.WEST)
        is_blocked = True

        self.communication.send_path(start_position, end_position, is_blocked)
        confirmation_msg = self.communication.get_first_response_by_type("syntax")
        self.assertEqual(self.correct, confirmation_msg["payload"]["message"])
        print("Received message: ", confirmation_msg)

    def test_message_select(self):
        """
        This test should check the syntax of the message type "pathSelect"
        """
        self.fail('implement me!')

    def test_message_complete(self):
        """
        This test should check the syntax of the message type "explorationCompleted" or "targetReached"
        """
        self.fail('implement me!')


if __name__ == "__main__":
    unittest.main()
