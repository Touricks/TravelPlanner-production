package org.laioffer.planner.planning.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(value = HttpStatus.NOT_FOUND, reason = "Itinerary not found.")
public class ItineraryNotFoundException extends RuntimeException {
    public ItineraryNotFoundException(String message) {
        super(message);
    }
}
