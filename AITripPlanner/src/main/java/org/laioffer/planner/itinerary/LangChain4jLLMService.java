package org.laioffer.planner.itinerary;

import org.laioffer.planner.model.place.PlaceDTO;
import org.laioffer.planner.model.common.GeoPoint;
import org.laioffer.planner.model.place.ContactDTO;
import org.laioffer.planner.model.place.OpeningHoursDTO;
import org.laioffer.planner.entity.ItineraryEntity;
import org.laioffer.planner.itinerary.model.llm.POIRecommendationResponse;
import org.laioffer.planner.itinerary.model.llm.LLMRecommendedPOI;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Service
public class LangChain4jLLMService {
    
    private static final Logger logger = LoggerFactory.getLogger(LangChain4jLLMService.class);
    private static final int MAX_RETRIES = 3;
    
    private final POIRecommendationService poiRecommendationService;
    
    public LangChain4jLLMService(POIRecommendationService poiRecommendationService) {
        this.poiRecommendationService = poiRecommendationService;
    }
    
    public List<PlaceDTO> generatePOIRecommendations(ItineraryEntity itinerary, int maxRecommendations) throws Exception {
        List<String> errorLog = new ArrayList<>();
        
        for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
            try {
                logger.debug("LangChain4j generation attempt {} for itinerary {}", attempt, itinerary.getId());
                
                POIRecommendationResponse response;
                if (attempt == 1) {
                    response = generateInitialRecommendations(itinerary, maxRecommendations);
                } else {
                    response = generateRecommendationsWithErrorFeedback(itinerary, maxRecommendations, errorLog);
                }
                
                List<PlaceDTO> places = convertToDTOs(response);
                
                if (!places.isEmpty()) {
                    logger.info("Successfully generated {} POI recommendations for itinerary {} using LangChain4j", 
                            places.size(), itinerary.getId());
                    return places;
                }
                
                errorLog.add("No valid places were returned from the AI service");
                
            } catch (Exception e) {
                String errorMessage = "Attempt " + attempt + " failed: " + e.getMessage();
                errorLog.add(errorMessage);
                
                logger.warn("LangChain4j generation attempt {} failed for itinerary {}: {}", 
                        attempt, itinerary.getId(), e.getMessage());
                
                if (attempt == MAX_RETRIES) {
                    throw new Exception("Failed to generate POI recommendations after " + MAX_RETRIES + " attempts using LangChain4j. Errors: " + String.join("; ", errorLog), e);
                }
            }
        }
        
