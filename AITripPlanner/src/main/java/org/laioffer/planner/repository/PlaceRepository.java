package org.laioffer.planner.repository;

import org.laioffer.planner.entity.ItineraryPlaceEntity;
import org.laioffer.planner.entity.PlaceEntity;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface PlaceRepository extends JpaRepository<PlaceEntity, UUID> {
    
    /**
     * Find all itinerary places that belong to the current itinerary
     * @param itineraryId The itinerary ID
     * @param query Optional keyword search (can be null)
     * @param pageable Pagination parameters
     * @return Page of itinerary places (both pinned and unpinned)
     */
    @Query("SELECT ip FROM ItineraryPlaceEntity ip " +
           "WHERE ip.itineraryId = :itineraryId " +
           "AND (:query IS NULL OR :query = '' OR " +
           " LOWER(ip.name) LIKE LOWER(CONCAT('%', :query, '%')) OR " +
           " LOWER(ip.description) LIKE LOWER(CONCAT('%', :query, '%')))")

    Page<ItineraryPlaceEntity> findItineraryPlacesByItinerary(
            @Param("itineraryId") UUID itineraryId,
            @Param("query") String query,
            Pageable pageable
    );
    
    /**
     * Find places within a geographic bounding box (for future location-based recommendations)
     * This is a placeholder for future geographic filtering
     */
    @Query("SELECT p FROM PlaceEntity p WHERE " +
           "p.latitude BETWEEN :minLat AND :maxLat AND " +
           "p.longitude BETWEEN :minLng AND :maxLng")
    List<PlaceEntity> findPlacesInBounds(
            @Param("minLat") Double minLatitude,
            @Param("maxLat") Double maxLatitude,
            @Param("minLng") Double minLongitude,
            @Param("maxLng") Double maxLongitude
    );
}