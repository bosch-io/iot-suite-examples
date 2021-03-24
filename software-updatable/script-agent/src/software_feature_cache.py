import os
import os.path
import json
from json import JSONEncoder
import uuid
from ditto_response import DittoResponse
from datetime import datetime

# Creates a file on the device which contains a list of artifact file paths associated with a feature id.
class SoftwareFeatureCache:
    CACHE_DIRECTORY = os.getcwd() + "/software-feature-cache/"
    def __init__(self,featureId):
        self.featureId = featureId
        self.files = []

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
    def updateDittoFeature(self,mqttClient,deviceInfo,executionResult):
        """Creates or updates the feature on ditto which represents this software module.
    
        Parameters
        ----------
        mqttClient : paho.mqtt.client
            The mqtt client that has the connection to the local mosquitto provided by the edge device.
        executionResult : Object
            Result of the script execution.
        """
        
        dittoRspTopic = "{}/{}/things/twin/commands/modify".format(deviceInfo.namespace, deviceInfo.deviceId)
        value = {}
        # See https://vorto.eclipseprojects.io/#/details/com.bosch.iotsuite.generic:Executor:1.0.0
        value["definition"] = ["com.bosch.iotsuite.generic:Executor:1.0.0"]
        value["properties"] = {}
        value["properties"]["status"]= {
            "files": self.files,
            "executionResult": executionResult,
            "executedAt": str(datetime.now())
        }
        path = "/features/" + self.featureId
        rsp = DittoResponse(dittoRspTopic, path, None)
        rsp.value = value
        mqttClient.publish("e", rsp.toJson(), qos=1)

    @staticmethod
    def loadOrCreate(featureId: str):
        if SoftwareFeatureCache.hasCache(featureId) == False:
            return SoftwareFeatureCache(featureId)
        else:
            filePath = SoftwareFeatureCache.getCachePath(featureId)
            f = open(filePath, "r")
            a = json.loads(f.read())
            f.close()
            cache = SoftwareFeatureCache(a["featureId"])
            cache.files = a["files"]
            print('loading from cache: ' + cache.toJson())
            return cache;

    def addFile(self,filePath):
        if (filePath in self.files) == False:
            self.files.append(filePath)
           
    def save(self):
        filePath = SoftwareFeatureCache.getCachePath(self.featureId)
        f = open(filePath,"w+")
        f.writelines(self.toJson())
        f.close()
        print ("Created cache with feature id",self.featureId)
    
    @staticmethod   
    def hasCache(featureId):
        return os.path.isfile(SoftwareFeatureCache.getCachePath(featureId))
    
    @staticmethod 
    def getCachePath(featureId):
        dir = SoftwareFeatureCache.CACHE_DIRECTORY
        if os.path.isdir(dir) == False:
            os.mkdir(dir)
        return dir + featureId + ".json"
        