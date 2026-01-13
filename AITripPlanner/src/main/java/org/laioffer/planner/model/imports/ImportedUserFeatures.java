package org.laioffer.planner.model.imports;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;

import java.util.List;

/**
 * User features extracted from CRAG conversation.
 */
public class ImportedUserFeatures {

    @NotBlank(message = "destination is required")
    private String destination;

    @Positive(message = "travelDays must be positive")
    private Integer travelDays;

    private String startDate;  // ISO format: "2025-03-01"
    private String endDate;
    private Integer budgetCents;
    private List<String> interests;
    private String travelPace;  // RELAXED, MODERATE, PACKED
    private String travelMode;  // WALKING, DRIVING, TRANSIT, BICYCLING
    private Integer numberOfTravelers;
    private Boolean hasChildren;
    private Boolean hasElderly;

    public ImportedUserFeatures() {}

    // Getters and Setters
    public String getDestination() {
        return destination;
    }

    public void setDestination(String destination) {
        this.destination = destination;
    }

    public Integer getTravelDays() {
        return travelDays;
    }

    public void setTravelDays(Integer travelDays) {
        this.travelDays = travelDays;
    }

    public String getStartDate() {
        return startDate;
    }

    public void setStartDate(String startDate) {
        this.startDate = startDate;
    }

    public String getEndDate() {
        return endDate;
    }

    public void setEndDate(String endDate) {
        this.endDate = endDate;
    }

    public Integer getBudgetCents() {
        return budgetCents;
    }

    public void setBudgetCents(Integer budgetCents) {
        this.budgetCents = budgetCents;
    }

    public List<String> getInterests() {
        return interests;
    }

    public void setInterests(List<String> interests) {
        this.interests = interests;
    }

    public String getTravelPace() {
        return travelPace;
    }

    public void setTravelPace(String travelPace) {
        this.travelPace = travelPace;
    }

    public String getTravelMode() {
        return travelMode;
    }

    public void setTravelMode(String travelMode) {
        this.travelMode = travelMode;
    }

    public Integer getNumberOfTravelers() {
        return numberOfTravelers;
    }

    public void setNumberOfTravelers(Integer numberOfTravelers) {
        this.numberOfTravelers = numberOfTravelers;
    }

    public Boolean getHasChildren() {
        return hasChildren;
    }

    public void setHasChildren(Boolean hasChildren) {
        this.hasChildren = hasChildren;
    }

    public Boolean getHasElderly() {
        return hasElderly;
    }

    public void setHasElderly(Boolean hasElderly) {
        this.hasElderly = hasElderly;
    }
}
