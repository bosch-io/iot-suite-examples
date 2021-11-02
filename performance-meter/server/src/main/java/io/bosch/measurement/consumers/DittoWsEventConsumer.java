package io.bosch.measurement.consumers;

import io.bosch.measurement.performance.Response;
import lombok.RequiredArgsConstructor;
import org.eclipse.ditto.client.live.messages.RepliableMessage;
import org.eclipse.ditto.model.base.acks.AcknowledgementLabel;
import org.eclipse.ditto.model.base.common.HttpStatusCode;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.function.Consumer;

@RequiredArgsConstructor
public class DittoWsEventConsumer extends ConsumerBase implements Consumer<RepliableMessage<?, Object>> {

    private static final Logger LOG = LoggerFactory.getLogger(DittoWsEventConsumer.class);
    private final AcknowledgementLabel acknowledgementLabel;

    public DittoWsEventConsumer() {
        this.acknowledgementLabel = null;
    }

    @Override
    public void accept(final RepliableMessage<?, Object> message) {
        final String msg = message.getPayload().get().toString();
        try {
            final Response data = objectMapper.readValue(msg, Response.class);
            if (request.getId().equals(data.getId())) {
                counter.accept(data);
            }
            if (acknowledgementLabel != null) {
                message.handleAcknowledgementRequest(acknowledgementLabel, handle -> handle.acknowledge(HttpStatusCode.OK));
            }
        } catch (final IOException e) {
            LOG.error("Exception while parsing {}, {}", msg, e);
        }
    }
}
