package org.laioffer.planner.itinerary.model.llm;

import dev.langchain4j.model.output.structured.Description;

public class POIRecommendationRequest {
    
    @Description("The destination city for which to generate POI recommendations")
    private String destinationCity;
    
    @Description("Number of POI recommendations to generate")
    private int maxRecommendations;
    
    @Description("Travel budget in cents (optional)")
    private Integer budgetInCents;
    
    @Description("Travel mode: DRIVING, TRANSIT, WALKING, or BICYCLING")
    private String travelMode;
    
    @Description("Daily start time in HH:mm format")
    private String dailyStart;
    
    @Description("Daily end time in HH:mm format")
    private String dailyEnd;
    
    @Description("Number of staying days")
    private int stayingDays;
    
    public POIRecommendationRequest() {}
    
    public POIRecommendationRequest(String destinationCity, int maxRecommendations) {
        this.destinationCity = destinationCity;
        this.maxRecommendations = maxRecommendations;
    }
    
    // Getters and Setters
    public String getDestinationCity() { return destinationCity; }
    public void setDestinationCity(String destinationCity) { this.destinationCity = destinationCity; }
    
    public int getMaxRecommendations() { return maxRecommendations; }
    public void setMaxRecommendations(int maxRecommendations) { this.maxRecommendations = maxRecommendations; }
    
    public Integer getBudgetInCents() { return budgetInCents; }
    public void setBudgetInCents(Integer budgetInCents) { this.budgetInCents = budgetInCents; }
    
    public String getTravelMode() { return travelMode; }
    public void setTravelMode(String travelMode) { this.travelMode = travelMode; }
    
    public String getDailyStart() { return dailyStart; }
    public void setDailyStart(String dailyStart) { this.dailyStart = dailyStart; }
    
    public String getDailyEnd() { return dailyEnd; }
    public void setDailyEnd(String dailyEnd) { this.dailyEnd = dailyEnd; }
    
    public int getStayingDays() { return stayingDays; }
    public void setStayingDays(int stayingDays) { this.stayingDays = stayingDays; }
}