package io.bosch.measurement.performance;

import java.util.Map;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class Request {
    private String id;
    private int count;

    /**
     * Time gap between each event sent from the edge device in milli-seconds.
     */
    private int delay;

    /*
     * Device should blindly include these headers while responding to thsi
     * request.
     */
    private Map responseHeaders;

    /**
     * This value is set if the device is expected to respond over a http call.
     */
    private String responseUrl;
}
