package org.laioffer.planner.model.itinerary;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonInclude;
import org.laioffer.planner.model.common.ActivityIntensity;
import org.laioffer.planner.model.common.AttractionCategory;
import org.laioffer.planner.model.common.TravelPace;

import java.time.OffsetDateTime;
import java.util.List;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class CreateItineraryRequest {
    private String destinationCity;

    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ssXXX")
    private OffsetDateTime startDate;

    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ssXXX")
    private OffsetDateTime endDate;

    private TravelMode travelMode;

    private Integer budgetLimitCents;

    // User preference fields
    private TravelPace travelPace;

    private ActivityIntensity activityIntensity;
    private List<AttractionCategory> preferredCategories;
    private Integer numberOfTravelers;
    private Boolean hasChildren;
    private Boolean hasElderly;
    private Boolean preferPopularAttractions;
    private String additionalPreferences;

    public CreateItineraryRequest() {}

    public CreateItineraryRequest(String destinationCity, OffsetDateTime startDate, OffsetDateTime endDate) {
        this.destinationCity = destinationCity;
        this.startDate = startDate;
        this.endDate = endDate;
    }

    public String getDestinationCity() {
        return destinationCity;
    }

    public void setDestinationCity(String destinationCity) {
        this.destinationCity = destinationCity;
    }

    public OffsetDateTime getStartDate() {
        return startDate;
    }

    public void setStartDate(OffsetDateTime startDate) {
        this.startDate = startDate;
    }

    public OffsetDateTime getEndDate() {
        return endDate;
    }

    public void setEndDate(OffsetDateTime endDate) {
        this.endDate = endDate;
    }

    public TravelMode getTravelMode() {
        return travelMode;
    }

    public void setTravelMode(TravelMode travelMode) {
        this.travelMode = travelMode;
    }

    public Integer getBudgetLimitCents() {
        return budgetLimitCents;
    }

    public void setBudgetLimitCents(Integer budgetLimitCents) {
        this.budgetLimitCents = budgetLimitCents;
    }

    public TravelPace getTravelPace() {
        return travelPace;
    }

    public void setTravelPace(TravelPace travelPace) {
        this.travelPace = travelPace;
    }

    public ActivityIntensity getActivityIntensity() {
        return activityIntensity;
    }

    public void setActivityIntensity(ActivityIntensity activityIntensity) {
        this.activityIntensity = activityIntensity;
    }

    public List<AttractionCategory> getPreferredCategories() {
        return preferredCategories;
    }

    public void setPreferredCategories(List<AttractionCategory> preferredCategories) {
        this.preferredCategories = preferredCategories;
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

    public Boolean getPreferPopularAttractions() {
        return preferPopularAttractions;
    }

    public void setPreferPopularAttractions(Boolean preferPopularAttractions) {
        this.preferPopularAttractions = preferPopularAttractions;
    }

    public String getAdditionalPreferences() {
        return additionalPreferences;
    }

    public void setAdditionalPreferences(String additionalPreferences) {
        this.additionalPreferences = additionalPreferences;
    }

    @Override
    public String toString() {
        return "CreateItineraryRequest{" +
                "destinationCity='" + destinationCity + '\'' +
                ", startDate=" + startDate +
                ", endDate=" + endDate +
                ", travelMode=" + travelMode +
                ", budgetLimitCents=" + budgetLimitCents +
                ", travelPace=" + travelPace +
                ", activityIntensity=" + activityIntensity +
                // ", preferredCategories=" + preferredCategories +
                ", numberOfTravelers=" + numberOfTravelers +
                ", hasChildren=" + hasChildren +
                ", hasElderly=" + hasElderly +
                ", preferPopularAttractions=" + preferPopularAttractions +
                ", additionalPreferences='" + additionalPreferences + '\'' +
                '}';
    }
}
