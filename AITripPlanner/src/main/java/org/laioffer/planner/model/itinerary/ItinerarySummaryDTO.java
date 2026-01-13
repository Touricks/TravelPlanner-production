package org.laioffer.planner.model.itinerary;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonInclude;
import org.laioffer.planner.model.common.TravelPace;

import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.util.UUID;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class ItinerarySummaryDTO {
    private UUID id;
    private String destinationCity;

    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ssXXX")
    private OffsetDateTime startDate;

    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ssXXX")
    private OffsetDateTime endDate;

    private TravelMode travelMode;
    private Integer budgetLimitCents;
    private TravelPace travelPace;

    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
    private LocalDateTime createdAt;

    public ItinerarySummaryDTO() {}

    public ItinerarySummaryDTO(UUID id, String destinationCity, OffsetDateTime startDate,
                              OffsetDateTime endDate, TravelMode travelMode,
                              Integer budgetLimitCents, TravelPace travelPace, LocalDateTime createdAt) {
        this.id = id;
        this.destinationCity = destinationCity;
        this.startDate = startDate;
        this.endDate = endDate;
        this.travelMode = travelMode;
        this.budgetLimitCents = budgetLimitCents;
        this.travelPace = travelPace;
        this.createdAt = createdAt;
    }

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

    public TravelPace getTravelPace() {
        return travelPace;
    }

    public void setTravelPace(TravelPace travelPace) {
        this.travelPace = travelPace;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    @Override
    public String toString() {
        return "ItinerarySummaryDTO{" +
                "id=" + id +
                ", destinationCity='" + destinationCity + '\'' +
                ", startDate=" + startDate +
                ", endDate=" + endDate +
                ", travelMode=" + travelMode +
                ", budgetLimitCents=" + budgetLimitCents +
                ", travelPace=" + travelPace +
                ", createdAt=" + createdAt +
                '}';
    }
}
