package org.laioffer.planner.model.planning;

import org.laioffer.planner.model.common.ApiError;

import java.util.List;
import java.util.UUID;

public class PlanItineraryResponse {
    private UUID itineraryId;
    private List<PlannedDay> days;
    private List<ApiError> warnings;
    
    public PlanItineraryResponse() {}
    
    public PlanItineraryResponse(UUID itineraryId, List<PlannedDay> days) {
        this.itineraryId = itineraryId;
        this.days = days;
    }
    
    public UUID getItineraryId() {
        return itineraryId;
    }
    
    public void setItineraryId(UUID itineraryId) {
        this.itineraryId = itineraryId;
    }
    
    public List<PlannedDay> getDays() {
        return days;
    }
    
    public void setDays(List<PlannedDay> days) {
        this.days = days;
    }
    
    public List<ApiError> getWarnings() {
        return warnings;
    }
    
    public void setWarnings(List<ApiError> warnings) {
        this.warnings = warnings;
    }
    
    @Override
    public String toString() {
        return "PlanItineraryResponse{" +
                "itineraryId=" + itineraryId +
                ", days=" + days +
                ", warnings=" + warnings +
                '}';
    }
}