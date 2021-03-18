import json
import re

class Artifacts:
    def __init__(self,name,url):
        self.name = name
        self.url = url

class SoftwareModules:
    def __init__(self,name,version,artifacts):
        self.name = name
        self.version = version
        self.artifacts = artifacts
    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

class DittoCommand:
    def __init__(self, payload,topic):
        self.payload = payload
        self.mqttTopic = topic
        self.dittoTopic = payload['topic']
        self.path = payload['path']
        self.dittoCorrelationId = payload['headers']["correlation-id"]
        self.dittoOriginator = payload['headers']["ditto-originator"]
        self.requestHeaders = payload['headers']
        self.featureId = self.getFeatureId()
        
    def getRolloutsCorrelationId(self):
        return self.payload['value']['correlationId']
    
    def isSoftwareUpdate(self):
        return (self.isInstallCommand() or self.isDownloadCommand())
    
    def isInstallCommand(self):
        return self.path.endswith('install')
    
    def isDownloadCommand(self):
        return self.path.endswith('download')
    
    def getRequestId(self):
        pattern = "req/(.*)/" ## everything between req/ and /install is the request id. Ex topic: command///req/01fp-pdid6m-12i8u431qmpi1b-1m2zqv2replies/install
        x = re.search(pattern, self.mqttTopic)
        if x:
            return x.group(1)
        else:
            return None
    def getFeatureId(self):
        pattern = "features/(.*)/inbox" ## /features/manually-created-lua-agent/inbox/messages/install
        x = re.search(pattern, self.path)
        if x:
            return x.group(1)
        else:
            return None
    def getServiceInstanceId(self):
        pattern = "service-instance.(.*).iot-" 
        ## everything between 'service-instance.' and '.iot-'. 
        # Ex topic: iot-suite:useridhere/service-instance.abcde.iot-things@device-management
        x = re.search(pattern, self.dittoOriginator)
        if x:
            return x.group(1)
        else:
            return None   
    
    def printInfo(self):
        print("MQTT topic: " + self.mqttTopic)
        print('Ditto topic: ' + self.dittoTopic)
        print('Ditto originator: ' + self.dittoOriginator)
        print('Service instance id: ' + self.getServiceInstanceId())
        print('Path: ' + self.path)
        print("===")
        print('Is install command: ' + str(self.isInstallCommand()))
        print('Is software updatable command: ' + str(self.isSoftwareUpdate()))
        if self.featureId:
            print('Feature id: : ' + self.featureId)
        print("===")
        
    def getSoftwareModules(self):
        lst = []
        if 'value' not in self.payload.keys():
            return []
        
        for swMod in self.payload['value']['softwareModules']: 
            name = swMod['softwareModule']['name']
            vrsn = swMod['softwareModule']['version']
            arts = []
            for artifact in swMod['artifacts']:
             arts.append(Artifacts(artifact['filename'], artifact['download']['HTTPS']['url']))
            lst.append(SoftwareModules(name,vrsn,arts))
        return lst
