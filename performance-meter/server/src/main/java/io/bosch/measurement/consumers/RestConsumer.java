package io.bosch.measurement.consumers;

import io.bosch.measurement.performance.Response;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

/**
 * Consumer for consuming the events sent by the device using the rest endpoint
 * of this client application.
 *
 */
@Service
public class RestConsumer extends ConsumerBase {

    private static final Logger LOG = LoggerFactory.getLogger(RestConsumer.class);

    @Async
    public void accept(final Response response) {
        if (request != null && request.getId().equals(response.getId())) {
            counter.accept(response);
        } else {
            LOG.error("Received unknown event {}", response);
        }
    }
}
