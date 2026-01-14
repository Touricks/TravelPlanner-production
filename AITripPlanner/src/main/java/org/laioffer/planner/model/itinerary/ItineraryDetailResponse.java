package org.laioffer.planner.model.itinerary;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonInclude;
import org.laioffer.planner.model.common.ActivityIntensity;
import org.laioffer.planner.model.common.AttractionCategory;
import org.laioffer.planner.model.common.TravelPace;
import org.laioffer.planner.model.place.PlaceDTO;

import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class ItineraryDetailResponse {
    private UUID id;
    private String destinationCity;

    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ssXXX")
    private OffsetDateTime startDate;

    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ssXXX")
    private OffsetDateTime endDate;

    private TravelMode travelMode;
    private Integer budgetLimitCents;
    private Integer budgetPerMealCents;

    // User preference fields
    private TravelPace travelPace;
    private ActivityIntensity activityIntensity;
    private Integer numberOfTravelers;
    private Boolean hasChildren;
    private Boolean hasElderly;
    private Boolean preferPopularAttractions;
    private List<AttractionCategory> preferredCategories;
    private String additionalPreferences;

    // Related data
    private List<PlaceDTO> places;
    private Map<String, Object> seededRecommendations;

    // AI generation metadata
    private Map<String, Object> aiMetadata;

    // CRAG session ID for conversation restore
    private String cragSessionId;

    // Metadata
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
    private LocalDateTime createdAt;

    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
    private LocalDateTime updatedAt;

    public ItineraryDetailResponse() {}

    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
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

    public Integer getBudgetPerMealCents() {
        return budgetPerMealCents;
    }

    public void setBudgetPerMealCents(Integer budgetPerMealCents) {
        this.budgetPerMealCents = budgetPerMealCents;
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

    public List<AttractionCategory> getPreferredCategories() {
        return preferredCategories;
    }

    public void setPreferredCategories(List<AttractionCategory> preferredCategories) {
        this.preferredCategories = preferredCategories;
    }

    public String getAdditionalPreferences() {
        return additionalPreferences;
    }

    public void setAdditionalPreferences(String additionalPreferences) {
        this.additionalPreferences = additionalPreferences;
    }

    public List<PlaceDTO> getPlaces() {
        return places;
    }

    public void setPlaces(List<PlaceDTO> places) {
        this.places = places;
    }

    public Map<String, Object> getSeededRecommendations() {
        return seededRecommendations;
    }

    public void setSeededRecommendations(Map<String, Object> seededRecommendations) {
        this.seededRecommendations = seededRecommendations;
    }

    public Map<String, Object> getAiMetadata() {
        return aiMetadata;
    }

    public void setAiMetadata(Map<String, Object> aiMetadata) {
        this.aiMetadata = aiMetadata;
    }

    public String getCragSessionId() {
        return cragSessionId;
    }

    public void setCragSessionId(String cragSessionId) {
        this.cragSessionId = cragSessionId;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    @Override
    public String toString() {
        return "ItineraryDetailResponse{" +
                "id=" + id +
                ", destinationCity='" + destinationCity + '\'' +
                ", startDate=" + startDate +
                ", endDate=" + endDate +
                ", travelMode=" + travelMode +
                ", budgetLimitCents=" + budgetLimitCents +
                ", budgetPerMealCents=" + budgetPerMealCents +
                ", travelPace=" + travelPace +
                ", activityIntensity=" + activityIntensity +
                ", numberOfTravelers=" + numberOfTravelers +
                ", hasChildren=" + hasChildren +
                ", hasElderly=" + hasElderly +
                ", preferPopularAttractions=" + preferPopularAttractions +
                // ", preferredCategories=" + preferredCategories +
                ", additionalPreferences='" + additionalPreferences + '\'' +
                ", places=" + places +
                ", seededRecommendations=" + seededRecommendations +
                ", createdAt=" + createdAt +
                ", updatedAt=" + updatedAt +
                '}';
    }
}
