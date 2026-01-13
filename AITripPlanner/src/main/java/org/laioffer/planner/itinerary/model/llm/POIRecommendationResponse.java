package org.laioffer.planner.itinerary.model.llm;

import dev.langchain4j.model.output.structured.Description;
import java.util.List;

public class POIRecommendationResponse {

    @Description("List of recommended points of interest")
    private List<LLMRecommendedPOI> recommendations;

    @Description("Total number of recommendations provided")
    private int totalCount;

    @Description("Any warnings or notes about the recommendations (optional)")
    private String notes;

    public POIRecommendationResponse() {}

    public POIRecommendationResponse(List<LLMRecommendedPOI> recommendations) {
        this.recommendations = recommendations;
        this.totalCount = recommendations != null ? recommendations.size() : 0;
    }

    // Getters and Setters
    public List<LLMRecommendedPOI> getRecommendations() { return recommendations; }
    public void setRecommendations(List<LLMRecommendedPOI> recommendations) {
        this.recommendations = recommendations;
        this.totalCount = recommendations != null ? recommendations.size() : 0;
    }

    public int getTotalCount() { return totalCount; }
    public void setTotalCount(int totalCount) { this.totalCount = totalCount; }

    public String getNotes() { return notes; }
    public void setNotes(String notes) { this.notes = notes; }
}
