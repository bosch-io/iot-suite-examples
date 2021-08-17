# Performance Measurement Tool

### Step 1: Start the agent on the edge device
* Install the following prerequisites.

```
sudo apt-get install python3 -y
sudo apt-get install lua5.1 -y
alias python=python3
sudo apt install python3-pip
pip3 install paho-mqtt python-etcd
pip3 install --upgrade requests
```

* Download the contents of repository on the edge device.
* Run `python3 edge-agent/start-agent.py`.

### Step 2: Run the client app
* Client is a spring boot application.
* To run, using following configurations. You can generate a clientId and secret from https://accounts.bosch-iot-suite.com/oauth2-clients/.

```
-Dauthentication.clientId=<generate-it-from-above-link>
-Dauthentication.clientSecret=
-Dauthentication.deviceId=<thing-id-including-namespace>
-Dauthentication.serviceInstanceId=<your-service-instance-id>
```
### Step 3: Start a measurement
Measurement can be started using any of the below options.
* Using the UI - http://localhost:8080/ui
* Using the provided postman collection.
