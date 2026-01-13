package org.laioffer.planner.planning;

import org.laioffer.planner.model.planning.PlanItineraryRequest;
import org.laioffer.planner.model.planning.PlanItineraryResponse;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface PlanningService {
    PlanItineraryResponse generatePlan(UUID itineraryId, PlanItineraryRequest request);

    boolean isItineraryOwnedByUser(UUID itineraryId, Long userId);

    /**
     * Save a plan to the database
     *
     * @param itineraryId UUID of the itinerary
     * @param plan The plan response to save
     * @return The saved plan response
     */
    PlanItineraryResponse savePlan(UUID itineraryId, PlanItineraryResponse plan);

    /**
     * Get the active plan for an itinerary
     *
     * @param itineraryId UUID of the itinerary
     * @return Optional containing the active plan, or empty if no active plan exists
     */
    Optional<PlanItineraryResponse> getActivePlan(UUID itineraryId);

    /**
     * Get all plans for an itinerary (history)
     *
     * @param itineraryId UUID of the itinerary
     * @return List of all plans ordered by creation date (newest first)
     */
    List<PlanItineraryResponse> getPlanHistory(UUID itineraryId);
}
