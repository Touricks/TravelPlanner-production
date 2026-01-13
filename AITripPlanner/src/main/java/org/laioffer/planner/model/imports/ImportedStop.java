package org.laioffer.planner.model.imports;

import jakarta.validation.constraints.NotBlank;

/**
 * A single stop in the imported plan.
 */
public class ImportedStop {

    @NotBlank(message = "poiExternalId is required")
    private String poiExternalId;

    private String poiName;
    private String arrivalTime;    // "09:00"
    private String departureTime;  // "11:30"
    private Integer durationMinutes;
    private String activity;

    public ImportedStop() {}

    // Getters and Setters
    public String getPoiExternalId() {
        return poiExternalId;
    }

    public void setPoiExternalId(String poiExternalId) {
        this.poiExternalId = poiExternalId;
    }

    public String getPoiName() {
        return poiName;
    }

    public void setPoiName(String poiName) {
        this.poiName = poiName;
    }

    public String getArrivalTime() {
        return arrivalTime;
    }

    public void setArrivalTime(String arrivalTime) {
        this.arrivalTime = arrivalTime;
    }

    public String getDepartureTime() {
        return departureTime;
    }

    public void setDepartureTime(String departureTime) {
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
}
