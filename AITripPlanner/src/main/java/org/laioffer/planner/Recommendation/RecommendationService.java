package org.laioffer.planner.Recommendation;

import org.laioffer.planner.entity.ItineraryPlaceEntity;
import org.laioffer.planner.model.common.PageMeta;
import org.laioffer.planner.model.itinerary.GetRecommendationsResponse;
import org.laioffer.planner.model.place.PlaceDTO;
import org.laioffer.planner.repository.ItineraryPlaceRepository;
import org.laioffer.planner.repository.PlaceRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class RecommendationService {
    
    private final ItineraryPlaceRepository itineraryPlaceRepository;
    private final PlaceRepository placeRepository;
    private final PlaceMapper placeMapper;
    
    @Autowired
    public RecommendationService(
            ItineraryPlaceRepository itineraryPlaceRepository,
            PlaceRepository placeRepository,
            PlaceMapper placeMapper) {
        this.itineraryPlaceRepository = itineraryPlaceRepository;
        this.placeRepository = placeRepository;
        this.placeMapper = placeMapper;
    }
    
    /**
     * Get recommendations for an itinerary, excluding pinned places
     * 
     * @param itineraryId UUID of the itinerary
     * @param query Optional keyword search
     * @param page Page number (0-based)
     * @param size Page size
     * @return GetRecommendationsResponse with paginated results
     */
    public GetRecommendationsResponse getRecommendations(UUID itineraryId, String query, int page, int size) {
        // Validate input parameters
        validateInputs(itineraryId, page, size);
        
        // Create pageable with sorting (by name for consistent results)
        Pageable pageable = PageRequest.of(page, size, Sort.by("name").ascending());
        
        // Query all itinerary places that belong to this itinerary (both pinned and unpinned)
        Page<ItineraryPlaceEntity> itineraryPlacePage = placeRepository.findItineraryPlacesByItinerary(
                itineraryId,
                sanitizeQuery(query), 
                pageable
        );
        
        // Convert itinerary place entities to DTOs
        List<PlaceDTO> placeDTOs = itineraryPlacePage.getContent().stream()
                .map(this::convertItineraryPlaceToDTO)
                .collect(Collectors.toList());
        
        // Build page metadata
        PageMeta pageMeta = new PageMeta(
                page,
                size,
                itineraryPlacePage.getTotalElements(),
                itineraryPlacePage.getTotalPages()
        );
        
        return new GetRecommendationsResponse(itineraryId, placeDTOs, pageMeta);
    }
    
    /**
     * Get statistics about recommendations for an itinerary
     * 
     * @param itineraryId UUID of the itinerary
     * @return Statistics object with counts
     */
    public RecommendationStats getRecommendationStats(UUID itineraryId) {
        long totalPlaces = placeRepository.count();
        long pinnedPlaces = itineraryPlaceRepository.countByItineraryIdAndPinned(itineraryId, true);
        long unpinnedPlaces = itineraryPlaceRepository.countByItineraryIdAndPinned(itineraryId, false);
        long totalSaved = pinnedPlaces + unpinnedPlaces;
        long availableRecommendations = totalPlaces - pinnedPlaces;
        
        return new RecommendationStats(
                totalPlaces,
                pinnedPlaces,
                unpinnedPlaces,
                totalSaved,
                availableRecommendations
        );
    }
    
    /**
     * Validate input parameters
     */
    private void validateInputs(UUID itineraryId, int page, int size) {
        if (itineraryId == null) {
            throw new IllegalArgumentException("Itinerary ID cannot be null");
        }
        
        if (page < 0) {
            throw new IllegalArgumentException("Page number cannot be negative");
        }
        
        if (size <= 0 || size > 200) {
            throw new IllegalArgumentException("Page size must be between 1 and 200");
        }
    }
    
    /**
     * Sanitize and prepare query string for search
     */
    private String sanitizeQuery(String query) {
        if (query == null) {
            return null;
        }
        
        String trimmed = query.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }
    
    /**
     * Convert ItineraryPlaceEntity to PlaceDTO using denormalized fields
     */
    private PlaceDTO convertItineraryPlaceToDTO(ItineraryPlaceEntity itineraryPlace) {
        return placeMapper.toItineraryPlaceDTO(itineraryPlace);
    }

    /**
     * Statistics class for recommendation information
     */
    public static class RecommendationStats {
        private final long totalPlaces;
        private final long pinnedPlaces;
        private final long unpinnedPlaces;
        private final long totalSaved;
        private final long availableRecommendations;
        
        public RecommendationStats(long totalPlaces, long pinnedPlaces, long unpinnedPlaces, 
                                  long totalSaved, long availableRecommendations) {
            this.totalPlaces = totalPlaces;
            this.pinnedPlaces = pinnedPlaces;
            this.unpinnedPlaces = unpinnedPlaces;
            this.totalSaved = totalSaved;
            this.availableRecommendations = availableRecommendations;
        }
        
        // Getters
        public long getTotalPlaces() { return totalPlaces; }
        public long getPinnedPlaces() { return pinnedPlaces; }
        public long getUnpinnedPlaces() { return unpinnedPlaces; }
        public long getTotalSaved() { return totalSaved; }
        public long getAvailableRecommendations() { return availableRecommendations; }
    }
}