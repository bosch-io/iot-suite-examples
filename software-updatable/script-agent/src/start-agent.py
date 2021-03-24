import paho.mqtt.client as mqtt
import time
import json
from commands import DittoCommand
from device_info import DeviceInfo
from downloader import DownloadManager
from executor import ScriptExecutor
from ditto_response import DittoResponse
from agent import Agent
from software_feature_cache import SoftwareFeatureCache

agent = Agent("script", "2.0.0", "script", 'software-updatable-script-agent')
deviceInfo = DeviceInfo()
DEVICE_INFO_TOPIC = "edge/thing/response"
MQTT_TOPIC = [(DEVICE_INFO_TOPIC, 0), ("command///req/#", 0)]


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing to a topic that sends install or download command
    client.subscribe(MQTT_TOPIC)
    # hint: to register as agent or operation status, use "e".


def on_publish(client, userdata, result):
    print("data published: " + str(result))


# The callback when a install or download command is received
# msg is of type MQTTMessage


def on_message(client, userdata, msg):
    print("received message on mqtt topic: " + msg.topic)
    # try-catch will ensure that subscription is not broken in case of any unhandled exception.
    try:
        processEvent(msg)
    except Exception as err:
        print(err)


def processEvent(msg):
    '''Will process the mqtt message based on the use case. Usecase is determined by the message topic.'''
    payloadStr = str(msg.payload.decode("utf-8", "ignore"))
    payload = json.loads(payloadStr)
    if msg.topic == "command///req//modified" or msg.topic == "command///req//deleted":
        print("Ignoring the message as this agent is not responsible for handling them")
    elif msg.topic == DEVICE_INFO_TOPIC:
        deviceInfo.compute(payload)
        agent.register(client, deviceInfo)
        print("======== Agent is ready =============")
    else:
        cmd = DittoCommand(payload, msg.topic)
        handleSupEvent(cmd)
 

def handleSupEvent(cmd):
    # cmd.printInfo()
    if cmd.isInstallCommand() and cmd.isSoftwareUpdate() and cmd.featureId == agent.featureId:
        print("processing rollouts request with ditto req id: " + str(cmd.getRequestId()))
        aknowledge(cmd)
        handleRolloutRequest(cmd)
    elif SoftwareFeatureCache.hasCache(cmd.featureId):
        # if required, add additional check if vorto definition supports multiple operations.
        execRes = executeSoftware(cmd.featureId)
        val = { "executionResult": execRes}
        aknowledge(cmd, value=execRes)
    else:
        print("command received on unknown feature: " + str(cmd.featureId))   
        # else, from cache file stored with cmd.featureId and execute the scripts stored there

def executeSoftware(featureId):
    swCache = SoftwareFeatureCache.loadOrCreate(featureId);
    execResult = ""
    for file in swCache.files:
        execResult += ScriptExecutor().executeFile(file) + "\n"
    swCache.updateDittoFeature(client, deviceInfo, execResult)
    return execResult


def handleRolloutRequest(cmd):
    print("Rollouts correlationId is: " + str(cmd.getRolloutsCorrelationId()))
    # print('Parsing software module information')
    for swMod in cmd.getSoftwareModules():
        execResult = ""
        featureId = swMod.name.replace(":", "-") + "-" + swMod.version
        swCache = SoftwareFeatureCache.loadOrCreate(featureId);
        # print(swMod.toJson())
        for art in swMod.artifacts:
            updateLastOperation(cmd, "DOWNLOADING", "Downloading " + art.name, swMod)
            filePath = DownloadManager().download(art)
            swCache.addFile(filePath)
            updateLastOperation(cmd, "DOWNLOADED", "Downloaded " + art.name, swMod)
            # # https://vorto.eclipseprojects.io/#/details/vorto.private.test:Executor:1.0.0
            updateLastOperation(cmd, "INSTALLING", "Executing script: " + filePath, swMod)
            res = "Installed a script to the location {}.\n".format(filePath)
            updateLastOperation(cmd, "INSTALLED", execResult, swMod)
            execResult += res
        swCache.save()
        swCache.updateDittoFeature(client, deviceInfo, execResult)
        updateLastOperation(cmd, "FINISHED_SUCCESS", execResult, swMod)   
  

# https://vorto.eclipseprojects.io/#/details/org.eclipse.hawkbit:Status:2.0.0
def updateLastOperation(cmd, status, message, swModule=None):
    print(">>> sending sup update " + status + " with message: " + message)
    pth = "/features/{}/properties/status/lastOperation".format(cmd.featureId)
    
    dittoRspTopic = "{}/{}/things/twin/commands/modify".format(deviceInfo.namespace, deviceInfo.deviceId)
    rsp = DittoResponse(dittoRspTopic, pth, None)
    rsp.prepareSupResponse(cmd.getRolloutsCorrelationId(), status, message, swModule)
    if status == "FINISHED_SUCCESS":
        print("======== Done =============")
    client.publish("e", rsp.toJson(), qos=1)

        
def aknowledge(cmd, value=None):
    status = 200
    mosquittoTopic = "command///res/" + str(cmd.getRequestId()) + "/" + str(status)
    # print("======== Sending aknowledgement for ditto requestId: %s =============" %(cmd.getRequestId()))
    aknPath = cmd.path.replace("inbox", "outbox")  # # "/features/manually-created-lua-agent/outbox/messages/install"
    rsp = DittoResponse(cmd.dittoTopic, aknPath, status)
    rsp.prepareAknowledgement(cmd.dittoCorrelationId)
    if value:
        rsp.value = value

    client.publish(mosquittoTopic, rsp.toJson())
    print("======== Aknowledgement sent on topic " + mosquittoTopic + " =============")


client = mqtt.Client()
client.on_connect = on_connect
client.on_publish = on_publish
client.on_message = on_message

client.connect("localhost", 1883, 60)

client.loop_forever()
