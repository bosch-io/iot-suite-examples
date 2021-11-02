/**
 * Copyright (c) 2020 Bosch.IO GmbH, Germany. All rights reserved.
 */

package io.bosch.measurement.ditto;

import com.neovisionaries.ws.client.WebSocket;
import lombok.extern.slf4j.Slf4j;
import org.eclipse.ditto.client.DittoClient;
import org.eclipse.ditto.client.DittoClients;
import org.eclipse.ditto.client.configuration.ClientCredentialsAuthenticationConfiguration;
import org.eclipse.ditto.client.configuration.ClientCredentialsAuthenticationConfiguration.ClientCredentialsAuthenticationConfigurationBuilder;
import org.eclipse.ditto.client.configuration.MessagingConfiguration;
import org.eclipse.ditto.client.configuration.WebSocketMessagingConfiguration;
import org.eclipse.ditto.client.messaging.AuthenticationProvider;
import org.eclipse.ditto.client.messaging.AuthenticationProviders;
import org.eclipse.ditto.client.messaging.MessagingProvider;
import org.eclipse.ditto.client.messaging.MessagingProviders;
import org.eclipse.ditto.model.base.acks.AcknowledgementLabel;
import org.eclipse.ditto.model.base.json.JsonSchemaVersion;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.ArrayList;
import java.util.List;

/**
 * Ditto client config to configure proxy and provide clients for live and twin
 * usage
 */
@Slf4j
@Configuration
public class DittoClientConfig {

//    public static final String LIVE_CLIENT = "liveClient";
//    public static final String TWIN_CLIENT = "twinClient";

    private final AuthenticationProperties authenticationProperties;

    DittoClientConfig(final AuthenticationProperties authenticationProperties) {
        this.authenticationProperties = authenticationProperties;
    }

    //    @Bean(LIVE_CLIENT)
//    DittoClient createLiveThingsClient() {
//        return DittoClients.newInstance(createDittoConfiguration());
//    }
//
//    @Bean(TWIN_CLIENT)
    @Bean
    DittoClient createTwinThingsClient() {
        return DittoClients.newInstance(createDittoConfiguration());
    }

    private MessagingProvider createDittoConfiguration() {
        final MessagingConfiguration messagingConfig = getMessagingConfiguration();

        final AuthenticationProvider<WebSocket> authenticationProvider;

        final ClientCredentialsAuthenticationConfigurationBuilder authenticationConfigurationBuilder = ClientCredentialsAuthenticationConfiguration
                .newBuilder().clientId(authenticationProperties.getClientId())
                .clientSecret(authenticationProperties.getClientSecret()).scopes(getScopes())
                .tokenEndpoint(authenticationProperties.getOauthTokenEndpoint());

        authenticationProvider = AuthenticationProviders.clientCredentials(authenticationConfigurationBuilder.build());

        return MessagingProviders.webSocket(messagingConfig, authenticationProvider);
    }

    private MessagingConfiguration getMessagingConfiguration() {
        final MessagingConfiguration messagingConfig;
        if (authenticationProperties.isAcknowledgeMessages()) {
            final AcknowledgementLabel acknLabel = authenticationProperties.getThingsAcknLabel();
            log.info("Message acknowledgement enabled, using label: {}", acknLabel);
            messagingConfig = WebSocketMessagingConfiguration.newBuilder()
                    .endpoint(authenticationProperties.getWssThingsEndpointUrl())
                    .jsonSchemaVersion(JsonSchemaVersion.V_2)
                    .declaredAcknowledgements(List.of(acknLabel))
                    .build();
        } else {
            messagingConfig = WebSocketMessagingConfiguration.newBuilder()
                    .endpoint(authenticationProperties.getWssThingsEndpointUrl())
                    .jsonSchemaVersion(JsonSchemaVersion.V_2)
                    .build();
        }
        return messagingConfig;
    }

    private List<String> getScopes() {
        final String serviceInstanceId = authenticationProperties.getServiceInstanceId();
        final List<String> res = new ArrayList<String>();
        // res.add("openid");
        // res.add("offline_access");

        /*
         * for (final String name : Arrays.asList("iot-hub", "iot-things",
         * "iot-manager", "iot-rollouts")) {
         * res.add(String.format("service-instance.%s.%s", serviceInstanceId,
         * name)); }
         */

        res.add(String.format("service:iot-manager:%s_iot-manager/full-access", serviceInstanceId));
        res.add(String.format("service:iot-rollouts:%s_rollouts/full-access", serviceInstanceId));
        res.add(String.format("service:iot-hub-prod:t%s_hub/full-access", serviceInstanceId.replace("-", "")));
        res.add(String.format("service:iot-things-eu-1:%s_things/full-access", serviceInstanceId));

        return res;
    }
}
