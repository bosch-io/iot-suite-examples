package io.bosch.measurement.consumers;

import io.bosch.measurement.performance.MeasureService;
import io.bosch.measurement.performance.Response;
import lombok.RequiredArgsConstructor;
import org.eclipse.ditto.client.changes.Change;
import org.eclipse.ditto.json.JsonValue;
import org.eclipse.ditto.model.base.acks.AcknowledgementLabel;
import org.eclipse.ditto.model.base.common.HttpStatusCode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.function.Consumer;

@RequiredArgsConstructor
public class DittoFeatureEventConsumer extends ConsumerBase implements Consumer<Change> {

    private static final Logger LOG = LoggerFactory.getLogger(DittoFeatureEventConsumer.class);
    private final AcknowledgementLabel acknowledgementLabel;

    public DittoFeatureEventConsumer() {
        acknowledgementLabel = null;
    }

    @Override
    public void accept(final Change change) {
        final String path = change.getPath().toString();
        change.getValue().ifPresent(value -> {
            if (path.equals(MeasureService.REQUEST_PATH.toString())) {
                LOG.info("Request has reached ditto: {}", value);
            } else if (path.equals(MeasureService.RESPONSE_PATH.toString())) {
                process(value);
            }
        });
        if (acknowledgementLabel != null) {
            LOG.trace("Sending acknowledge: {}", acknowledgementLabel);
            change.handleAcknowledgementRequest(acknowledgementLabel, handle -> handle.acknowledge(HttpStatusCode.OK));
        }
    }

    public void process(final JsonValue value) {
        try {
            final Response data = objectMapper.readValue(value.toString(), Response.class);
            if (request.getId().equals(data.getId())) {
                counter.accept(data);
            } else {
                LOG.error("Received unknown event {}. Expecting {}", data, request.getId());
            }
        } catch (final IOException e) {
            LOG.error("Exception while parsing {}, {}", value, e);
        }
    }


}
