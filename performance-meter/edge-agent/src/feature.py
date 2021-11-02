import asyncio
import json
import logging
import random

import paho
import requests
import stomper
import time
from websocket._core import create_connection

from commands import DittoCommand, DittoResponse, MeasurementData
from device_info import DeviceInfo


class Feature:

    def __init__(self, name, version, feature_id, mqtt_client: paho.mqtt.client.Client, device_info: DeviceInfo):
        """
        Create a new Feature for being present on the respective device thing.

        :param name: Name of the feature
        :param version: Version information
        :param feature_id: The id to be used
        :param mqtt_client: A connected MQTT-client
        :param device_info: Registration information
        """

        self.name = name
        self.version = version
        self.featureId = feature_id
        self.__mqttClient = mqtt_client
        self.__deviceInfo = device_info

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4,
                          skipkeys=['__mqttClient', '__deviceInfo'])

    def register(self):
        """Registers this as a feature in IoT-THings
    
        Parameters
        ----------
        mqtt_client : paho.mqtt.client
            The mqtt client that has the connection to the local mosquitto provided by the edge device.
        device_info : DeviceInfo
            Information of this device in the context of its subscription.
        """

        ditto_rsp_topic = "{}/{}/things/twin/commands/modify".format(self.__deviceInfo.namespace,
                                                                     self.__deviceInfo.deviceId)
        value = {
            "definition": ["org.example:PerformanceTest:2.0.0"],
            "properties": {
                "status": {
                    "agentName": self.name,
                    "agentVersion": self.version
                }
            }
        }
        path = "/features/" + self.featureId
        rsp = DittoResponse(ditto_rsp_topic, path, None)

        rsp.value = value
        self.__mqttClient.publish("e", rsp.to_json(), qos=1)

    def acknowledge(self, command: DittoCommand):
        if command.response_required():
            mosquitto_topic = "command///res/" + str(command.get_request_id()) + "/200"
            self.__mqttClient.publish(mosquitto_topic, command.get_response().to_json())
            print("======== Acknowledgement sent on topic " + mosquitto_topic + " =============")

    def handle(self, command: DittoCommand):
        """Handles a DittoCommand"""
        if self.featureId != command.featureId:
            print("Not matching feature ID: {}".format(command.featureId))
            return

        self.acknowledge(command)

        count = command.value.get('count', 100)
        delay_in_sec = command.value.get('delay', 0) / 1000
        request_id = command.value.get('id')
        response_url = command.value.get('responseUrl')

        print("Sending {} events with a delay of {} seconds".format(count, delay_in_sec))
        if response_url and response_url.startswith('ws://'):
            asyncio.get_event_loop().run_until_complete(
                self.respond_using_ws(command, count, delay_in_sec, request_id, response_url))
        elif response_url:
            self.respond_using_rest(command, count, delay_in_sec, request_id, response_url)
        elif command.dittoTopic.endswith("live/messages/start"):
            self.respond_using_events(command, count, delay_in_sec, request_id)
        elif command.path.endswith("properties/status/request") and (
                command.mqttTopic == "command///req//modified" or command.mqttTopic == "command///req//created"):
            self.respond_using_feature(command, count, delay_in_sec, request_id)

    def respond_using_feature(self, command: DittoCommand, count, delay_in_sec, request_id):
        print("Responding using feature update")
        ditto_rsp_topic = "{}/{}/things/twin/commands/modify".format(self.__deviceInfo.namespace,
                                                                     self.__deviceInfo.deviceId)
        for i in range(count):
            event = {
                # 'topic': command.dittoTopic,
                'topic': ditto_rsp_topic,
                'path': "/features/{}/properties/status/response".format(command.featureId),
                'headers': {
                    "response-required": False,
                    "content-type": "application/json"
                },
                'value': MeasurementData(request_id, count, i).__dict__
            }
            if i == count - 1:
                print("Sending {}".format(json.dumps(event)))
            time.sleep(delay_in_sec)
            self.__mqttClient.publish('e', json.dumps(event), qos=1)

    def respond_using_events(self, command: DittoCommand, count, delay_in_sec, request_id):
        print("Responding using events")
        resp_headers = command.value.get('responseHeaders', {
            "response-required": False,
            "content-type": "application/json",
            "correlation-id": "dont-care",
        })

        resp_subject = 'meter.event.response';
        resp_path = "/features/{}/outbox/messages/{}".format(command.featureId, resp_subject)
        print("Expected response message count = {}, headers={}, request id = {} "
              .format(count, resp_headers, request_id))

        for i in range(count):
            event = {
                # 'topic': command.dittoTopic,
                'topic': self.__deviceInfo.namespace + "/" + self.__deviceInfo.deviceId + "/things/live/messages/" + resp_subject,
                'path': resp_path,
                'headers': resp_headers,
                'value': MeasurementData(request_id, count, i).__dict__
            }
            if i == count - 1:
                print("Sending {}".format(json.dumps(event)))
            time.sleep(delay_in_sec)
            self.__mqttClient.publish('t', json.dumps(event), qos=1)

    @staticmethod
    def get_message(request_id, count, no):
        return {
            'id': request_id,
            'expected': count,
            'current': no
        }

    @staticmethod
    def respond_using_rest(command: DittoCommand, count, delay_in_sec, request_id, response_url):
        print("Responding over url= {}; delay= {}ms".format(response_url, delay_in_sec))
        for i in range(count):
            post_data = MeasurementData(request_id, count, i)
            requests.post(response_url, data=post_data.to_json(), headers={
                'Content-type': 'application/json'
            })

    @staticmethod
    async def respond_using_ws(command: DittoCommand, count, delay_in_sec, request_id, response_url):
        logging.info("Responding over url= %s; delay= %s ms", response_url, delay_in_sec)
        ws = create_connection(response_url)

        idx = str(random.randint(0, 1000))
        sub = stomper.subscribe("/data", idx, ack='auto')
        ws.send(sub)
        for i in range(count):
            post_data = MeasurementData(request_id, count, i)
            time.sleep(delay_in_sec)
            msg = stomper.send(dest="/app/data", msg=post_data.to_json(), content_type="application/json")
            logging.debug("Going to send stomp message: %s", msg)
            ws.send(msg)
            # ws.send("some trash")
            # await ws.send(post_data.to_json())
            # await ws.recv()

        ws.send(stomper.unsubscribe(idx))
