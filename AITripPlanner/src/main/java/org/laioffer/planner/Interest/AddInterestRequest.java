package org.laioffer.planner.Interest;

import jakarta.validation.constraints.NotNull;
import java.util.UUID;

public class AddInterestRequest {
    @NotNull(message = "placeId is required")
    private UUID placeId;

    private boolean pinned = true;

    public AddInterestRequest() {}

    public AddInterestRequest(UUID placeId) {
        this.placeId = placeId;
    }

    public AddInterestRequest(UUID placeId, boolean pinned) {
        this.placeId = placeId;
        this.pinned = pinned;
    }

    public UUID getPlaceId() {
        return placeId;
    }

    public void setPlaceId(UUID placeId) {
        this.placeId = placeId;
    }

    public boolean isPinned() {
        return pinned;
    }

    public void setPinned(boolean pinned) {
        this.pinned = pinned;
    }

    @Override
    public String toString() {
        return "AddInterestRequest{" +
                "placeId=" + placeId +
                ", pinned=" + pinned +
                '}';
    }
}