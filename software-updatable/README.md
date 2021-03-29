# Script Installer And Executor As Edge Feature
This example shows how to implement [Software Updatable](https://vorto.eclipseprojects.io/#/details/org.eclipse.hawkbit.swupdatable:SoftwareUpdatable:2.0.0) agent that can install and executor a `python` or `lua` or `shell` script on an edge device.


# Provisioning the device
Download the edge agent. Copy the device `provisioning.json` to the directory containing the `start.sh`. If this step is not familiar, then see:
* [Install and manage the Edge Agent](https://docs.bosch-iot-suite.com/edge/index.html#109641.htm)
* [Register a device](https://docs.bosch-iot-suite.com/device-management/Register-a-device-via-the-Bosch-IoT-Manager-UI.html)

## Running the agent

#### a. Manual Approach

- Install the following prerequisites.

```
sudo apt-get install python3 -y
sudo apt-get install lua5.1 -y
alias python=python3
sudo apt install python3-pip
pip3 install paho-mqtt python-etcd
pip3 install --upgrade requests
```
- Run `python script-agent/src/start-agent.py`.

#### b. Running as a docker container
This approach is not tested. Below are some steps that could be used to achieve this.

* Modify `python-scripts/start-agent.py` to use `ctrhost` as mosquitto host. Ex: ```client.connect("ctrhost", 1883)```
* Build the dockerfile and push the image to a repository which is publically available.
* Please see [how to deploy a container](https://docs.bosch-iot-suite.com/edge/index.html#109664.htm). It describes how to remotely trigger installation of containers on gateways in the form of Software Updates from Bosch IoT Suite Rollouts service.
* In the above step, make sure that you configure `extra_hosts` as shown below.

```
{
   "container_name": "your-container-name",
   "image": {
      "name": "image-ref"
   },
   "host_config": {
      "extra_hosts": [
         "ctrhost:host_ip"
      ]
   }
}
```
* Please Note: The scripts must be executed in the host and not inside the container.

## Performing a software update
- Login to the [Rollouts UI](https://console.eu1.bosch-iot-rollouts.com/).
- Navigate to `Distributions` tab and create a software module of type `script`.
- Upload a `shell`, or `python` or `lua` script as an artifact. There are few sample script [here](./demo-lua-scripts/).
- Create a distribution set from this software module and assign it to the device. Observe the action history.
- You can also re-execute the scripts from the [Iot Manager UI](https://console.manager.eu-1.bosch-iot-suite.com/ui). 

### Limitation
If you delete an artifact on the rollouts, you must also manually update the cache file created by this agent on the device. To know where the cache is created, please [see here](./script-agent/src/softwareFeatureCache.py).

## Clean up
If you wish to clean up the runtime, here are the steps.
- Delete the cache folder containing the artifacts associated with a feature id.
- Delete all the features created by this agent on the IoT-Things.

## References
* [Registering a device](https://docs.bosch-iot-suite.com/device-management/Register-a-device-via-the-Bosch-IoT-Manager-UI.html).
* [Install and manage the Edge Agent](https://docs.bosch-iot-suite.com/edge/index.html#109641.htm)
* [Ditto protocol](https://www.eclipse.org/ditto/1.5/protocol-specification-things-create-or-modify.html)
* [Software updatable integration suite](https://docs.bosch-iot-suite.com/device-management/SoftwareUpdatable-feature-detailed-specification-and-integration-guide.html).

## Useful Snippets

This agent does not use all concepts from ditto or edge device. So below you find some useful snippets that can be used on the device side if you wish to extend or improve this agent.

#### Get ditto feature by definition

```
def getFeatureByAgentId():
    # see https://www.eclipse.org/ditto/1.5/protocol-examples-retrievefeature.html
    # "topic": "namespace/device-id/things/twin/commands/retrieve",
    print("Request all features available in iot-things")
    pth = "/features/{}".format(agent.featureId);
    topic = "{}/{}/things/twin/commands/retrieve".format(sInfo.namespace, sInfo.deviceId)
    obj = DittoResponse(topic, pth, None)
    obj.headers = {
            "response-required": True,
            "correlation-id": "{}/{}/random-corr-id".format(sInfo.namespace, sInfo.deviceId),
            "reply-to": "command/" + sInfo.hubTenantId
    }
    client.publish("e", obj.toJson(), qos=1)
```

