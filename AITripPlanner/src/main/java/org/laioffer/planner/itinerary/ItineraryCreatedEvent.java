package org.laioffer.planner.itinerary;

import java.util.UUID;

/**
 * Event published when an itinerary is successfully created
 * Used to trigger async POI generation after transaction commit
 */
public class ItineraryCreatedEvent {
    private final UUID itineraryId;
    private final int poiCount;

    public ItineraryCreatedEvent(UUID itineraryId, int poiCount) {
        this.itineraryId = itineraryId;
        this.poiCount = poiCount;
    }

    public UUID getItineraryId() {
        return itineraryId;
    }

    public int getPoiCount() {
        return poiCount;
    }
}
