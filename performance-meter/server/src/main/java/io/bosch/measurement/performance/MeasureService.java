package io.bosch.measurement.performance;

import io.bosch.measurement.consumers.Counter.Status;
import io.bosch.measurement.consumers.DittoFeatureEventConsumer;
import io.bosch.measurement.consumers.DittoWsEventConsumer;
import io.bosch.measurement.consumers.RestConsumer;
import io.bosch.measurement.ditto.AuthenticationProperties;
import io.bosch.measurement.ditto.DittoThingClient;
import org.eclipse.ditto.client.DittoClient;
import org.eclipse.ditto.json.JsonPointer;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Service;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.ExecutionException;

@Service
public class MeasureService {
    // agent will respond to featureUpdate on this id..
    private static final String FEATURE_ID = "measure-performance-feature";
    public static final JsonPointer REQUEST_PATH = JsonPointer.of("status/request");
    public static final JsonPointer RESPONSE_PATH = JsonPointer.of("status/response");

    // Beans
    private final DittoClient twinClient;
    private final DittoClient liveClient;
    private final AuthenticationProperties authenticationProperties;
    private final RestConsumer restConsumer;

    // Not Beans
    private DittoThingClient thingClient;
    private final DittoFeatureEventConsumer featureEventConsumer;
    private final DittoWsEventConsumer wsEventConsumer;

    public MeasureService(/*@Qualifier(DittoClientConfig.TWIN_CLIENT)*/ DittoClient twinClient,
//            @Qualifier(DittoClientConfig.LIVE_CLIENT) DittoClient liveClient,
                                                                        AuthenticationProperties authenticationProperties,
                                                                        RestConsumer restConsumer) {
        this.twinClient = twinClient;
        this.liveClient = twinClient; //liveClient;
        this.authenticationProperties = authenticationProperties;
        this.restConsumer = restConsumer;

        if (authenticationProperties.isAcknowledgeMessages()) {
            this.featureEventConsumer = new DittoFeatureEventConsumer(authenticationProperties.getThingsAcknLabel());
            this.wsEventConsumer = new DittoWsEventConsumer(authenticationProperties.getThingsAcknLabel());
        } else {
            this.featureEventConsumer = new DittoFeatureEventConsumer();
            this.wsEventConsumer = new DittoWsEventConsumer();
        }
    }

    @EventListener(ApplicationReadyEvent.class)
    public void onInit() throws InterruptedException, ExecutionException {
        thingClient = new DittoThingClient(twinClient, liveClient, authenticationProperties.getDeviceId());
        thingClient.createFeatureIfNotPresent(FEATURE_ID);
        thingClient.registerForFeatureChange(FEATURE_ID, featureEventConsumer);
    }

    public void measureUsingEvents(final Request request) {
        thingClient.deregisterForMeterEvents(authenticationProperties.getDeviceId());
        wsEventConsumer.reset(request);
        thingClient.registerForMeterEvents(wsEventConsumer);
        thingClient.sendStartMessage(FEATURE_ID, request);
    }

    public void measureUsingFeature(final Request request) {
        featureEventConsumer.reset(request);
        thingClient.updateFeature(FEATURE_ID, REQUEST_PATH, request);
    }

    public void measureUsingRest(final Request request) {
        restConsumer.reset(request);
        thingClient.sendStartMessage(FEATURE_ID, request);
    }

    public Map<String, Status> getStatus() {
        final var res = new LinkedHashMap<String, Status>();
        res.put("feature-based", featureEventConsumer.getStatus());
        res.put("event-based", wsEventConsumer.getStatus());
        res.put("rest-based", restConsumer.getStatus());
        return res;
    }

}
