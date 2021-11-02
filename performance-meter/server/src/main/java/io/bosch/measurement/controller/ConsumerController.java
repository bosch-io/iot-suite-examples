package io.bosch.measurement.controller;

import io.bosch.measurement.consumers.RestConsumer;
import io.bosch.measurement.performance.Response;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Controller
@RestController
@Slf4j
@RequiredArgsConstructor
public class ConsumerController {
    private final RestConsumer restConsumer;

    @RequestMapping("api/v1/consumer")
    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE)
    public void receiveResponse(@RequestBody final Response response) {
        restConsumer.accept(response);
    }

    @MessageMapping("/data")
//    @SendTo("/topic/response")
    @Payload(MediaType.APPLICATION_JSON_VALUE)
    public void receiveResponseStream(final Response response) {
        restConsumer.accept(response);
    }
}
