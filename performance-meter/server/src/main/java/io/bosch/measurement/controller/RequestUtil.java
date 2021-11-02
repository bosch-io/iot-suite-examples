package io.bosch.measurement.controller;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

public class RequestUtil {

    public static String generateId() {
        return UUID.randomUUID().toString().replace("-", "");
    }

    public static Map enrichHeaders(final Map desiredResponseHeaders) {
        if (desiredResponseHeaders != null) {
            return desiredResponseHeaders;
        }
        return getDittoHeaders();
    }

    public static Map getDittoHeaders() {
        final Map desiredResponseHeaders = new HashMap<>();
        desiredResponseHeaders.put("response-required", false);
        desiredResponseHeaders.put("content-type", "application/json");
        desiredResponseHeaders.put("correlation-id", "dont-care");
        return desiredResponseHeaders;
    }

}
