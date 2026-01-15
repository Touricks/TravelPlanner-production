package org.laioffer.planner.imports;

import org.laioffer.planner.model.imports.ImportPlanRequest;
import org.laioffer.planner.model.imports.ImportPlanResponse;

/**
 * Service for importing plans from CRAG system.
 */
public interface ImportService {

    /**
     * Import a complete plan from CRAG including POIs and itinerary.
     *
     * @param userId the ID of the authenticated user
     * @param request the import request containing POIs and plan data
     * @return response with the created itinerary ID and import statistics
     */
    ImportPlanResponse importPlan(Long userId, ImportPlanRequest request);

    /**
     * Update an existing plan from CRAG when cragSessionId already exists.
     * This will update itinerary metadata, clear and re-import POIs and Plan.
     *
     * @param userId the ID of the authenticated user
     * @param request the import request containing updated POIs and plan data
     * @return response with the updated itinerary ID and import statistics
     */
    ImportPlanResponse updatePlan(Long userId, ImportPlanRequest request);

    /**
     * Check if a plan with the given CRAG session ID has already been imported.
     * Used for idempotency.
     *
     * @param userId the user ID
     * @param cragSessionId the CRAG session ID
     * @return true if already imported
     */
    boolean isAlreadyImported(Long userId, String cragSessionId);
}
