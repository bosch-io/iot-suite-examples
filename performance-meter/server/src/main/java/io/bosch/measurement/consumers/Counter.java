package io.bosch.measurement.consumers;

import com.google.common.collect.Ordering;
import io.bosch.measurement.performance.Response;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.joda.time.Duration;
import org.joda.time.format.PeriodFormatterBuilder;

import java.util.LinkedHashSet;
import java.util.Set;
import java.util.stream.Collectors;

@Slf4j
public class Counter {
    private final String id;
    private final int expectedCount;
    private int duplicateReceivedCount = 0;
    private final int delay;
    private final Set<Response> received;
    private final long startTime;
    private long lastReceivedEventTime;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class Status {
        private String id;
        private int expected;
        private int received;
        private boolean completed;
        private boolean inOrder;
        // private List<Integer> messages;
        private String timeTaken;
        private int duplicatesReceived;

        /**
         * This will subtract the delay added to the response.
         */
        private String timePerMessage;
    }

    public Counter(final String id, final int expectedCount, final int delay) {
        this.id = id;
        this.expectedCount = expectedCount;
        this.delay = delay;
        this.received = new LinkedHashSet<>(expectedCount);
        this.startTime = System.currentTimeMillis();
    }

    public void accept(final Response data) {
        if (!received.add(data)) {
            duplicateReceivedCount++;
        } else {
            log.trace("Responce received: {}", data);
            lastReceivedEventTime = System.currentTimeMillis();
            if (data.getCurrent() >= data.getExpected()) {
                final String elapsedDuration = prettify(lastReceivedEventTime - startTime);
                log.info("Received {} events in {}. Request id {}", expectedCount, elapsedDuration, id);
            }
        }
    }

    public Status getStatus() {
        if (received.isEmpty()) {
            return null;
        }
        final var elapsedTimeWithDelay = lastReceivedEventTime - startTime;
        final var completed = expectedCount == received.size();

        final var indexReceived = received.stream().map(Response::getCurrent).collect(Collectors.toList());
        final var isInOrder = Ordering.natural().isOrdered(indexReceived);
        final var averageTimePerMsg = (elapsedTimeWithDelay - ((long) received.size() * delay))
                / received.size();

        log.debug("id={}; elapsedTimeWithDelay= {}ms; averageTimePerMsg={}ms", id, elapsedTimeWithDelay, averageTimePerMsg);
        return Status.builder()//
                .id(id)//
                .expected(expectedCount) //
                .received(received.size())//
                .completed(completed)//
                .inOrder(isInOrder)//
                .duplicatesReceived(duplicateReceivedCount)
                // .messages(indexReceived)//
                .timeTaken(prettify(elapsedTimeWithDelay))//
                .timePerMessage(prettify(averageTimePerMsg))
                .build();
    }

    private String prettify(final long milliSeconds) {
        return new PeriodFormatterBuilder()//
                .appendMinutes()//
                .appendSuffix("m ") //
                .appendSeconds()//
                .appendSuffix("s ")//
                .appendMillis()//
                .appendSuffix("ms")//
                .toFormatter()
                .print(Duration.millis(milliSeconds).toPeriod());
    }

}
