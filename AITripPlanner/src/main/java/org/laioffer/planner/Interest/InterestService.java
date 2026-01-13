package org.laioffer.planner.Interest;

import org.laioffer.planner.entity.UserEntity;

import java.util.UUID;

public interface InterestService {

    /**
     * Add a place to the itinerary's interest list or update its pinned status
     *
     * @param itineraryId UUID of the itinerary
     * @param request AddInterestRequest containing placeId and pinned status
     * @param user Authenticated user
     * @return AddInterestResponse with place details and pinned status
     * @throws IllegalArgumentException if placeId format is invalid
     * @throws SecurityException if user doesn't own the itinerary
     * @throws RuntimeException if itinerary or place not found
     */
    AddInterestResponse addInterest(UUID itineraryId, AddInterestRequest request, UserEntity user);
}