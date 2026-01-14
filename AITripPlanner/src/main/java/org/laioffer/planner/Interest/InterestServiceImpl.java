package org.laioffer.planner.Interest;

import org.laioffer.planner.Recommendation.PlaceMapper;
import org.laioffer.planner.model.place.PlaceDTO;
import org.laioffer.planner.entity.ItineraryEntity;
import org.laioffer.planner.entity.ItineraryPlaceEntity;
import org.laioffer.planner.entity.PlaceEntity;
import org.laioffer.planner.entity.UserEntity;
import org.laioffer.planner.repository.ItineraryPlaceRepository;
import org.laioffer.planner.repository.ItineraryRepository;
import org.laioffer.planner.repository.PlaceRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
public class InterestServiceImpl implements InterestService {

    private static final Logger logger = LoggerFactory.getLogger(InterestServiceImpl.class);

    private final ItineraryPlaceRepository itineraryPlaceRepository;
    private final ItineraryRepository itineraryRepository;
    private final PlaceRepository placeRepository;
    private final PlaceMapper placeMapper;

    public InterestServiceImpl(
            ItineraryPlaceRepository itineraryPlaceRepository,
            ItineraryRepository itineraryRepository,
            PlaceRepository placeRepository,
            PlaceMapper placeMapper) {
        this.itineraryPlaceRepository = itineraryPlaceRepository;
        this.itineraryRepository = itineraryRepository;
        this.placeRepository = placeRepository;
        this.placeMapper = placeMapper;
    }
    
    @Override
    @Transactional
    public AddInterestResponse addInterest(UUID itineraryId, AddInterestRequest request, UserEntity user) {
        if (itineraryId == null) {
            throw new IllegalArgumentException("itineraryId must be provided");
        }

        if (request == null || request.getPlaceId() == null) {
            throw new IllegalArgumentException("placeId must be provided");
        }

        if (user == null || user.getId() == null) {
            throw new SecurityException("Authenticated user is required");
        }

        UUID placeId = request.getPlaceId();

        logger.info("Processing interest for placeId: {}, itineraryId: {}, user: {}",
                placeId, itineraryId, user.getEmail());

        // Find the ItineraryPlace record using itineraryId and placeId
        ItineraryPlaceEntity itineraryPlace = itineraryPlaceRepository
                .findByItineraryIdAndPlaceId(itineraryId, placeId)
                .orElseThrow(() -> new RuntimeException(
                        "Place " + placeId + " not found in itinerary " + itineraryId));

        // Verify user ownership
        ItineraryEntity itinerary = itineraryPlace.getItinerary();
        if (itinerary == null || itinerary.getUser() == null) {
            throw new RuntimeException(
                    "Itinerary not found for place: " + placeId);
        }

        Long ownerId = itinerary.getUser().getId();
        if (ownerId == null || !ownerId.equals(user.getId())) {
            logger.warn("Unauthorized access attempt by user {} on itinerary {} place {}",
                    user.getEmail(), itineraryId, placeId);
            throw new SecurityException(
                    "User does not own the itinerary for the requested place");
        }

        // Update pinned status
        itineraryPlace.setPinned(request.isPinned());
        ItineraryPlaceEntity updatedItineraryPlace = itineraryPlaceRepository.save(itineraryPlace);

        logger.info("Updated pinned status to {} for place: {} in itinerary: {}",
                request.isPinned(), placeId, itineraryId);

        PlaceDTO placeDTO = placeMapper.toItineraryPlaceDTO(updatedItineraryPlace);

        return new AddInterestResponse(placeDTO, updatedItineraryPlace.isPinned());
    }

