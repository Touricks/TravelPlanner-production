package org.laioffer.planner.imports;

import org.laioffer.planner.entity.ItineraryEntity;
import org.laioffer.planner.entity.ItineraryPlaceEntity;
import org.laioffer.planner.entity.PlaceEntity;
import org.laioffer.planner.entity.PlanEntity;
import org.laioffer.planner.entity.UserEntity;
import org.laioffer.planner.model.common.GeoPoint;
import org.laioffer.planner.model.common.TravelPace;
import org.laioffer.planner.model.imports.*;
import org.laioffer.planner.model.itinerary.TravelMode;
import org.laioffer.planner.model.place.PlaceDTO;
import org.laioffer.planner.model.planning.PlannedDay;
import org.laioffer.planner.model.planning.PlannedStop;
import org.laioffer.planner.model.planning.PlanItineraryResponse;
import org.laioffer.planner.repository.ItineraryPlaceRepository;
import org.laioffer.planner.repository.ItineraryRepository;
import org.laioffer.planner.repository.PlaceRepository;
import org.laioffer.planner.repository.PlanRepository;
import org.laioffer.planner.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
public class ImportServiceImpl implements ImportService {

    private static final Logger logger = LoggerFactory.getLogger(ImportServiceImpl.class);

    private final UserRepository userRepository;
    private final ItineraryRepository itineraryRepository;
    private final PlaceRepository placeRepository;
    private final ItineraryPlaceRepository itineraryPlaceRepository;
    private final PlanRepository planRepository;

    public ImportServiceImpl(
            UserRepository userRepository,
            ItineraryRepository itineraryRepository,
            PlaceRepository placeRepository,
            ItineraryPlaceRepository itineraryPlaceRepository,
            PlanRepository planRepository) {
        this.userRepository = userRepository;
        this.itineraryRepository = itineraryRepository;
        this.placeRepository = placeRepository;
        this.itineraryPlaceRepository = itineraryPlaceRepository;
        this.planRepository = planRepository;
    }

    @Override
    @Transactional
    public ImportPlanResponse importPlan(Long userId, ImportPlanRequest request) {
        logger.info("Importing plan for user {} from CRAG session {}",
                userId, request.getCragSessionId());

        List<String> warnings = new ArrayList<>();

        // 1. Get user entity
        UserEntity user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("User not found: " + userId));

        // 2. Create Itinerary
        ItineraryEntity itinerary = createItinerary(user, request.getUserFeatures(), request.getPlan(), request.getCragSessionId());
        itinerary = itineraryRepository.save(itinerary);
        logger.info("Created itinerary {} for destination {}",
                itinerary.getId(), itinerary.getDestinationCity());

        // 3. Import POIs with deduplication
        Map<String, PlaceEntity> poiMap = importPOIs(request.getPois(), warnings);
        logger.info("Imported {} POIs", poiMap.size());

        // 4. Link places to itinerary
        linkPlacesToItinerary(itinerary, poiMap, request.getPois());

        // 5. Build and save plan
        PlanItineraryResponse planResponse = buildPlanResponse(
                itinerary.getId(), request.getPlan(), poiMap);
        int planVersion = savePlan(itinerary, planResponse);

        logger.info("Plan import completed. Itinerary: {}, POIs: {}, Version: {}",
                itinerary.getId(), poiMap.size(), planVersion);

