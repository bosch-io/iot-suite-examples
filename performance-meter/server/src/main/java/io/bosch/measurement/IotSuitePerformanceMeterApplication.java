package io.bosch.measurement;

import io.bosch.measurement.ditto.AuthenticationProperties;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableConfigurationProperties({AuthenticationProperties.class})
@EnableAsync
public class IotSuitePerformanceMeterApplication {

    public static void main(final String[] args) {
        SpringApplication.run(IotSuitePerformanceMeterApplication.class, args);
    }

}
