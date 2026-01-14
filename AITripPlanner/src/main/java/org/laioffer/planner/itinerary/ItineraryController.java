package org.laioffer.planner.itinerary;

import org.laioffer.planner.entity.ItineraryEntity;
import org.laioffer.planner.entity.ItineraryPlaceEntity;
import org.laioffer.planner.entity.PlaceEntity;
import org.laioffer.planner.model.common.ActivityIntensity;
import org.laioffer.planner.model.common.AttractionCategory;
import org.laioffer.planner.model.common.GeoPoint;
import org.laioffer.planner.model.common.PageMeta;
import org.laioffer.planner.model.itinerary.CreateItineraryRequest;
import org.laioffer.planner.model.itinerary.CreateItineraryResponse;
import org.laioffer.planner.entity.UserEntity;
import org.laioffer.planner.model.itinerary.GetItinerariesResponse;
import org.laioffer.planner.model.itinerary.ItineraryDetailResponse;
import org.laioffer.planner.model.itinerary.ItinerarySummaryDTO;
import org.laioffer.planner.model.place.PlaceDTO;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/itineraries")
public class ItineraryController {
    
    private static final Logger logger = LoggerFactory.getLogger(ItineraryController.class);
    private final ItineraryService itineraryService;
    public ItineraryController(ItineraryService itineraryService) {
        this.itineraryService = itineraryService;
    }
    
    /**
     * Creates a new itinerary and triggers async AI-generated place recommendations
     *
     * @param request CreateItineraryRequest containing trip details
     * @param user Authenticated user from JWT token
     * @return HTTP 202 Accepted with itinerary ID and status
     */
    @PostMapping
    public ResponseEntity<CreateItineraryResponse> createItinerary(
            @Validated @RequestBody CreateItineraryRequest request,
            @AuthenticationPrincipal UserEntity user) {
        logger.info("Creating itinerary for user: {} to destination: {}",
                user.getEmail(), request.getDestinationCity());
        logger.info("🔍 DEBUG - Received request: travelPace={}, activityIntensity={}",
                request.getTravelPace(), request.getActivityIntensity());
        logger.info("🔍 DEBUG - Full request: {}", request);
        try {
            ItineraryEntity itinerary = itineraryService.createItinerary(request, user);

            CreateItineraryResponse response = new CreateItineraryResponse();
            response.setItineraryId(itinerary.getId());
            response.setDestinationCity(itinerary.getDestinationCity());
            response.setStartDate(itinerary.getStartDate());
            response.setEndDate(itinerary.getEndDate());
            response.setTravelMode(itinerary.getTravelMode());
            response.setBudgetLimitCents(itinerary.getBudgetInCents());
            response.setBudgetPerMealCents(itinerary.getBudgetPerMealCents());

            return new ResponseEntity<>(response, HttpStatus.ACCEPTED);
        } catch (Exception e) {
            logger.error("Error creating itinerary for user {}: {}",
                    user.getEmail(), e.getMessage(), e);
            return new ResponseEntity<>(HttpStatus.BAD_REQUEST);
        }
    }

