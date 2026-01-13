package org.laioffer.planner.model.imports;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;

import java.util.List;

/**
 * A single day in the imported plan.
 */
public class ImportedDay {

    @NotBlank(message = "date is required")
    private String date;  // "2025-03-01"

    @NotEmpty(message = "stops cannot be empty")
    @Valid
    private List<ImportedStop> stops;

    public ImportedDay() {}

    // Getters and Setters
    public String getDate() {
        return date;
    }

    public void setDate(String date) {
        this.date = date;
    }

    public List<ImportedStop> getStops() {
        return stops;
    }

    public void setStops(List<ImportedStop> stops) {
        this.stops = stops;
    }
}