    @Override
    @Transactional
    public void deletePlace(UUID itineraryId, UUID placeId, UserEntity user) {
        if (itineraryId == null) {
            throw new IllegalArgumentException("itineraryId must be provided");
        }

        if (placeId == null) {
            throw new IllegalArgumentException("placeId must be provided");
        }

        if (user == null || user.getId() == null) {
            throw new SecurityException("Authenticated user is required");
        }

        logger.info("Deleting place {} from itinerary {} for user {}",
                placeId, itineraryId, user.getEmail());

        // Find the ItineraryPlace record to verify ownership
        ItineraryPlaceEntity itineraryPlace = itineraryPlaceRepository
                .findByItineraryIdAndPlaceId(itineraryId, placeId)
                .orElseThrow(() -> new RuntimeException(
                        "Place " + placeId + " not found in itinerary " + itineraryId));

        // Verify user ownership
        ItineraryEntity itinerary = itineraryPlace.getItinerary();
        if (itinerary == null || itinerary.getUser() == null) {
            throw new RuntimeException(
                    "Itinerary not found for place: " + placeId);
        }

        Long ownerId = itinerary.getUser().getId();
        if (ownerId == null || !ownerId.equals(user.getId())) {
            logger.warn("Unauthorized delete attempt by user {} on itinerary {} place {}",
                    user.getEmail(), itineraryId, placeId);
            throw new SecurityException(
                    "User does not own the itinerary for the requested place");
        }

        // Hard delete the record
        itineraryPlaceRepository.deleteByItineraryIdAndPlaceId(itineraryId, placeId);

        logger.info("Successfully deleted place {} from itinerary {}", placeId, itineraryId);
    }

    @Override
    @Transactional
    public AddInterestResponse addPlace(UUID itineraryId, AddPlaceRequest request, UserEntity user) {
        if (itineraryId == null) {
            throw new IllegalArgumentException("itineraryId must be provided");
        }

        if (request == null || request.getName() == null || request.getName().isBlank()) {
            throw new IllegalArgumentException("Place name is required");
        }

        if (user == null || user.getId() == null) {
            throw new SecurityException("Authenticated user is required");
        }

        logger.info("Adding new place '{}' to itinerary {} for user {}",
                request.getName(), itineraryId, user.getEmail());

        // Find and verify itinerary ownership
        ItineraryEntity itinerary = itineraryRepository.findById(itineraryId)
                .orElseThrow(() -> new RuntimeException("Itinerary not found: " + itineraryId));

        if (itinerary.getUser() == null || !itinerary.getUser().getId().equals(user.getId())) {
            logger.warn("Unauthorized add attempt by user {} on itinerary {}",
                    user.getEmail(), itineraryId);
            throw new SecurityException("User does not own the itinerary");
        }

        // Try to find existing place by googlePlaceId (deduplication)
        PlaceEntity place = null;
        if (request.getGooglePlaceId() != null && !request.getGooglePlaceId().isBlank()) {
            place = placeRepository.findByGooglePlaceId(request.getGooglePlaceId()).orElse(null);
            if (place != null) {
                logger.info("Found existing place by googlePlaceId: {}", request.getGooglePlaceId());
            }
        }

        // Create new place if not found
        if (place == null) {
            place = new PlaceEntity();
            place.setName(request.getName());
            place.setAddress(request.getAddress());
            place.setLatitude(request.getLatitude());
            place.setLongitude(request.getLongitude());
            place.setImageUrl(request.getImageUrl());
            place.setDescription(request.getDescription());
            place.setSource(request.getSource());
            place.setGooglePlaceId(request.getGooglePlaceId());
            place = placeRepository.save(place);
            logger.info("Created new place with id: {}", place.getId());
        }

        // Check if place is already in itinerary
        if (itineraryPlaceRepository.existsByItineraryIdAndPlaceId(itineraryId, place.getId())) {
            throw new IllegalStateException("Place is already in this itinerary");
        }

        // Create itinerary-place association
        ItineraryPlaceEntity itineraryPlace = new ItineraryPlaceEntity();
        itineraryPlace.setItineraryId(itineraryId);
        itineraryPlace.setPlaceId(place.getId());
        itineraryPlace.setItinerary(itinerary);
        itineraryPlace.setPlace(place);
        itineraryPlace.setName(place.getName());
        itineraryPlace.setDescription(place.getDescription());
        itineraryPlace.setPinned(true); // New places are pinned by default
        itineraryPlace = itineraryPlaceRepository.save(itineraryPlace);

        logger.info("Successfully added place {} to itinerary {}", place.getId(), itineraryId);

        PlaceDTO placeDTO = placeMapper.toItineraryPlaceDTO(itineraryPlace);
        return new AddInterestResponse(placeDTO, true);
    }
}
