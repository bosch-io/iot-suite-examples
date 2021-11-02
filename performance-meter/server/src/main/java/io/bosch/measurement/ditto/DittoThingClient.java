package io.bosch.measurement.ditto;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.bosch.measurement.performance.Request;
import org.eclipse.ditto.client.DittoClient;
import org.eclipse.ditto.client.changes.Change;
import org.eclipse.ditto.client.live.messages.RepliableMessage;
import org.eclipse.ditto.client.twin.TwinFeatureHandle;
import org.eclipse.ditto.client.twin.TwinThingHandle;
import org.eclipse.ditto.json.JsonFactory;
import org.eclipse.ditto.json.JsonPointer;
import org.eclipse.ditto.json.JsonValue;
import org.eclipse.ditto.model.things.Feature;
import org.eclipse.ditto.model.things.FeatureProperties;
import org.eclipse.ditto.model.things.ThingId;
import org.eclipse.ditto.model.things.ThingsModelFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;

public class DittoThingClient {
    private static final Logger LOG = LoggerFactory.getLogger(DittoThingClient.class.getName());
    private final DittoClient twinClient;
    private final DittoClient liveClient;
    private final String thingId;
    private final TwinThingHandle thingTwin;

    public DittoThingClient(final DittoClient twinClient, final DittoClient liveClient, final String deviceId) {
        this.thingId = deviceId;
        this.twinClient = twinClient;
        this.liveClient = liveClient;
        this.thingTwin = twinClient.twin().forId(ThingId.of(deviceId));
        this.liveClient.live().startConsumption().thenAccept(Void -> {
            LOG.info("Registered for live events");
        });
    }

    public void registerForFeatureChange(final String featureId, final Consumer<Change> handler)
            throws InterruptedException, ExecutionException {
        twinClient.twin().startConsumption().thenAccept(Void -> {
            twinClient.twin().registerForFeaturePropertyChanges("my-feature-changes", featureId, "/", handler);
            LOG.info("Registered for feature update events");
        });
    }

    public void registerForMeterEvents(final Consumer<RepliableMessage<?, Object>> handler) {
        liveClient.live().forId(ThingId.of(thingId)).registerForMessage("performance-meter", "meter.event.response",
                handler);
    }

    public void deregisterForMeterEvents(final String thingId) {
        liveClient.live().forId(ThingId.of(thingId)).deregister("performance-meter");
        liveClient.live().forId(ThingId.of(thingId)).deregister("log-handler");
    }

    public void createFeatureIfNotPresent(final String featureId) {
        try {
            thingTwin.forFeature(featureId).retrieve().get(10, TimeUnit.SECONDS);
        } catch (final Exception e) {
            final FeatureProperties featureProperties = FeatureProperties.newBuilder().build();
            final Feature feature = ThingsModelFactory.newFeatureBuilder().properties(featureProperties)
                    .withId(featureId).build();
            createFeature(feature);
        }
    }

    public Feature createFeature(final Feature feature) {
        try {
            return createFeatureWithClient(feature).get();
        } catch (final InterruptedException e) {
            Thread.currentThread().interrupt();
            LOG.error("{}: Failed to create feature.", thingId, e);
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, e.getMessage());
        } catch (final ExecutionException e) {
            LOG.error("{}: Failed to create feature.", thingId, e);
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, e.getMessage());
        }
    }

    public void updateFeature(final String featureId, final JsonPointer path, final Object value) {
        // for the feature id, call any operation. edge-agent does not care.
        final TwinFeatureHandle twinFeatureHandle = thingTwin.forFeature(featureId);
        final JsonValue asJsonValue = getAsJsonValue(value);
        try {
            twinFeatureHandle.putProperty(path, asJsonValue).get();
        } catch (final InterruptedException e) {
            Thread.currentThread().interrupt();
            LOG.error("{}: Failed to update feature {}.", thingId, featureId, e);
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, e.getMessage());
        } catch (final ExecutionException e) {
            LOG.error("{}: Failed to update feature {}.", thingId, featureId, e);
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, e.getMessage());
        }
    }

    private CompletableFuture<Feature> createFeatureWithClient(final Feature feature) {
        LOG.debug("{}: Create/Update feature: {}", thingId, feature.toJson());
        return thingTwin.putFeature(feature).thenCompose(aVoid -> thingTwin.forFeature(feature.getId()).retrieve())
                .whenComplete((responseThing, throwable) -> {
                    if (throwable != null) {
                        LOG.error("{}: Create/Update thing Failed: {}", thingId, throwable.getMessage());
                    }
                });
    }

    private static JsonValue getAsJsonValue(final Object value) {
        try {
            return JsonFactory.readFrom(new ObjectMapper().writeValueAsString(value));
        } catch (final JsonProcessingException e) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Cannot create measurement request property.");
        }
    }

    public void sendStartMessage(final String featureId, final Request request) {
        try {
            final String payload = new ObjectMapper().writeValueAsString(request);
            twinClient.live().forId(ThingId.of(thingId)).forFeature(featureId).message().from().subject("start")
                    .payload(payload).send();
        } catch (final JsonProcessingException e) {
            throw new RuntimeException(e);
        }

    }
}
