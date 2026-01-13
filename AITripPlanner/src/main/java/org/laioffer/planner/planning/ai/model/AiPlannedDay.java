package org.laioffer.planner.planning.ai.model;

import dev.langchain4j.model.output.structured.Description;
import java.time.LocalDate;
import java.util.List;

/**
 * Represents a single day in the AI-generated travel plan.
 * AiPlannedDay.java - AI 生成的每日计划
 */
public class AiPlannedDay {

    @Description("Date of this day in YYYY-MM-DD format")
    private LocalDate date;

    @Description("Brief summary of the day's activities and theme")
    private String summary;

    @Description("List of stops/places to visit on this day in chronological order")
    private List<AiPlannedStop> stops;

    // Constructors
    public AiPlannedDay() {}

    // Getters and Setters
    public LocalDate getDate() {
        return date;
    }

    public void setDate(LocalDate date) {
        this.date = date;
    }

    public String getSummary() {
        return summary;
    }

    public void setSummary(String summary) {
        this.summary = summary;
    }

    public List<AiPlannedStop> getStops() {
        return stops;
    }

    public void setStops(List<AiPlannedStop> stops) {
        this.stops = stops;
    }
}