        if (warnings.isEmpty()) {
            return ImportPlanResponse.success(itinerary.getId(), poiMap.size(), planVersion);
        } else {
            return ImportPlanResponse.withWarnings(itinerary.getId(), poiMap.size(), planVersion, warnings);
        }
    }

    @Override
    public boolean isAlreadyImported(Long userId, String cragSessionId) {
        if (cragSessionId == null || cragSessionId.isBlank()) {
            return false;
        }
        return itineraryRepository.existsByCragSessionId(cragSessionId);
    }

    @Override
    @Transactional
    public ImportPlanResponse updatePlan(Long userId, ImportPlanRequest request) {
        String cragSessionId = request.getCragSessionId();
        logger.info("Updating plan for user {} with CRAG session {}", userId, cragSessionId);

        List<String> warnings = new ArrayList<>();

        // 1. Find existing itinerary
        ItineraryEntity itinerary = itineraryRepository.findByCragSessionIdAndUserId(cragSessionId, userId)
                .orElseThrow(() -> new IllegalArgumentException(
                        "Itinerary not found for cragSessionId: " + cragSessionId));

        // 2. Update itinerary metadata
        updateItineraryMetadata(itinerary, request.getUserFeatures(), request.getPlan());
        itinerary = itineraryRepository.save(itinerary);
        logger.info("Updated itinerary {} metadata", itinerary.getId());

        // 3. IMPORTANT: Do NOT modify itinerary_places
        // User's pinned POI list should be preserved when continuing a conversation.
        // We only update the plan (schedule), not the interest list.
        logger.info("Preserving existing itinerary_places (pinned POIs) for itinerary {}", itinerary.getId());

        // 4. Build existing place map from current itinerary_places
        // This allows the plan to reference places the user has already saved
        Map<String, PlaceEntity> existingPoiMap = buildExistingPoiMap(itinerary.getId());
        logger.info("Found {} existing places in itinerary", existingPoiMap.size());

        // 5. Build and save new plan using existing places where available
        PlanItineraryResponse planResponse = buildPlanResponse(
                itinerary.getId(), request.getPlan(), existingPoiMap);
        int planVersion = savePlan(itinerary, planResponse);

        // Count how many stops have valid place references
        int existingPoiCount = (int) itineraryPlaceRepository.countByItineraryId(itinerary.getId());

        logger.info("Plan update completed. Itinerary: {}, Existing POIs: {}, Version: {}",
                itinerary.getId(), existingPoiCount, planVersion);

        if (warnings.isEmpty()) {
            return ImportPlanResponse.updated(itinerary.getId(), existingPoiCount, planVersion);
        } else {
            return ImportPlanResponse.updatedWithWarnings(itinerary.getId(), existingPoiCount, planVersion, warnings);
        }
    }

    /**
     * Build a map of existing places linked to the itinerary.
     * Used during plan updates to reference places without modifying itinerary_places.
     */
    private Map<String, PlaceEntity> buildExistingPoiMap(UUID itineraryId) {
        Map<String, PlaceEntity> poiMap = new HashMap<>();

        List<ItineraryPlaceEntity> itineraryPlaces = itineraryPlaceRepository.findAllByItineraryId(itineraryId);
        for (ItineraryPlaceEntity ip : itineraryPlaces) {
            PlaceEntity place = ip.getPlace();
            if (place != null) {
                // Map by place ID (as string)
                poiMap.put(place.getId().toString(), place);
                // Also map by google place ID if available
                if (place.getGooglePlaceId() != null) {
                    poiMap.put(place.getGooglePlaceId(), place);
                }
            }
        }

        return poiMap;
    }

    /**
     * Update itinerary metadata from user features and plan data.
     */
    private void updateItineraryMetadata(ItineraryEntity itinerary,
                                          ImportedUserFeatures features,
                                          ImportedPlan plan) {
        // Update destination
        itinerary.setDestinationCity(features.getDestination());

        // Update dates
        OffsetDateTime startDate = parseDateTime(plan.getStartDate());
        OffsetDateTime endDate = parseDateTime(plan.getEndDate());
        itinerary.setStartDate(startDate);
        itinerary.setEndDate(endDate);

        // Update budget
        itinerary.setBudgetInCents(features.getBudgetCents() != null ? features.getBudgetCents() : 0);

        // Update travel pace
        if (features.getTravelPace() != null) {
            try {
                itinerary.setTravelPace(TravelPace.valueOf(features.getTravelPace().toUpperCase()));
            } catch (IllegalArgumentException e) {
                itinerary.setTravelPace(TravelPace.MODERATE);
            }
        }

        // Update travel mode
        if (features.getTravelMode() != null) {
            try {
                itinerary.setTravelMode(TravelMode.valueOf(features.getTravelMode().toUpperCase()));
            } catch (IllegalArgumentException e) {
                itinerary.setTravelMode(TravelMode.WALKING);
            }
        }

        // Update preferences
        itinerary.setNumberOfTravelers(features.getNumberOfTravelers());
        itinerary.setHasChildren(features.getHasChildren());
        itinerary.setHasElderly(features.getHasElderly());

        // Update categories
        if (features.getInterests() != null) {
            itinerary.setPreferredCategories(features.getInterests());
        }

        // Update AI metadata
        Map<String, Object> aiMetadata = itinerary.getAiMetadata();
        if (aiMetadata == null) {
            aiMetadata = new HashMap<>();
        }
        aiMetadata.put("last_update_time", LocalDateTime.now().toString());
        aiMetadata.put("update_source", "crag");
        itinerary.setAiMetadata(aiMetadata);
    }

    /**
     * Create an ItineraryEntity from user features and plan data.
     */
    private ItineraryEntity createItinerary(UserEntity user, ImportedUserFeatures features, ImportedPlan plan, String cragSessionId) {
        ItineraryEntity itinerary = new ItineraryEntity();
        itinerary.setUser(user);
        itinerary.setDestinationCity(features.getDestination());
        itinerary.setCragSessionId(cragSessionId);

        // Parse dates
        OffsetDateTime startDate = parseDateTime(plan.getStartDate());
        OffsetDateTime endDate = parseDateTime(plan.getEndDate());
        itinerary.setStartDate(startDate);
        itinerary.setEndDate(endDate);

        // Budget
        itinerary.setBudgetInCents(features.getBudgetCents() != null ? features.getBudgetCents() : 0);

        // Travel pace
        if (features.getTravelPace() != null) {
            try {
                itinerary.setTravelPace(TravelPace.valueOf(features.getTravelPace().toUpperCase()));
            } catch (IllegalArgumentException e) {
                itinerary.setTravelPace(TravelPace.MODERATE);
            }
        } else {
            itinerary.setTravelPace(TravelPace.MODERATE);
        }

        // Travel mode
        if (features.getTravelMode() != null) {
            try {
                itinerary.setTravelMode(TravelMode.valueOf(features.getTravelMode().toUpperCase()));
            } catch (IllegalArgumentException e) {
                itinerary.setTravelMode(TravelMode.WALKING);
            }
        }

        // Other preferences
        itinerary.setNumberOfTravelers(features.getNumberOfTravelers());
        itinerary.setHasChildren(features.getHasChildren());
        itinerary.setHasElderly(features.getHasElderly());

        // Categories from interests
        if (features.getInterests() != null) {
            itinerary.setPreferredCategories(features.getInterests());
        }

        // Store CRAG metadata
        Map<String, Object> aiMetadata = new HashMap<>();
        aiMetadata.put("source", "crag");
        aiMetadata.put("import_time", LocalDateTime.now().toString());
        itinerary.setAiMetadata(aiMetadata);

        return itinerary;
    }

    /**
     * Import POIs with deduplication strategy: name + city match.
     */
    private Map<String, PlaceEntity> importPOIs(List<ImportedPOI> pois, List<String> warnings) {
        Map<String, PlaceEntity> result = new HashMap<>();

        for (ImportedPOI poi : pois) {
            PlaceEntity place = findOrCreatePlace(poi, warnings);
            result.put(poi.getExternalId(), place);
        }

        return result;
    }

    /**
     * Find existing place or create new one.
     * Deduplication: match by name and city.
     */
    private PlaceEntity findOrCreatePlace(ImportedPOI poi, List<String> warnings) {
        // For now, always create new place (future: add dedup query)
        // TODO: Add PlaceRepository.findByNameAndCity method for deduplication

        PlaceEntity place = new PlaceEntity();
        place.setName(poi.getName());
        place.setAddress(poi.getAddress());
        place.setLatitude(BigDecimal.valueOf(poi.getLatitude()));
        place.setLongitude(BigDecimal.valueOf(poi.getLongitude()));
        place.setDescription(poi.getDescription());
        place.setImageUrl(poi.getImageUrl());
        place.setSource("crag");

        // Store additional metadata
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("external_id", poi.getExternalId());
        metadata.put("city", poi.getCity());
        metadata.put("rating", poi.getRating());
        metadata.put("reviews_count", poi.getReviewsCount());
        metadata.put("price_level", poi.getPriceLevel());
        metadata.put("primary_category", poi.getPrimaryCategory());
        place.setMetadata(metadata);

        // Store opening hours if available
        if (poi.getOpeningHours() != null) {
            Map<String, Object> openingHours = new HashMap<>();
            openingHours.put("raw", poi.getOpeningHours());
            place.setOpeningHours(openingHours);
        }

        return placeRepository.save(place);
    }

    /**
     * Link all places to the itinerary.
     */
    private void linkPlacesToItinerary(ItineraryEntity itinerary,
                                       Map<String, PlaceEntity> poiMap,
                                       List<ImportedPOI> pois) {
        for (ImportedPOI poi : pois) {
            PlaceEntity place = poiMap.get(poi.getExternalId());
            if (place != null) {
                ItineraryPlaceEntity link = new ItineraryPlaceEntity(itinerary, place, true, null);
                link.setName(place.getName());
                link.setDescription(place.getDescription());
                itineraryPlaceRepository.save(link);
            }
        }
    }

    /**
     * Build PlanItineraryResponse from imported plan data.
     */
    private PlanItineraryResponse buildPlanResponse(UUID itineraryId,
                                                     ImportedPlan importedPlan,
                                                     Map<String, PlaceEntity> poiMap) {
        PlanItineraryResponse response = new PlanItineraryResponse();
        response.setItineraryId(itineraryId);

        List<PlannedDay> days = new ArrayList<>();
        for (ImportedDay importedDay : importedPlan.getDays()) {
            PlannedDay day = new PlannedDay();
            day.setDate(importedDay.getDate());

            List<PlannedStop> stops = new ArrayList<>();
            int order = 1;
            for (ImportedStop importedStop : importedDay.getStops()) {
                PlannedStop stop = new PlannedStop();
                stop.setOrder(order++);
                stop.setArrivalLocal(importedStop.getArrivalTime());
                stop.setDepartLocal(importedStop.getDepartureTime());
                stop.setStayMinutes(importedStop.getDurationMinutes() != null
                        ? importedStop.getDurationMinutes() : 60);
                stop.setNote(importedStop.getActivity());

                // Set place info
                PlaceEntity place = poiMap.get(importedStop.getPoiExternalId());
                if (place != null) {
                    stop.setPlace(convertToPlaceDTO(place));
                }

                stops.add(stop);
            }

            day.setStops(stops);
            days.add(day);
        }

        response.setDays(days);
        return response;
    }

    /**
     * Convert PlaceEntity to PlaceDTO.
     */
    private PlaceDTO convertToPlaceDTO(PlaceEntity place) {
        PlaceDTO dto = new PlaceDTO();
        dto.setId(place.getId());
        dto.setName(place.getName());
        dto.setAddress(place.getAddress());
        dto.setDescription(place.getDescription());
        dto.setImageUrl(place.getImageUrl());

        if (place.getLatitude() != null && place.getLongitude() != null) {
            dto.setLocation(new GeoPoint(
                    place.getLatitude().doubleValue(),
                    place.getLongitude().doubleValue()));
        }

        return dto;
    }

    /**
     * Save plan to database.
     */
    private int savePlan(ItineraryEntity itinerary, PlanItineraryResponse planResponse) {
        // Deactivate existing plans
        planRepository.deactivateAllPlansByItineraryId(itinerary.getId());

        // Get next version
        int nextVersion = planRepository.findMaxVersionByItineraryId(itinerary.getId()) + 1;

        // Convert to JSON Map
        Map<String, Object> planData = new HashMap<>();
        planData.put("itineraryId", planResponse.getItineraryId().toString());
        planData.put("days", planResponse.getDays());

        // Save
        PlanEntity planEntity = new PlanEntity(itinerary, planData, nextVersion);
        planRepository.save(planEntity);

        return nextVersion;
    }

    /**
     * Parse ISO datetime string to OffsetDateTime.
     */
    private OffsetDateTime parseDateTime(String dateTimeStr) {
        try {
            // Try full ISO format first: "2025-03-01T10:00:00+09:00"
            return OffsetDateTime.parse(dateTimeStr);
        } catch (Exception e1) {
            try {
                // Try date-only format: "2025-03-01"
                return OffsetDateTime.of(
                        java.time.LocalDate.parse(dateTimeStr).atTime(9, 0),
                        ZoneOffset.UTC);
            } catch (Exception e2) {
                logger.warn("Failed to parse date: {}, using current time", dateTimeStr);
                return OffsetDateTime.now();
            }
        }
    }
}
