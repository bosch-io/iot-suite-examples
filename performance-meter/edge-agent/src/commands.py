import json
import re


class MeasurementData:
    def __init__(self, message_id, expected, currentIndex):
        self.id = message_id
        self.expected = expected
        self.current = currentIndex

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class DittoResponse:
    """A utility class that is responsible for generating response messages according to the ditto protocol."""

    def __init__(self, topic, path, response_code=None):
        self.topic = topic
        self.path = path.replace("inbox","outbox") ## "/features/manually-created-lua-agent/outbox/messages/install"

        if response_code:
            self.status = response_code

    def prepare_acknowledgement(self, ditto_correlation_id):
        self.value = {}
        self.headers = {
            "response-required": False,
            "correlation-id": ditto_correlation_id,
            "content-type": "application/json"
        }

    def prepare_measurement_response(self, req):
        self.headers = {
            "response-required": False,
            "content-type": "application/json"
        }
        self.value = MeasurementData(req.id, req.serialNumber)


    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class DittoCommand:
    def __init__(self, payload, topic, featureId):
        self.payload = payload
        self.mqttTopic = topic
        self.dittoTopic = payload['topic']
        self.path = payload['path']
        self.dittoCorrelationId = payload['headers']["correlation-id"]
        self.dittoOriginator = payload['headers']["ditto-originator"]
        self.requestHeaders = payload['headers']
        
        val = payload['value']
        # For events, the value is delivered as string. In case of feature update, the value is delivered as dict.
        if type(val) is dict:
            self.value = json.loads(json.dumps(val))
        else:
            self.value = json.loads(val)
        self.featureId = featureId

    def get_request_id(self):
        # everything between req/ and /install is the request id.
        # Ex topic: command///req/01fp-pdid6m-12i8u431qmpi1b-1m2zqv2replies/install
        pattern = "req/(.*)/"
        x = re.search(pattern, self.mqttTopic)
        if x:
            return x.group(1)
        else:
            return None

    def get_service_instance_id(self):
        pattern = "service-instance.(.*).iot-"
        ## everything between 'service-instance.' and '.iot-'. 
        # Ex topic: iot-suite:useridhere/service-instance.abcde.iot-things@device-management
        x = re.search(pattern, self.dittoOriginator)
        if x:
            return x.group(1)
        else:
            return None

    def print_info(self):
        print("MQTT topic: " + self.mqttTopic)
        print('Ditto topic: ' + self.dittoTopic)
        print('Ditto originator: ' + self.dittoOriginator)
        print('Service instance id: ' + self.get_service_instance_id())
        print('Path: ' + self.path)
        if self.featureId:
            print('Feature id: : ' + self.featureId)
        print("===")

    def get_measurement_data(self) -> MeasurementData:
        lst = []
        if 'value' not in self.payload.keys():
            return None
        value_id = self.payload['value']['id']
        serial_number = self.payload['value']['serialNumber']
        return MeasurementData(value_id, serial_number)

    def get_response(self) -> DittoResponse:
        """Get an acknowledge response for this command."""
        status = 200
        akn_path = self.path.replace("inbox", "outbox")
        rsp = DittoResponse(self.dittoTopic, akn_path, status)
        rsp.prepare_acknowledgement(self.dittoCorrelationId)
        return rsp

    def response_required(self) -> bool:
        return self.payload['headers']['response-required']
