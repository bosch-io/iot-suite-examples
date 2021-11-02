/**
 * Copyright (c) 2020 Bosch.IO GmbH, Germany. All rights reserved.
 */

package io.bosch.measurement.ditto;

import lombok.Data;
import org.eclipse.ditto.model.base.acks.AcknowledgementLabel;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * Things client specific configuration properties
 */
@Configuration
@ConfigurationProperties(prefix = "authentication")
@Data
public class AuthenticationProperties {

    private String oauthTokenEndpoint;
    private String wssThingsEndpointUrl;
    private String clientId;
    private String clientSecret;
    private String serviceInstanceId;
    private String deviceId;
    private boolean acknowledgeMessages = false;

    public AcknowledgementLabel getThingsAcknLabel() {
        return AcknowledgementLabel.of(getServiceInstanceId() + "_things:performancemeter");
    }
}
