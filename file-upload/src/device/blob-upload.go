/*
                           Bosch.IO Example Code License
                               Version 1.1, May 2020

Copyright 2020 Bosch.IO GmbH (“Bosch.IO”). All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
following disclaimer in the documentation and/or other materials provided with the distribution.

BOSCH.IO PROVIDES THE PROGRAM "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE ENTIRE RISK AS TO
THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU. SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
ALL NECESSARY SERVICING, REPAIR OR CORRECTION. THIS SHALL NOT APPLY TO MATERIAL DEFECTS AND DEFECTS OF TITLE WHICH
BOSCH.IO HAS FRAUDULENTLY CONCEALED. APART FROM THE CASES STIPULATED ABOVE, BOSCH.IO SHALL BE LIABLE WITHOUT
LIMITATION FOR INTENT OR GROSS NEGLIGENCE, FOR INJURIES TO LIFE, BODY OR HEALTH AND ACCORDING TO THE PROVISIONS OF
THE GERMAN PRODUCT LIABILITY ACT (PRODUKTHAFTUNGSGESETZ). THE SCOPE OF A GUARANTEE GRANTED BY BOSCH.IO SHALL REMAIN
UNAFFECTED BY LIMITATIONS OF LIABILITY. IN ALL OTHER CASES, LIABILITY OF BOSCH.IO IS EXCLUDED. THESE LIMITATIONS OF
LIABILITY ALSO APPLY IN REGARD TO THE FAULT OF VICARIOUS AGENTS OF BOSCH.IO AND THE PERSONAL LIABILITY OF BOSCH.IO’S
EMPLOYEES, REPRESENTATIVES AND ORGANS.
*/

/*
blob-upload.go is a simple implementation of BLOBUpload Vorto feature. It sends a 'requestUpload' message for a single file
specified with the '-f' command-line flag and listens for the 'triggerUpload' response. Upon receiving it the provided
pre-signed URL is used to upload the file, after which the program exits.
Adding events for upload progress, success or failure is left as an exercise for the reader.
*/
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/eclipse/ditto-clients-golang"
	"github.com/eclipse/ditto-clients-golang/model"
	"github.com/eclipse/ditto-clients-golang/protocol"
	"github.com/eclipse/ditto-clients-golang/protocol/things"
	mqtt "github.com/eclipse/paho.mqtt.golang"
)

const (
	blobUploadFeatureID = "BLOBUpload"
)

var (
	mqttBrokerURI string
	filePath      string

	deviceID string
	tenantID string

	chstop = make(chan bool) // channel signaling the program should exit
)

// initialize file path and MQTT broker URI from command-line flags
func init() {
	flag.StringVar(&mqttBrokerURI, "b", "tcp://edgehost:1883", "edge agent mqtt broker")
	flag.StringVar(&filePath, "f", "", "path to file for upload (required)")

	flag.Parse()

	if filePath == "" {
		log.Fatalln("Use '-f' command flag to specify file for upload!")
	}

	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		log.Fatalf("File '%s' not found!\n", filePath)
	}
}

// fetch device and tenant IDs from edge agent, initialize the ditto client (with connectHandler and messageHandler) and wait for program exit signal
func main() {
	deviceID, tenantID = fetchDeviceInfo()
	dittoClient := ditto.NewClient(ditto.NewConfiguration().WithBroker(mqttBrokerURI).WithConnectHandler(connectHandler))

	dittoClient.Subscribe(messageHandler)

	if err := dittoClient.Connect(); err != nil {
		panic(err)
	}

	defer func() {
		dittoClient.Unsubscribe()
		dittoClient.Disconnect()
	}()

	chsys := make(chan os.Signal)
	signal.Notify(chsys, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		<-chsys
		chstop <- true
	}()

	<-chstop

	fmt.Println("Exitting")
}

