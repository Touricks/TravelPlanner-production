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

    /**
     * Remove a place from the itinerary completely (hard delete)
     *
     * @param itineraryId UUID of the itinerary
     * @param placeId UUID of the place to remove
     * @param user Authenticated user
     * @throws SecurityException if user doesn't own the itinerary
     * @throws RuntimeException if itinerary or place not found
     */
    void deletePlace(UUID itineraryId, UUID placeId, UserEntity user);

    /**
     * Add a new place to the itinerary (from Google Places or manual entry)
     *
     * @param itineraryId UUID of the itinerary
     * @param request AddPlaceRequest containing place details
     * @param user Authenticated user
     * @return AddInterestResponse with place details
     * @throws SecurityException if user doesn't own the itinerary
     * @throws IllegalStateException if place already exists in itinerary
     */
    AddInterestResponse addPlace(UUID itineraryId, AddPlaceRequest request, UserEntity user);
}