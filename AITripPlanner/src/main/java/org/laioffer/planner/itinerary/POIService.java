package org.laioffer.planner.itinerary;

import org.laioffer.planner.model.place.PlaceDTO;
import org.laioffer.planner.entity.ItineraryEntity;
import org.laioffer.planner.entity.ItineraryPlaceEntity;
import org.laioffer.planner.entity.PlaceEntity;
import org.laioffer.planner.repository.ItineraryPlaceRepository;
import org.laioffer.planner.repository.PlaceRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@Transactional
public class POIService {

    private static final Logger logger = LoggerFactory.getLogger(POIService.class);

    private final PlaceRepository placeRepository;
    private final ItineraryPlaceRepository itineraryPlaceRepository;

    @Autowired
    public POIService(PlaceRepository placeRepository, ItineraryPlaceRepository itineraryPlaceRepository) {
        this.placeRepository = placeRepository;
        this.itineraryPlaceRepository = itineraryPlaceRepository;
    }
    
    /**
     * Creates PlaceEntity records from PlaceDTO and adds them to the itinerary
     * 
     * @param placeDTOs List of places from LLM
     * @param itinerary The itinerary to add places to
     * @return List of created PlaceEntity objects
     */
    public List<PlaceEntity> createAndAddPlacesToItinerary(List<PlaceDTO> placeDTOs, ItineraryEntity itinerary) {
        List<PlaceEntity> createdPlaces = new ArrayList<>();

        for (PlaceDTO placeDTO : placeDTOs) {
            try {
                PlaceEntity placeEntity = createPlaceEntity(placeDTO);
                PlaceEntity savedPlace = placeRepository.save(placeEntity);

                // Directly create and save ItineraryPlaceEntity to avoid lazy initialization errors
                // DO NOT use itinerary.addPlace() in async context as it accesses lazy-loaded collections
                ItineraryPlaceEntity itineraryPlace = new ItineraryPlaceEntity(itinerary, savedPlace, false, null);
                itineraryPlaceRepository.save(itineraryPlace);

                createdPlaces.add(savedPlace);

                logger.debug("Created place: {} for itinerary: {}", savedPlace.getName(), itinerary.getId());

            } catch (Exception e) {
                logger.error("Failed to create place: {}", placeDTO.getName(), e);
            }
        }

        logger.info("Created {} places for itinerary: {}", createdPlaces.size(), itinerary.getId());
        return createdPlaces;
    }
    
    private PlaceEntity createPlaceEntity(PlaceDTO placeDTO) {
        PlaceEntity place = new PlaceEntity();
        
        place.setName(placeDTO.getName());
        place.setAddress(placeDTO.getAddress());
        place.setDescription(placeDTO.getDescription());
        place.setImageUrl(placeDTO.getImageUrl());
        place.setSource("LLM_GENERATED");
        
        if (placeDTO.getLocation() != null) {
            place.setLatitude(BigDecimal.valueOf(placeDTO.getLocation().getLatitude()));
            place.setLongitude(BigDecimal.valueOf(placeDTO.getLocation().getLongitude()));
        }
        
        if (placeDTO.getContact() != null) {
            place.setWebsite(placeDTO.getContact().getWebsite());
            place.setPhone(placeDTO.getContact().getPhone());
            
            Map<String, Object> contactInfo = new HashMap<>();
            contactInfo.put("website", placeDTO.getContact().getWebsite());
            contactInfo.put("phone", placeDTO.getContact().getPhone());
            place.setContactInfo(contactInfo);
        }
        
        if (placeDTO.getOpeningHours() != null) {
            Map<String, Object> openingHours = new HashMap<>();
            openingHours.put("raw", placeDTO.getOpeningHours().getRaw());
            if (placeDTO.getOpeningHours().getNormalized() != null) {
                openingHours.put("normalized", placeDTO.getOpeningHours().getNormalized());
            }
            place.setOpeningHours(openingHours);
        }
        
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("generated_from", "llm");
        metadata.put("original_id", placeDTO.getId().toString());
        place.setMetadata(metadata);
        
        return place;
    }
}