// upon connect, create the BLOBUpload feature and send file upload request message
func connectHandler(client *ditto.Client) {
	feature := &model.Feature{}

	cmd := things.NewCommand(model.NewNamespacedIDFrom(deviceID)).Twin().Feature(blobUploadFeatureID).Modify(feature)
	msg := cmd.Envelope(protocol.WithResponseRequired(false))

	err := client.Send(msg)
	if err != nil {
		panic(fmt.Errorf("failed to create '%s' feature", blobUploadFeatureID))
	}

	sendUploadRequest(filePath, client)
}

// send requestUpload message for the given file
func sendUploadRequest(filePath string, client *ditto.Client) {
	request := map[string]string{"blobId": filePath, "blobType": "demo"}

	msg := things.NewMessage(model.NewNamespacedIDFrom(deviceID)).Feature(blobUploadFeatureID).Outbox("requestUpload").WithPayload(request)

	replyTo := fmt.Sprintf("command/%s", tenantID)
	err := client.Send(msg.Envelope(protocol.WithResponseRequired(true), protocol.WithContentType("application/json"), protocol.WithReplyTo(replyTo)))

	if err != nil {
		log.Printf("Failed to send message for request upload '%v' - %v\n", request, err)
	} else {
		fmt.Printf("Request upload message sent: '%v' \n", request)
	}
}

// handler for triggerUpload messages
func messageHandler(requestID string, msg *protocol.Envelope) {
	const triggerUploadPath = "/features/" + blobUploadFeatureID + "/inbox/messages/triggerUpload"

	if model.NewNamespacedID(msg.Topic.Namespace, msg.Topic.EntityID).String() == deviceID {
		if msg.Path == triggerUploadPath {
			payload, _ := (msg.Value).(map[string]interface{})
			filePath, urlStr := payload["blobId"].(string), payload["uploadURL"].(string)

			fmt.Printf("Trigger upload message received for '%v'\n", filePath)

			uploadFile(filePath, urlStr)
		}
	}
}

// upload the specified file using the given pre-signed URL
func uploadFile(filePath string, urlStr string) {
	file, err := os.Open(filePath)
	if err != nil {
		log.Printf("Failed to open '%s': %s\n", filePath, err)
		return
	}
	defer file.Close()

	stats, _ := file.Stat()
	req, _ := http.NewRequest("PUT", urlStr, file)

	fmt.Println("Uploading file: ", filePath)

	req.Header.Set("Content-Type", "application/x-binary")
	req.ContentLength = stats.Size()
	resp, err := http.DefaultClient.Do(req)

	if err != nil {
		log.Println(err)
	} else if resp.StatusCode != http.StatusOK {
		fmt.Printf("Upload error: %d, %s\n", resp.StatusCode, resp.Status)
		resp.Body.Close()
	} else {
		fmt.Println("File upload successful: ", filePath)
		resp.Body.Close()
		chstop <- true
	}
}

//fetch deviceId, tenantId info from edge agent (see https://docs.bosch-iot-suite.com/edge/index.html#109655.htm)
func fetchDeviceInfo() (string, string) {
	client := mqtt.NewClient(mqtt.NewClientOptions().AddBroker(mqttBrokerURI))
	if token := client.Connect(); token.Wait() && token.Error() != nil {
		panic(token.Error())
	}

	const responseTopic = "edge/thing/response"

	ch := make(chan map[string]string)
	client.Subscribe(responseTopic, 1, func(client mqtt.Client, message mqtt.Message) {
		deviceInfo := map[string]string{}
		json.Unmarshal(message.Payload(), &deviceInfo)

		ch <- deviceInfo
	})

	defer client.Unsubscribe(responseTopic)

	client.Publish("edge/thing/request", 1, false, "")

	const timeout = 20 * time.Second
	select {
	case deviceInfo := <-ch:
		return deviceInfo["deviceId"], deviceInfo["tenantId"]
	case <-time.After(20 * timeout):
		panic(fmt.Errorf("things info not received in %v", timeout))
	}
}
