package org.laioffer.planner.model.imports;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;

import java.util.List;

/**
 * Request body for importing a plan from CRAG system.
 */
public class ImportPlanRequest {

    private String cragSessionId;

    @NotNull(message = "userFeatures is required")
    @Valid
    private ImportedUserFeatures userFeatures;

    @NotEmpty(message = "pois cannot be empty")
    @Valid
    private List<ImportedPOI> pois;

    @NotNull(message = "plan is required")
    @Valid
    private ImportedPlan plan;

    public ImportPlanRequest() {}

    // Getters and Setters
    public String getCragSessionId() {
        return cragSessionId;
    }

    public void setCragSessionId(String cragSessionId) {
        this.cragSessionId = cragSessionId;
    }

    public ImportedUserFeatures getUserFeatures() {
        return userFeatures;
    }

    public void setUserFeatures(ImportedUserFeatures userFeatures) {
        this.userFeatures = userFeatures;
    }

    public List<ImportedPOI> getPois() {
        return pois;
    }

    public void setPois(List<ImportedPOI> pois) {
        this.pois = pois;
    }

    public ImportedPlan getPlan() {
        return plan;
    }

    public void setPlan(ImportedPlan plan) {
        this.plan = plan;
    }
}
