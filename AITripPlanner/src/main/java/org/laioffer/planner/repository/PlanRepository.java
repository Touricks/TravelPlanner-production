package org.laioffer.planner.repository;

import org.laioffer.planner.entity.PlanEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface PlanRepository extends JpaRepository<PlanEntity, UUID> {

    /**
     * Find the active plan for a specific itinerary
     */
    Optional<PlanEntity> findByItineraryIdAndIsActiveTrue(UUID itineraryId);

    /**
     * Find all plans for a specific itinerary, ordered by creation date (newest first)
     */
    List<PlanEntity> findAllByItineraryIdOrderByCreatedAtDesc(UUID itineraryId);

    /**
     * Get the highest version number for an itinerary's plans
     */
    @Query("SELECT COALESCE(MAX(p.version), 0) FROM PlanEntity p WHERE p.itinerary.id = :itineraryId")
    Integer findMaxVersionByItineraryId(@Param("itineraryId") UUID itineraryId);

    /**
     * Deactivate all plans for a specific itinerary
     */
    @Modifying
    @Query("UPDATE PlanEntity p SET p.isActive = false WHERE p.itinerary.id = :itineraryId AND p.isActive = true")
    void deactivateAllPlansByItineraryId(@Param("itineraryId") UUID itineraryId);
}
