# Simple performance meter for the Bosch IoT Suite

The performance meter consists out of:

- edge-agent: A service to be installed on a edge device (requires python)
- server/REST-API: Counterpart to be installed in the cloud

After a request to the server a command will be send through the Bosch IoT Suite in order to the service on the device

- instructing it to send a certain amount of messages through different channels back to the server.

Available channels are:

- Live-messages/telemetry events
- Feature updates (of a digital-twin within Bosch IoT Things)
- Direct HTTP-requests on an REST endpoint of the server
- Direct websocket communication from device to server

There is a simple UI for triggering the metering requests.
REST/Websockets are distinquished by using either http://... or ws://... as response URL.

