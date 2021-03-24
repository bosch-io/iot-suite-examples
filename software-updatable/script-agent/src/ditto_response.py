import json

class DittoResponse:
    """A utility class that is responsible for generating response messages according to the ditto protocol."""
    
    def __init__(self,topic,path,responseCode):
        self.topic = topic
        self.path = path.replace("inbox","outbox") ## "/features/manually-created-lua-agent/outbox/messages/install"
        
        if responseCode:
            self.status = responseCode

    def prepareAknowledgement(self,dittoCorrelationId):
        self.value = {}
        self.headers = {
            "response-required": False,
            "correlation-id": dittoCorrelationId,
            "content-type": "application/json"
        }
    def prepareSupResponse(self,rolloutCorrelationId,status,message,swModule = None):
        self.headers = {
            "response-required": False,
            "content-type": "application/json"
        }
        self.value = {
            "status": status,
            "message": message,
            "correlationId": rolloutCorrelationId
        }
        if swModule:
            self.value["softwareModule"] = {
                "name": swModule.name,
                "version": swModule.version
            }
        
    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)