    /**
     * Retrieves a paginated list of itineraries for the authenticated user
     *
     * @param page Page number (0-indexed)
     * @param size Page size
     * @param user Authenticated user from JWT token
     * @return HTTP 200 OK with GetItinerariesResponse
     */
    @GetMapping
    public ResponseEntity<GetItinerariesResponse> getUserItineraries(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @AuthenticationPrincipal UserEntity user) {
        logger.info("Fetching itineraries for user: {}, page: {}, size: {}",
                user.getEmail(), page, size);

        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "createdAt"));
        Page<ItineraryEntity> itinerariesPage = itineraryService.getUserItineraries(user.getId(), pageable);

        List<ItinerarySummaryDTO> summaries = itinerariesPage.getContent().stream()
                .map(this::convertToSummaryDTO)
                .collect(Collectors.toList());

        PageMeta pageMeta = new PageMeta(
                itinerariesPage.getNumber(),
                itinerariesPage.getSize(),
                itinerariesPage.getTotalElements(),
                itinerariesPage.getTotalPages()
        );

        GetItinerariesResponse response = new GetItinerariesResponse(summaries, pageMeta);
        return ResponseEntity.ok(response);
    }

    /**
     * Retrieves detailed information about a specific itinerary
     *
     * @param itineraryId UUID of the itinerary
     * @param user Authenticated user from JWT token
     * @return HTTP 200 OK with ItineraryDetailResponse, 403 if not owner, 404 if not found
     */
    @GetMapping("/{itineraryId}")
    public ResponseEntity<ItineraryDetailResponse> getItineraryById(
            @PathVariable UUID itineraryId,
            @AuthenticationPrincipal UserEntity user) {
        logger.info("Fetching itinerary {} for user: {}", itineraryId, user.getEmail());

        // Check ownership
        if (!itineraryService.isItineraryOwnedByUser(itineraryId, user.getId())) {
            logger.warn("User {} attempted to access itinerary {} they don't own",
                    user.getEmail(), itineraryId);
            return ResponseEntity.status(HttpStatus.FORBIDDEN).build();
        }

        Optional<ItineraryEntity> itineraryOpt = itineraryService.getItineraryWithPlaces(itineraryId);

        if (itineraryOpt.isEmpty()) {
            logger.warn("Itinerary {} not found", itineraryId);
            return ResponseEntity.notFound().build();
        }

        ItineraryDetailResponse response = convertToDetailResponse(itineraryOpt.get());
        return ResponseEntity.ok(response);
    }

    /**
     * Converts ItineraryEntity to ItinerarySummaryDTO
     */
    private ItinerarySummaryDTO convertToSummaryDTO(ItineraryEntity entity) {
        return new ItinerarySummaryDTO(
                entity.getId(),
                entity.getDestinationCity(),
                entity.getStartDate(),
                entity.getEndDate(),
                entity.getTravelMode(),
                entity.getBudgetInCents(),
                entity.getTravelPace(),
                entity.getCreatedAt()
        );
    }

    /**
     * Converts ItineraryEntity to ItineraryDetailResponse
     */
    private ItineraryDetailResponse convertToDetailResponse(ItineraryEntity entity) {
        ItineraryDetailResponse response = new ItineraryDetailResponse();

        response.setId(entity.getId());
        response.setDestinationCity(entity.getDestinationCity());
        response.setStartDate(entity.getStartDate());
        response.setEndDate(entity.getEndDate());
        response.setTravelMode(entity.getTravelMode());
        response.setBudgetLimitCents(entity.getBudgetInCents());
        response.setBudgetPerMealCents(entity.getBudgetPerMealCents());

        response.setTravelPace(entity.getTravelPace());
        response.setActivityIntensity(entity.getActivityIntensity());
        response.setNumberOfTravelers(entity.getNumberOfTravelers());
        response.setHasChildren(entity.getHasChildren());
        response.setHasElderly(entity.getHasElderly());
        response.setPreferPopularAttractions(entity.getPreferPopularAttractions());

        // Convert preferredCategories from List<String> to List<AttractionCategory>
        if (entity.getPreferredCategories() != null) {
            List<AttractionCategory> categories = entity.getPreferredCategories().stream()
                    .map(s -> {
                        try {
                            return AttractionCategory.valueOf(s.toUpperCase());
                        } catch (IllegalArgumentException e) {
                            return null; // Skip invalid categories
                        }
                    })
                    .filter(c -> c != null)
                    .collect(Collectors.toList());
            response.setPreferredCategories(categories);
        }

        response.setAdditionalPreferences(entity.getAdditionalPreferences());
        response.setSeededRecommendations(entity.getSeededRecommendations());
        response.setAiMetadata(entity.getAiMetadata());
        response.setCragSessionId(entity.getCragSessionId());
        response.setCreatedAt(entity.getCreatedAt());
        response.setUpdatedAt(entity.getUpdatedAt());

        // Convert itineraryPlaces to PlaceDTOs
        if (entity.getItineraryPlaces() != null && !entity.getItineraryPlaces().isEmpty()) {
            List<PlaceDTO> places = entity.getItineraryPlaces().stream()
                    .map(this::convertToPlaceDTO)
                    .collect(Collectors.toList());
            response.setPlaces(places);
        }

        return response;
    }

    /**
     * Converts ItineraryPlaceEntity to PlaceDTO
     */
    private PlaceDTO convertToPlaceDTO(ItineraryPlaceEntity ipEntity) {
        PlaceEntity place = ipEntity.getPlace();

        PlaceDTO dto = new PlaceDTO();
        dto.setId(place.getId());
        dto.setName(place.getName());

        if (place.getLatitude() != null && place.getLongitude() != null) {
            dto.setLocation(new GeoPoint(
                    place.getLatitude().doubleValue(),
                    place.getLongitude().doubleValue()
            ));
        }

        dto.setAddress(place.getAddress());
        dto.setImageUrl(place.getImageUrl());
        dto.setDescription(place.getDescription());

        // Itinerary-specific fields
        dto.setItineraryPlaceRecordId(ipEntity.getId());
        dto.setPinned(ipEntity.isPinned());
        dto.setNote(ipEntity.getNote());
        dto.setAddedAt(ipEntity.getAddedAt());

        return dto;
    }

}