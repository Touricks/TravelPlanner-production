package org.laioffer.planner.model.planning;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonInclude;
import org.laioffer.planner.model.itinerary.TravelMode;

import java.time.OffsetDateTime;
import java.util.List;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class PlanItineraryRequest {
    private List<String> interestPlaceIds;
    
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ssXXX")
    private OffsetDateTime startDate;
    
    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ssXXX")
    private OffsetDateTime endDate;
    
    private TravelMode travelMode;
    private String dailyStart;
    private String dailyEnd;
    private boolean avoidCrowds = false;
    private boolean minimizeTransfers = false;
    private boolean balanceCategories = true;
    
    public PlanItineraryRequest() {}
    
    public List<String> getInterestPlaceIds() {
        return interestPlaceIds;
    }
    
    public void setInterestPlaceIds(List<String> interestPlaceIds) {
        this.interestPlaceIds = interestPlaceIds;
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
    
    public boolean isAvoidCrowds() {
        return avoidCrowds;
    }
    
    public void setAvoidCrowds(boolean avoidCrowds) {
        this.avoidCrowds = avoidCrowds;
    }
    
    public boolean isMinimizeTransfers() {
        return minimizeTransfers;
    }
    
    public void setMinimizeTransfers(boolean minimizeTransfers) {
        this.minimizeTransfers = minimizeTransfers;
    }
    
    public boolean isBalanceCategories() {
        return balanceCategories;
    }
    
    public void setBalanceCategories(boolean balanceCategories) {
        this.balanceCategories = balanceCategories;
    }
    
    @Override
    public String toString() {
        return "PlanItineraryRequest{" +
                "interestPlaceIds=" + interestPlaceIds +
                ", startDate=" + startDate +
                ", endDate=" + endDate +
                ", travelMode=" + travelMode +
                ", dailyStart='" + dailyStart + '\'' +
                ", dailyEnd='" + dailyEnd + '\'' +
                ", avoidCrowds=" + avoidCrowds +
                ", minimizeTransfers=" + minimizeTransfers +
                ", balanceCategories=" + balanceCategories +
                '}';
    }
}