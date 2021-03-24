import os
import os.path
import json
from json import JSONEncoder
import uuid
from ditto_response import DittoResponse

class Agent:
    """An entity that represents a Software Updatable agent."""

    def __init__(self, name, version, type,featureId):
        self.name = name
        self.version = version
        self.type = type
        self.featureId = featureId

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
    def register(self,mqttClient,deviceInfo):
        """Registers this agent as a feature in IoT-THings
    
        Parameters
        ----------
        mqttClient : paho.mqtt.client
            The mqtt client that has the connection to the local mosquitto provided by the edge device.
        deviceInfo : DeviceInfo
            Information of this device in the context of its subscription.
        """
        
        dittoRspTopic = "{}/{}/things/twin/commands/modify".format(deviceInfo.namespace, deviceInfo.deviceId)
        value = {}
        value["definition"] = ["org.eclipse.hawkbit.swupdatable:SoftwareUpdatable:2.0.0"]
        value["properties"] = {}
        value["properties"]["status"]= {
            "agentName": self.name,
            "agentVersion": self.version,
            "softwareModuleType": self.type
        }
        path = "/features/" + self.featureId
        rsp = DittoResponse(dittoRspTopic, path, None)
        
        rsp.value = value
        mqttClient.publish("e", rsp.toJson(), qos=1)
