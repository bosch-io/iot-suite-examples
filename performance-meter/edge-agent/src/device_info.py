import json

from commands import DittoCommand


class DeviceInfo:
    """An entity that represents the information provided by edge agent over edge/thing/response topic."""

    def __init__(self, payload):
        # See https://docs.bosch-iot-suite.com/edge/index.html#109655.htm
        self.thingId = payload["deviceId"]
        arr = payload["deviceId"].split(":")
        self.namespace = arr[0]
        self.deviceId = arr[1]
        self.hubTenantId = payload["tenantId"]
        self.policyId = payload["policyId"]

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def print_info(self):
        print("Device information is \n" + self.toJson())