        throw new Exception("Failed to generate valid POI recommendations using LangChain4j. Errors: " + String.join("; ", errorLog));
    }
    
    private POIRecommendationResponse generateInitialRecommendations(ItineraryEntity itinerary, int maxRecommendations) {
        // Provide non-null default values for ALL fields to avoid LangChain4j template errors
        // Mustache templates require all variables to exist, even in conditional blocks

        Integer budgetInCents = itinerary.getBudgetInCents() != null ? itinerary.getBudgetInCents() : 0;
        Double budgetInDollars = budgetInCents / 100.0;
        String travelMode = itinerary.getTravelMode() != null ? itinerary.getTravelMode().toString() : "WALKING";

        // Calculate staying days
        Integer stayingDays = 1;
        if (itinerary.getStartDate() != null && itinerary.getEndDate() != null) {
            long daysBetween = java.time.temporal.ChronoUnit.DAYS.between(
                itinerary.getStartDate().toLocalDate(),
                itinerary.getEndDate().toLocalDate()
            );
            stayingDays = (int) daysBetween;
            if (stayingDays == 0) {
                stayingDays = 1;
            }
        }

        // Extract user preferences with non-null defaults
        String travelPace = itinerary.getTravelPace() != null ? itinerary.getTravelPace().toString() : "MODERATE";
        String activityIntensity = itinerary.getActivityIntensity() != null ? itinerary.getActivityIntensity().toString() : "MODERATE";
        Integer numberOfTravelers = itinerary.getNumberOfTravelers() != null ? itinerary.getNumberOfTravelers() : 1;
        Boolean hasChildren = itinerary.getHasChildren() != null ? itinerary.getHasChildren() : false;
        Boolean hasElderly = itinerary.getHasElderly() != null ? itinerary.getHasElderly() : false;
        Boolean preferPopularAttractions = itinerary.getPreferPopularAttractions() != null ? itinerary.getPreferPopularAttractions() : true;
        // Fetch from entity (now eagerly loaded)
        java.util.List<String> preferredCategories = itinerary.getPreferredCategories();
        if (preferredCategories == null) {
            preferredCategories = new ArrayList<>();  // Ensure non-null for template
        }
        // Convert List to comma-separated string for Mustache template
        String preferredCategoriesStr = preferredCategories.isEmpty() ? "Any" : String.join(", ", preferredCategories);
        String additionalPreferences = (itinerary.getAdditionalPreferences() != null && !itinerary.getAdditionalPreferences().trim().isEmpty())
            ? itinerary.getAdditionalPreferences()
            : "None";

        return poiRecommendationService.generatePOIRecommendations(
                itinerary.getDestinationCity(),
                maxRecommendations,
                budgetInCents,  // Pass non-null value
                budgetInDollars,
                travelMode,
                stayingDays,
                travelPace,
                activityIntensity,
                numberOfTravelers,
                hasChildren,
                hasElderly,
                preferPopularAttractions,
                preferredCategoriesStr,
                additionalPreferences
        );
    }
    
    private POIRecommendationResponse generateRecommendationsWithErrorFeedback(
            ItineraryEntity itinerary, int maxRecommendations, List<String> errorLog) {

        // Provide default values for null fields to avoid LangChain4j template errors
        Integer budgetInCents = itinerary.getBudgetInCents() != null ? itinerary.getBudgetInCents() : 0;
        Double budgetInDollars = budgetInCents / 100.0;
        String travelMode = itinerary.getTravelMode() != null ? itinerary.getTravelMode().toString() : "WALKING";

        return poiRecommendationService.generatePOIRecommendationsWithErrorFeedback(
                itinerary.getDestinationCity(),
                maxRecommendations,
                budgetInCents,
                budgetInDollars,
                travelMode,
                errorLog
        );
    }
    
    private List<PlaceDTO> convertToDTOs(POIRecommendationResponse response) throws Exception {
        if (response == null || response.getRecommendations() == null) {
            return new ArrayList<>();
        }
        
        List<PlaceDTO> places = new ArrayList<>();
        List<String> validationErrors = new ArrayList<>();
        
        for (int i = 0; i < response.getRecommendations().size(); i++) {
            LLMRecommendedPOI poi = response.getRecommendations().get(i);
            try {
                PlaceDTO place = convertToDTO(poi);
                if (place != null) {
                    places.add(place);
                }
            } catch (Exception e) {
                validationErrors.add("POI " + (i + 1) + ": " + e.getMessage());
                logger.warn("Failed to convert POI {} to PlaceDTO: {}", poi.getName(), e.getMessage());
            }
        }
        
        if (places.isEmpty() && !validationErrors.isEmpty()) {
            throw new Exception("No valid places could be converted. Errors: " + String.join("; ", validationErrors));
        }
        
        return places;
    }
    
    private PlaceDTO convertToDTO(LLMRecommendedPOI poi) {
        if (poi == null) {
            throw new IllegalArgumentException("POI cannot be null");
        }
        
        // Validate required fields
        if (poi.getName() == null || poi.getName().trim().isEmpty()) {
            throw new IllegalArgumentException("POI name is required");
        }
        
        if (poi.getAddress() == null || poi.getAddress().trim().isEmpty()) {
            throw new IllegalArgumentException("POI address is required");
        }
        
        if (poi.getDescription() == null || poi.getDescription().trim().isEmpty()) {
            throw new IllegalArgumentException("POI description is required");
        }
        
        if (poi.getLocation() == null) {
            throw new IllegalArgumentException("POI location is required");
        }
        
        // Validate coordinates
        double lat = poi.getLocation().getLatitude();
        double lng = poi.getLocation().getLongitude();
        
        if (lat < -90 || lat > 90) {
            throw new IllegalArgumentException("Invalid latitude: " + lat + " (must be between -90 and 90)");
        }
        
        if (lng < -180 || lng > 180) {
            throw new IllegalArgumentException("Invalid longitude: " + lng + " (must be between -180 and 180)");
        }
        
        // Create PlaceDTO
        PlaceDTO place = new PlaceDTO();
        place.setId(UUID.randomUUID());
        place.setName(poi.getName().trim());
        place.setAddress(poi.getAddress().trim());
        place.setDescription(poi.getDescription().trim());
        place.setImageUrl(poi.getImageUrl());
        
        // Set location
        GeoPoint location = new GeoPoint();
        location.setLatitude(lat);
        location.setLongitude(lng);
        place.setLocation(location);
        
        // Set contact information (optional)
        if (poi.getContact() != null) {
            ContactDTO contact = new ContactDTO();
            contact.setWebsite(poi.getContact().getWebsite());
            contact.setPhone(poi.getContact().getPhone());
            place.setContact(contact);
        }
        
        // Set opening hours (optional)
        if (poi.getOpeningHours() != null && poi.getOpeningHours().getRaw() != null) {
            OpeningHoursDTO hours = new OpeningHoursDTO();
            hours.setRaw(poi.getOpeningHours().getRaw());
            place.setOpeningHours(hours);
        }
        
        return place;
    }
}