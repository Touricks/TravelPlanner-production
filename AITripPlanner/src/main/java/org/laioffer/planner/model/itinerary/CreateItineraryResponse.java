package org.laioffer.planner.model.itinerary;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonInclude;
import org.laioffer.planner.model.place.PlaceDTO;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.UUID;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class CreateItineraryResponse {
    private UUID itineraryId;
    private String destinationCity;

    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ssXXX")
    private OffsetDateTime startDate;

    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ssXXX")
    private OffsetDateTime endDate;

    private TravelMode travelMode;
    private Integer budgetLimitCents;
    private Integer budgetPerMealCents;
    private String dailyStart;
    private String dailyEnd;
    private List<PlaceDTO> seededRecommendations;

    public CreateItineraryResponse() {}

    public UUID getItineraryId() {
        return itineraryId;
    }

    public void setItineraryId(UUID itineraryId) {
        this.itineraryId = itineraryId;
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

    public String getDailyStart() {
        return dailyStart;
    }

    public void setDailyStart(String dailyStart) {
        this.dailyStart = dailyStart;
    }

    public String getDailyEnd() {
        return dailyEnd;
    }

    public void setDailyEnd(String dailyEnd) {
        this.dailyEnd = dailyEnd;
    }

    public List<PlaceDTO> getSeededRecommendations() {
        return seededRecommendations;
    }

    public void setSeededRecommendations(List<PlaceDTO> seededRecommendations) {
        this.seededRecommendations = seededRecommendations;
    }

    @Override
    public String toString() {
        return "CreateItineraryResponse{" +
                "itineraryId=" + itineraryId +
                ", destinationCity='" + destinationCity + '\'' +
                ", startDate=" + startDate +
                ", endDate=" + endDate +
                ", travelMode=" + travelMode +
                ", budgetLimitCents=" + budgetLimitCents +
                ", budgetPerMealCents=" + budgetPerMealCents +
                ", dailyStart='" + dailyStart + '\'' +
                ", dailyEnd='" + dailyEnd + '\'' +
                ", seededRecommendations=" + seededRecommendations +
                '}';
    }
}
