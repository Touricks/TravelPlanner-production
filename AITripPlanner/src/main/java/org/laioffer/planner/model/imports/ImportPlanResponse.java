package org.laioffer.planner.model.imports;

import java.util.List;
import java.util.UUID;

/**
 * Response for plan import operation.
 */
public class ImportPlanResponse {

    private UUID itineraryId;
    private String status;
    private int importedPoisCount;
    private int planVersion;
    private List<String> warnings;

    public ImportPlanResponse() {}

    public ImportPlanResponse(UUID itineraryId, String status, int importedPoisCount, int planVersion) {
        this.itineraryId = itineraryId;
        this.status = status;
        this.importedPoisCount = importedPoisCount;
        this.planVersion = planVersion;
    }

    public static ImportPlanResponse success(UUID itineraryId, int importedPoisCount, int planVersion) {
        return new ImportPlanResponse(itineraryId, "success", importedPoisCount, planVersion);
    }

    public static ImportPlanResponse withWarnings(UUID itineraryId, int importedPoisCount, int planVersion, List<String> warnings) {
        ImportPlanResponse response = new ImportPlanResponse(itineraryId, "success_with_warnings", importedPoisCount, planVersion);
        response.setWarnings(warnings);
        return response;
    }

    public static ImportPlanResponse updated(UUID itineraryId, int importedPoisCount, int planVersion) {
        return new ImportPlanResponse(itineraryId, "updated", importedPoisCount, planVersion);
    }

    public static ImportPlanResponse updatedWithWarnings(UUID itineraryId, int importedPoisCount, int planVersion, List<String> warnings) {
        ImportPlanResponse response = new ImportPlanResponse(itineraryId, "updated_with_warnings", importedPoisCount, planVersion);
        response.setWarnings(warnings);
        return response;
    }

    // Getters and Setters
    public UUID getItineraryId() {
        return itineraryId;
    }

    public void setItineraryId(UUID itineraryId) {
        this.itineraryId = itineraryId;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public int getImportedPoisCount() {
        return importedPoisCount;
    }

    public void setImportedPoisCount(int importedPoisCount) {
        this.importedPoisCount = importedPoisCount;
    }

    public int getPlanVersion() {
        return planVersion;
    }

    public void setPlanVersion(int planVersion) {
        this.planVersion = planVersion;
    }

    public List<String> getWarnings() {
        return warnings;
    }

    public void setWarnings(List<String> warnings) {
        this.warnings = warnings;
    }
}
