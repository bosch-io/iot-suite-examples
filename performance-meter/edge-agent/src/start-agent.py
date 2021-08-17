import argparse
import json
import logging
import re

import paho
import paho.mqtt.client as mqtt

from commands import DittoCommand
# from commands import MeasurementData
from device_info import DeviceInfo
# from ditto_response import DittoResponse
from feature import Feature

deviceInfo = None
meter_feature = None
DEVICE_INFO_TOPIC = "edge/thing/response"
MQTT_TOPIC = [(DEVICE_INFO_TOPIC, 0), ("command///req/#", 0)]


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing to a topic that sends install or download command
    client.subscribe(MQTT_TOPIC)
    client.publish('edge/thing/request', '', qos=1);
    # hint: to register as agent or operation status, use "e".


def on_publish(client, userdata, result):
    print("data published: " + str(result))


# The callback when a install or download command is received
# msg is of type MQTTMessage


def on_message(client, userdata, msg):
    print("received message on mqtt topic: " + msg.topic)
    # try-catch will ensure that subscription is not broken in case of any unhandled exception.
    try:
        process_event(msg)
    except Exception as err:
        print(err)


def process_event(msg: paho.mqtt.client.MQTTMessage):
    """Will process the mqtt message based on the use case. Use case is determined by the message topic."""
    payload_str = str(msg.payload.decode("utf-8", "ignore"))
    print(payload_str)
    payload = json.loads(payload_str)
    
    if msg.topic == DEVICE_INFO_TOPIC:
        global deviceInfo, meter_feature
        deviceInfo = DeviceInfo(payload)
        meter_feature = Feature("performanceTest", "2.0.0", 'measure-performance-feature', mqtt_client, deviceInfo)
        meter_feature.register()
        print("======== Feature is ready =============")
    # elif msg.topic == "command///req//modified":
    #     handle_measurement_request(cmd)
    else:
        handle_measurement_request(msg,payload)

def handle_measurement_request(msg: paho.mqtt.client.MQTTMessage, payload):
    """Will process the measurement request based on path. If path is present then it will be a feature based update request."""

    feature_id = get_feature_id(payload)
    print("feature_id: " + feature_id)
    if feature_id and feature_id == meter_feature.featureId:
        print("check completed")
        cmd = DittoCommand(payload, msg.topic, feature_id)
        cmd.print_info()
        meter_feature.handle(cmd)
    
def get_feature_id(payload):
    ## in case of event based request, feature id is in the headers
    feature_id = payload.get('headers', {}).get('ditto-message-feature-id', None)
    if feature_id:
        return feature_id
    
    ## in case of feature update based request, feature id is in the path
    pattern = "features/(.*)/properties/"  ## /features/measure-performance-feature/properties/status/request
    x = re.search(pattern, payload.get('path', {}))
    if x:
        return x.group(1)
    else:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-mh", "--mqtt_host", metavar='HOST', help="Host of the MQTT broker", default='localhost')
    parser.add_argument("-mp", "--mqtt_port", metavar='PORT', help="Port of the MQTT broker", type=int, default=1883)
    parser.add_argument("-ll", "--log_level", metavar="LOG_LEVEL", help="Log level", default='INFO')
    args = parser.parse_args()

    logging.basicConfig(level=args.log_level)
    print("MQTT connecting to {}:{}".format(args.mqtt_host, args.mqtt_port))
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_publish = on_publish
    mqtt_client.on_message = on_message

    mqtt_client.connect(args.mqtt_host, args.mqtt_port, 60)

    mqtt_client.loop_forever()
