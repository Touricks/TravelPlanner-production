package org.laioffer.planner.repository;

import org.laioffer.planner.entity.ItineraryPlaceEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ItineraryPlaceRepository extends JpaRepository<ItineraryPlaceEntity, UUID> {
    
    /**
     * Find all places for a specific itinerary
     */
    List<ItineraryPlaceEntity> findAllByItineraryId(UUID itineraryId);

    /**
     * Find a subset of places for a specific itinerary by their IDs.
     */
    List<ItineraryPlaceEntity> findAllByItineraryIdAndIdIn(UUID itineraryId, List<UUID> ids);
    
    /**
     * Check if a specific place is already added to an itinerary
     */
    boolean existsByItineraryIdAndPlaceId(UUID itineraryId, UUID placeId);

    /**
     * Find a specific place in an itinerary by itineraryId and placeId
     */
    Optional<ItineraryPlaceEntity> findByItineraryIdAndPlaceId(UUID itineraryId, UUID placeId);
    
    /**
     * Find places by itinerary and pinned status
     */
    List<ItineraryPlaceEntity> findByItineraryIdAndPinned(UUID itineraryId, boolean pinned);
    
    /**
     * Find pinned places for an itinerary
     */
    default List<ItineraryPlaceEntity> findPinnedPlaces(UUID itineraryId) {
        return findByItineraryIdAndPinned(itineraryId, true);
    }
    
    /**
     * Find unpinned places for an itinerary
     */
    default List<ItineraryPlaceEntity> findUnpinnedPlaces(UUID itineraryId) {
        return findByItineraryIdAndPinned(itineraryId, false);
    }
    
    /**
     * Delete a specific place from an itinerary
     */
    @Modifying
    @Transactional
    void deleteByItineraryIdAndPlaceId(UUID itineraryId, UUID placeId);
    
    /**
     * Count places in an itinerary
     */
    long countByItineraryId(UUID itineraryId);
    
    /**
     * Count pinned places in an itinerary
     */
    long countByItineraryIdAndPinned(UUID itineraryId, boolean pinned);
    
    /**
     * Get place IDs for an itinerary (useful for recommendation filtering)
     */
    @Query("SELECT ip.placeId FROM ItineraryPlaceEntity ip WHERE ip.itineraryId = :itineraryId")
    List<UUID> findPlaceIdsByItineraryId(@Param("itineraryId") UUID itineraryId);
    
    /**
     * Get only pinned place IDs for an itinerary (useful for recommendations)
     */
    @Query("SELECT ip.placeId FROM ItineraryPlaceEntity ip WHERE ip.itineraryId = :itineraryId AND ip.pinned = true")
    List<UUID> findPinnedPlaceIdsByItineraryId(@Param("itineraryId") UUID itineraryId);
    
    /**
     * Update pinned status for a specific itinerary-place combination
     */
    @Modifying
    @Transactional
    @Query("UPDATE ItineraryPlaceEntity ip SET ip.pinned = :pinned WHERE ip.itineraryId = :itineraryId AND ip.placeId = :placeId")
    void updatePinnedStatus(@Param("itineraryId") UUID itineraryId, 
                           @Param("placeId") UUID placeId, 
                           @Param("pinned") boolean pinned);
    
    /**
     * Update note for a specific itinerary-place combination
     */
    @Modifying
    @Transactional
    @Query("UPDATE ItineraryPlaceEntity ip SET ip.note = :note WHERE ip.itineraryId = :itineraryId AND ip.placeId = :placeId")
    void updateNote(@Param("itineraryId") UUID itineraryId,
                    @Param("placeId") UUID placeId,
                    @Param("note") String note);

    /**
     * Find ItineraryPlace by ID and verify user ownership in a single query.
     * Fetch joins ensure itinerary and user are available for downstream checks.
     */
    @Query("SELECT ip FROM ItineraryPlaceEntity ip " +
           "JOIN FETCH ip.itinerary i " +
           "JOIN FETCH i.user u " +
           "WHERE ip.id = :itineraryPlaceId AND u.id = :userId")
    Optional<ItineraryPlaceEntity> findByIdAndUserId(@Param("itineraryPlaceId") UUID itineraryPlaceId,
                                                     @Param("userId") Long userId);
}
