package org.laioffer.planner.planning.ai.model;

import dev.langchain4j.model.output.structured.Description;
import java.time.LocalTime;
import java.util.UUID;

/**
 * Represents a single stop/place in a day's itinerary.
 * AiPlannedStop.java - AI 生成的每个站点详情
 */
public class AiPlannedStop {

    @Description("UUID of the place from the interested places list - MUST match exactly")
    private UUID placeId;

    @Description("Name of the place")
    private String placeName;

    @Description("Arrival time at this place in HH:mm format")
    private LocalTime arrivalTime;

    @Description("Departure time from this place in HH:mm format")
    private LocalTime departureTime;

    @Description("Duration of visit in minutes")
    private Integer durationMinutes;

    @Description("Description of what to do at this place")
    private String activity;

    @Description("Transportation mode to next location (e.g., walking, metro, bus, taxi)")
    private String transportMode;

    @Description("Transportation duration to next location in minutes")
    private Integer transportDurationMinutes;

    // Constructors
    public AiPlannedStop() {}

    // Getters and Setters
    public UUID getPlaceId() {
        return placeId;
    }

    public void setPlaceId(UUID placeId) {
        this.placeId = placeId;
    }

    public String getPlaceName() {
        return placeName;
    }

    public void setPlaceName(String placeName) {
        this.placeName = placeName;
    }

    public LocalTime getArrivalTime() {
        return arrivalTime;
    }

    public void setArrivalTime(LocalTime arrivalTime) {
        this.arrivalTime = arrivalTime;
    }

    public LocalTime getDepartureTime() {
        return departureTime;
    }

    public void setDepartureTime(LocalTime departureTime) {
        this.departureTime = departureTime;
    }

    public Integer getDurationMinutes() {
        return durationMinutes;
    }

    public void setDurationMinutes(Integer durationMinutes) {
        this.durationMinutes = durationMinutes;
    }

    public String getActivity() {
        return activity;
    }

    public void setActivity(String activity) {
        this.activity = activity;
    }

    public String getTransportMode() {
        return transportMode;
    }

    public void setTransportMode(String transportMode) {
        this.transportMode = transportMode;
    }

    public Integer getTransportDurationMinutes() {
        return transportDurationMinutes;
    }

    public void setTransportDurationMinutes(Integer transportDurationMinutes) {
        this.transportDurationMinutes = transportDurationMinutes;
    }
}
