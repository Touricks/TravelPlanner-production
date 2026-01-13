package org.laioffer.planner.model.imports;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;

import java.util.List;

/**
 * The complete plan structure imported from CRAG.
 */
public class ImportedPlan {

    @NotBlank(message = "destination is required")
    private String destination;

    @NotBlank(message = "startDate is required")
    private String startDate;  // ISO format: "2025-03-01T10:00:00+09:00"

    @NotBlank(message = "endDate is required")
    private String endDate;

    @NotEmpty(message = "days cannot be empty")
    @Valid
    private List<ImportedDay> days;

    public ImportedPlan() {}

    // Getters and Setters
    public String getDestination() {
        return destination;
    }

    public void setDestination(String destination) {
        this.destination = destination;
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

    public List<ImportedDay> getDays() {
        return days;
    }

    public void setDays(List<ImportedDay> days) {
        this.days = days;
    }
}
