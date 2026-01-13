package org.laioffer.planner.planning.ai.model;

import java.math.BigDecimal;
import java.util.UUID;

/**
 * Place information included in the AI planning request.
 * AiPlaceInfo.java - 地点信息 DTO
 */
public class AiPlaceInfo {

    private UUID placeId;
    private String name = "";
    private String address = "";
    private BigDecimal latitude = BigDecimal.ZERO;
    private BigDecimal longitude = BigDecimal.ZERO;
    private String description = "";
    private boolean pinned = false;
    private String note = "";

    // Constructors
    public AiPlaceInfo() {}

    // Getters and Setters
    public UUID getPlaceId() {
        return placeId;
    }

    public void setPlaceId(UUID placeId) {
        this.placeId = placeId;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public BigDecimal getLatitude() {
        return latitude;
    }

    public void setLatitude(BigDecimal latitude) {
        this.latitude = latitude;
    }

    public BigDecimal getLongitude() {
        return longitude;
    }

    public void setLongitude(BigDecimal longitude) {
        this.longitude = longitude;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public boolean isPinned() {
        return pinned;
    }

    public void setPinned(boolean pinned) {
        this.pinned = pinned;
    }

    public String getNote() {
        return note;
    }

    public void setNote(String note) {
        this.note = note;
    }
}
