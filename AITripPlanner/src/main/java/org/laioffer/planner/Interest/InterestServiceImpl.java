package org.laioffer.planner.Interest;

import org.laioffer.planner.Recommendation.PlaceMapper;
import org.laioffer.planner.model.place.PlaceDTO;
import org.laioffer.planner.entity.ItineraryEntity;
import org.laioffer.planner.entity.ItineraryPlaceEntity;
import org.laioffer.planner.entity.UserEntity;
import org.laioffer.planner.repository.ItineraryPlaceRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
public class InterestServiceImpl implements InterestService {

    private static final Logger logger = LoggerFactory.getLogger(InterestServiceImpl.class);

    private final ItineraryPlaceRepository itineraryPlaceRepository;
    private final PlaceMapper placeMapper;

    public InterestServiceImpl(
            ItineraryPlaceRepository itineraryPlaceRepository,
            PlaceMapper placeMapper) {
        this.itineraryPlaceRepository = itineraryPlaceRepository;
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
}
