package io.bosch.measurement.controller;

import io.bosch.measurement.performance.MeasureService;
import io.bosch.measurement.performance.Request;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;

import java.util.Arrays;
import java.util.List;

@Controller
@RequiredArgsConstructor
public class ViewController {

    public static final String USING_EVENTS = "using-events";
    public static final String USING_FEATURE = "using-feature";
    public static final String USING_REST = "using-rest";

    private final MeasureService service;
    private final List<String> typeOptions = Arrays.asList(USING_EVENTS, USING_FEATURE, USING_REST);

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    @Builder
    public static class TriggerRequest {
        private int count;
        private int delay;
        private String responseUrl;
        private String type;
    }

    @GetMapping("/ui")
    public String index(final Model model) {
        final TriggerRequest triggerRequest = new TriggerRequest();
        triggerRequest.type = typeOptions.get(0);
        triggerRequest.setCount(50);
        triggerRequest.setDelay(100);

        model.addAttribute("allstatus", this.service.getStatus());
        model.addAttribute("triggerRequest", triggerRequest);
        model.addAttribute("typeOptions", typeOptions);
        return "index";
    }

    @PostMapping("/trigger")
    public String submissionResult(@ModelAttribute("triggerRequest") final TriggerRequest trigger) {
        final Request req = Request.builder().id(RequestUtil.generateId()).count(trigger.getCount())
                .delay(trigger.getDelay()).build();
        switch (trigger.getType()) {
        case USING_EVENTS:
            req.setResponseHeaders(RequestUtil.getDittoHeaders());
            service.measureUsingEvents(req);
            break;
        case USING_FEATURE:
            service.measureUsingFeature(req);
            break;
        case USING_REST:
            req.setResponseUrl(trigger.getResponseUrl());
            service.measureUsingRest(req);
            break;
        default:
            break;
        }
        return "redirect:/ui";
    }

}
