package org.laioffer.planner.planning;

import org.laioffer.planner.model.planning.PlanItineraryRequest;
import org.laioffer.planner.model.planning.PlanItineraryResponse;
import org.laioffer.planner.model.planning.PlannedDay;
import org.laioffer.planner.model.planning.PlannedStop;
import org.laioffer.planner.entity.ItineraryEntity;
import org.laioffer.planner.entity.ItineraryPlaceEntity;
import org.laioffer.planner.planning.ai.model.*;
import org.laioffer.planner.planning.exception.ItineraryNotFoundException;
import org.laioffer.planner.repository.ItineraryPlaceRepository;
import org.laioffer.planner.repository.ItineraryRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.CollectionUtils;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class PlanningServiceImpl implements PlanningService {

    private static final Logger logger = LoggerFactory.getLogger(PlanningServiceImpl.class);

    private final ItineraryRepository itineraryRepository;
    private final ItineraryPlaceRepository itineraryPlaceRepository;
    private final PlanningLLMService planningLLMService;
    private final org.laioffer.planner.Recommendation.PlaceMapper placeMapper;
    private final org.laioffer.planner.repository.PlanRepository planRepository;

    public PlanningServiceImpl(
            ItineraryRepository itineraryRepository,
            ItineraryPlaceRepository itineraryPlaceRepository,
            PlanningLLMService planningLLMService,
            org.laioffer.planner.Recommendation.PlaceMapper placeMapper,
            org.laioffer.planner.repository.PlanRepository planRepository) {
        this.itineraryRepository = itineraryRepository;
        this.itineraryPlaceRepository = itineraryPlaceRepository;
        this.planningLLMService = planningLLMService;
        this.placeMapper = placeMapper;
        this.planRepository = planRepository;
    }

    @Override
    public boolean isItineraryOwnedByUser(UUID itineraryId, Long userId) {
        return itineraryRepository.existsByIdAndUserId(itineraryId, userId);
    }

    @Override
    @Transactional
    public PlanItineraryResponse generatePlan(UUID itineraryId, PlanItineraryRequest request) {
        // 1. Fetch the core itinerary information from the database.
        // If not found, this will throw an ItineraryNotFoundException.
        ItineraryEntity itinerary = itineraryRepository.findById(itineraryId)
                .orElseThrow(() -> new ItineraryNotFoundException("Itinerary with id " + itineraryId + " not found."));

        logger.info("Generating plan for itinerary {} in {}", itineraryId, itinerary.getDestinationCity());

        // 2. Fetch the list of places the user is interested in.
        // If the request specifies a list of places, use that. Otherwise, use only
        // pinned places (user-selected) from the itinerary's interest list.
        List<ItineraryPlaceEntity> interestedPlaces;
        if (CollectionUtils.isEmpty(request.getInterestPlaceIds())) {
            List<ItineraryPlaceEntity> allPlaces = itineraryPlaceRepository.findAllByItineraryId(itineraryId);
            interestedPlaces = allPlaces.stream()
                    .filter(ItineraryPlaceEntity::isPinned)
                    .collect(Collectors.toList());
            logger.debug("Filtered {} pinned places out of {} total places for planning",
                    interestedPlaces.size(), allPlaces.size());
        } else {
            List<UUID> placeIds = request.getInterestPlaceIds().stream().map(UUID::fromString).toList();
            interestedPlaces = itineraryPlaceRepository.findAllByItineraryIdAndIdIn(itineraryId, placeIds);
            logger.debug("Using {} explicitly specified places for planning", interestedPlaces.size());
        }

        // 3. Convert places to AI format
        List<AiPlaceInfo> aiPlaces = interestedPlaces.stream()
                .map(this::convertToAiPlaceInfo)
                .collect(Collectors.toList());

        logger.debug("Converted {} places to AI format. First place note value: '{}'",
                aiPlaces.size(), aiPlaces.isEmpty() ? "N/A" : aiPlaces.get(0).getNote());

        // 4. Prepare parameters for AI service
        LocalDate startDate = itinerary.getStartDate().toLocalDate();
        LocalDate endDate = itinerary.getEndDate().toLocalDate();
        String travelMode = itinerary.getTravelMode() != null ? itinerary.getTravelMode().name() : "WALKING";
        Integer budgetInCents = itinerary.getBudgetInCents() != null ? itinerary.getBudgetInCents() : 0;
        Double budgetInDollars = budgetInCents / 100.0;

        // Parse daily start/end times from request, or use defaults
        LocalTime dailyStart = request.getDailyStart() != null ? LocalTime.parse(request.getDailyStart()) : LocalTime.of(9, 0);
        LocalTime dailyEnd = request.getDailyEnd() != null ? LocalTime.parse(request.getDailyEnd()) : LocalTime.of(20, 0);

        // 5. Call LangChain4j AI service with retry logic
        AiPlanResponse aiResponse;
        try {
            aiResponse = planningLLMService.generatePlan(
                    itineraryId,
                    itinerary.getDestinationCity(),
                    startDate,
                    endDate,
                    travelMode,
                    budgetInCents,
                    budgetInDollars,
                    dailyStart,
                    dailyEnd,
                    aiPlaces
            );
        } catch (Exception e) {
            logger.error("Failed to generate plan for itinerary {}: {}", itineraryId, e.getMessage(), e);
            throw new RuntimeException("Failed to generate travel plan: " + e.getMessage(), e);
        }

        // 6. Validate and deduplicate the AI response to ensure no duplicate POIs
        aiResponse = validateAndDeduplicatePlan(aiResponse);

        // 7. Process the AI response and format it into PlanItineraryResponse
        PlanItineraryResponse planResponse = buildPlanResponse(itineraryId, aiResponse);

        // 8. Save the generated plan to database
        savePlan(itineraryId, planResponse);

        return planResponse;
    }

    /**
     * Converts an ItineraryPlaceEntity to AiPlaceInfo for the AI request.
     */
    private AiPlaceInfo convertToAiPlaceInfo(ItineraryPlaceEntity itineraryPlace) {
        AiPlaceInfo aiPlace = new AiPlaceInfo();

        aiPlace.setPlaceId(itineraryPlace.getPlaceId());
        aiPlace.setName(itineraryPlace.getName() != null ? itineraryPlace.getName() : "");
        aiPlace.setPinned(itineraryPlace.isPinned());
        aiPlace.setNote(itineraryPlace.getNote() != null ? itineraryPlace.getNote() : "");

        // Get place details if available - ensure all fields are non-null for Mustache template
        if (itineraryPlace.getPlace() != null) {
            aiPlace.setAddress(itineraryPlace.getPlace().getAddress() != null ? itineraryPlace.getPlace().getAddress() : "");
            aiPlace.setLatitude(itineraryPlace.getPlace().getLatitude());
            aiPlace.setLongitude(itineraryPlace.getPlace().getLongitude());
            aiPlace.setDescription(itineraryPlace.getPlace().getDescription() != null ? itineraryPlace.getPlace().getDescription() : "");
        } else {
            aiPlace.setAddress("");
            aiPlace.setDescription("");
        }

        return aiPlace;
    }

    /**
     * Converts the AI response into the API response format.
     */
    private PlanItineraryResponse buildPlanResponse(UUID itineraryId, AiPlanResponse aiResponse) {
        PlanItineraryResponse response = new PlanItineraryResponse();

        // Set the itinerary ID
        response.setItineraryId(itineraryId);

        // Convert AI days to API format
        List<PlannedDay> days = aiResponse.getDays().stream()
                .map(aiDay -> convertToPlannedDay(itineraryId, aiDay))
                .collect(Collectors.toList());
        response.setDays(days);

        return response;
    }

    /**
     * Converts an AI planned day to the API PlannedDay format.
     */
    private PlannedDay convertToPlannedDay(UUID itineraryId, AiPlannedDay aiDay) {
        PlannedDay day = new PlannedDay();

        // Convert date to String format
        day.setDate(aiDay.getDate() != null ? aiDay.getDate().toString() : null);

        // Convert stops with order
        List<PlannedStop> stops = new java.util.ArrayList<>();
        for (int i = 0; i < aiDay.getStops().size(); i++) {
            stops.add(convertToPlannedStop(itineraryId, aiDay.getStops().get(i), i + 1));
        }
        day.setStops(stops);

        return day;
    }

    /**
     * Converts an AI planned stop to the API PlannedStop format.
     */
    private PlannedStop convertToPlannedStop(UUID itineraryId, AiPlannedStop aiStop, int order) {
        PlannedStop stop = new PlannedStop();

        // Set order
        stop.setOrder(order);

        // Set timing information
        stop.setArrivalLocal(aiStop.getArrivalTime() != null ? aiStop.getArrivalTime().toString() : null);
        stop.setDepartLocal(aiStop.getDepartureTime() != null ? aiStop.getDepartureTime().toString() : null);
        stop.setStayMinutes(aiStop.getDurationMinutes() != null ? aiStop.getDurationMinutes() : 0);
        stop.setNote(aiStop.getActivity());

        // Fetch and set place information if placeId is available
        if (aiStop.getPlaceId() != null) {
            itineraryPlaceRepository.findByItineraryIdAndPlaceId(itineraryId, aiStop.getPlaceId()).ifPresent(itineraryPlace -> {
                // Use PlaceMapper to convert ItineraryPlaceEntity to PlaceDTO
                org.laioffer.planner.model.place.PlaceDTO placeDTO = placeMapper.toItineraryPlaceDTO(itineraryPlace);
                stop.setPlace(placeDTO);
            });
        }

        return stop;
    }

    @Override
    @Transactional
    public PlanItineraryResponse savePlan(UUID itineraryId, PlanItineraryResponse plan) {
        // Fetch the itinerary
        ItineraryEntity itinerary = itineraryRepository.findById(itineraryId)
                .orElseThrow(() -> new ItineraryNotFoundException("Itinerary with id " + itineraryId + " not found."));

        logger.info("Saving plan for itinerary {}", itineraryId);

        // Convert PlanItineraryResponse to JSON Map
        Map<String, Object> planData = convertPlanToMap(plan);

        // Get next version number
        Integer nextVersion = planRepository.findMaxVersionByItineraryId(itineraryId) + 1;

        // Deactivate all existing plans for this itinerary
        planRepository.deactivateAllPlansByItineraryId(itineraryId);

        // Create and save new plan entity
        org.laioffer.planner.entity.PlanEntity planEntity = new org.laioffer.planner.entity.PlanEntity(
                itinerary, planData, nextVersion
        );
        planRepository.save(planEntity);

        logger.info("Plan saved successfully for itinerary {} with version {}", itineraryId, nextVersion);

        return plan;
    }

    @Override
    @Transactional(readOnly = true)
    public java.util.Optional<PlanItineraryResponse> getActivePlan(UUID itineraryId) {
        logger.info("Retrieving active plan for itinerary {}", itineraryId);

        return planRepository.findByItineraryIdAndIsActiveTrue(itineraryId)
                .map(planEntity -> convertMapToPlan(planEntity.getPlanData(), itineraryId));
    }

    @Override
    @Transactional(readOnly = true)
    public java.util.List<PlanItineraryResponse> getPlanHistory(UUID itineraryId) {
        logger.info("Retrieving plan history for itinerary {}", itineraryId);

        return planRepository.findAllByItineraryIdOrderByCreatedAtDesc(itineraryId).stream()
                .map(planEntity -> convertMapToPlan(planEntity.getPlanData(), itineraryId))
                .collect(Collectors.toList());
    }

    /**
     * Convert PlanItineraryResponse to Map for JSON storage
     */
    private Map<String, Object> convertPlanToMap(PlanItineraryResponse plan) {
        Map<String, Object> planMap = new java.util.HashMap<>();
        planMap.put("itineraryId", plan.getItineraryId().toString());
        planMap.put("days", plan.getDays());
        if (plan.getWarnings() != null) {
            planMap.put("warnings", plan.getWarnings());
        }
        return planMap;
    }

    /**
     * Convert Map from JSON storage to PlanItineraryResponse
     */
    private PlanItineraryResponse convertMapToPlan(Map<String, Object> planData, UUID itineraryId) {
        PlanItineraryResponse response = new PlanItineraryResponse();
        response.setItineraryId(itineraryId);

        // Convert days
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> daysData = (List<Map<String, Object>>) planData.get("days");
        if (daysData != null) {
            List<PlannedDay> days = daysData.stream()
                    .map(this::convertMapToPlannedDay)
                    .collect(Collectors.toList());
            response.setDays(days);
        }

        // Convert warnings if present
        if (planData.containsKey("warnings")) {
            @SuppressWarnings("unchecked")
            List<org.laioffer.planner.model.common.ApiError> warnings =
                (List<org.laioffer.planner.model.common.ApiError>) planData.get("warnings");
            response.setWarnings(warnings);
        }

        return response;
    }

    /**
     * Convert Map to PlannedDay
     */
    private PlannedDay convertMapToPlannedDay(Map<String, Object> dayData) {
        PlannedDay day = new PlannedDay();
        day.setDate((String) dayData.get("date"));

        @SuppressWarnings("unchecked")
        List<Map<String, Object>> stopsData = (List<Map<String, Object>>) dayData.get("stops");
        if (stopsData != null) {
            List<PlannedStop> stops = stopsData.stream()
                    .map(this::convertMapToPlannedStop)
                    .collect(Collectors.toList());
            day.setStops(stops);
        }

        return day;
    }

    /**
     * Convert Map to PlannedStop
     */
    private PlannedStop convertMapToPlannedStop(Map<String, Object> stopData) {
        PlannedStop stop = new PlannedStop();

        if (stopData.get("order") != null) {
            stop.setOrder(((Number) stopData.get("order")).intValue());
        }
        stop.setArrivalLocal((String) stopData.get("arrivalLocal"));
        stop.setDepartLocal((String) stopData.get("departLocal"));
        if (stopData.get("stayMinutes") != null) {
            stop.setStayMinutes(((Number) stopData.get("stayMinutes")).intValue());
        }
        stop.setNote((String) stopData.get("note"));

        // Convert place data if present
        @SuppressWarnings("unchecked")
        Map<String, Object> placeData = (Map<String, Object>) stopData.get("place");
        if (placeData != null) {
            org.laioffer.planner.model.place.PlaceDTO placeDTO = convertMapToPlaceDTO(placeData);
            stop.setPlace(placeDTO);
        }

        return stop;
    }

    /**
     * Validates the AI-generated plan and removes duplicate POIs.
     * If the same placeId appears multiple times across different days,
     * only the first occurrence is kept, and subsequent duplicates are removed.
     *
     * @param aiResponse the AI-generated plan response
     * @return the validated and deduplicated plan response
     */
    private AiPlanResponse validateAndDeduplicatePlan(AiPlanResponse aiResponse) {
        if (aiResponse == null || aiResponse.getDays() == null) {
            return aiResponse;
        }

        java.util.Set<UUID> seenPlaceIds = new java.util.HashSet<>();
        int totalRemovedDuplicates = 0;

        for (AiPlannedDay day : aiResponse.getDays()) {
            if (day.getStops() == null) {
                continue;
            }

            List<AiPlannedStop> originalStops = new java.util.ArrayList<>(day.getStops());
            List<AiPlannedStop> validStops = new java.util.ArrayList<>();

            for (AiPlannedStop stop : originalStops) {
                UUID placeId = stop.getPlaceId();

                if (placeId == null) {
                    // Keep stops without placeId (e.g., free time, breaks)
                    validStops.add(stop);
                } else if (!seenPlaceIds.contains(placeId)) {
                    // First occurrence of this place - keep it
                    seenPlaceIds.add(placeId);
                    validStops.add(stop);
                } else {
                    // Duplicate detected - skip this stop
                    totalRemovedDuplicates++;
                    logger.warn("Duplicate POI detected and removed: placeId={}, placeName={}, date={}",
                            placeId, stop.getPlaceName(), day.getDate());
                }
            }

            // Update the day with deduplicated stops
            day.setStops(validStops);
        }

        if (totalRemovedDuplicates > 0) {
            logger.warn("Total {} duplicate POI(s) removed from the generated plan", totalRemovedDuplicates);
        } else {
            logger.info("Plan validation passed - no duplicate POIs found");
        }

        return aiResponse;
    }

    /**
     * Convert Map to PlaceDTO
     */
    private org.laioffer.planner.model.place.PlaceDTO convertMapToPlaceDTO(Map<String, Object> placeData) {
        org.laioffer.planner.model.place.PlaceDTO placeDTO = new org.laioffer.planner.model.place.PlaceDTO();

        if (placeData.get("id") != null) {
            placeDTO.setId(UUID.fromString((String) placeData.get("id")));
        }
        placeDTO.setName((String) placeData.get("name"));
        placeDTO.setAddress((String) placeData.get("address"));

        @SuppressWarnings("unchecked")
        Map<String, Object> locationData = (Map<String, Object>) placeData.get("location");
        if (locationData != null) {
            org.laioffer.planner.model.common.GeoPoint location = new org.laioffer.planner.model.common.GeoPoint(
                    ((Number) locationData.get("lat")).doubleValue(),
                    ((Number) locationData.get("lng")).doubleValue()
            );
            placeDTO.setLocation(location);
        }

        placeDTO.setDescription((String) placeData.get("description"));
        placeDTO.setImageUrl((String) placeData.get("imageUrl"));

        if (placeData.get("itineraryPlaceRecordId") != null) {
            placeDTO.setItineraryPlaceRecordId(UUID.fromString((String) placeData.get("itineraryPlaceRecordId")));
        }

        if (placeData.get("pinned") != null) {
            placeDTO.setPinned((Boolean) placeData.get("pinned"));
        }
        placeDTO.setNote((String) placeData.get("note"));

        return placeDTO;
    }
}
