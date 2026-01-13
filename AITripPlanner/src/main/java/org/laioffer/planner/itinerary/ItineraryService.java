package org.laioffer.planner.itinerary;

import org.laioffer.planner.model.itinerary.CreateItineraryRequest;
import org.laioffer.planner.entity.ItineraryEntity;
import org.laioffer.planner.entity.UserEntity;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.Optional;
import java.util.UUID;

public interface ItineraryService {
    
    /**
     * Creates a new itinerary and triggers async AI POI generation
     *
     * @param request The itinerary creation request containing trip details
     * @param user The authenticated user creating the itinerary
     * @return The created itinerary entity (with generation_pending=true)
     * @throws IllegalArgumentException if request validation fails
     */
    ItineraryEntity createItinerary(CreateItineraryRequest request, UserEntity user);
    
    /**
     * Retrieves an itinerary by its ID
     * 
     * @param itineraryId The UUID of the itinerary
     * @return Optional containing the itinerary if found
     */
    Optional<ItineraryEntity> getItinerary(UUID itineraryId);
    
    /**
     * Checks if an itinerary belongs to a specific user
     *
     * @param itineraryId The UUID of the itinerary
     * @param userId The ID of the user
     * @return true if the itinerary belongs to the user, false otherwise
     */
    boolean isItineraryOwnedByUser(UUID itineraryId, Long userId);

    /**
     * Retrieves a paginated list of itineraries for a specific user
     *
     * @param userId The ID of the user
     * @param pageable Pagination information
     * @return Page of itinerary entities
     */
    Page<ItineraryEntity> getUserItineraries(Long userId, Pageable pageable);

    /**
     * Retrieves an itinerary with its associated places eagerly loaded
     *
     * @param itineraryId The UUID of the itinerary
     * @return Optional containing the itinerary with places if found
     */
    Optional<ItineraryEntity> getItineraryWithPlaces(UUID itineraryId);
}