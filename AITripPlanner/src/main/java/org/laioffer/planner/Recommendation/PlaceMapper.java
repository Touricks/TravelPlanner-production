package org.laioffer.planner.Recommendation;

import org.laioffer.planner.entity.PlaceEntity;
import org.laioffer.planner.entity.ItineraryPlaceEntity;
import org.laioffer.planner.model.common.GeoPoint;
import org.laioffer.planner.model.place.ContactDTO;
import org.laioffer.planner.model.place.DailyHours;
import org.laioffer.planner.model.place.OpeningHoursDTO;
import org.laioffer.planner.model.place.PlaceDTO;
import org.laioffer.planner.model.place.TimeRange;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

@Component
public class PlaceMapper {
    /**
     * Convert ItineraryPlaceEntity to PlaceDTO using denormalized fields
     */
    public PlaceDTO toItineraryPlaceDTO(ItineraryPlaceEntity itineraryPlace) {
        if (itineraryPlace == null) {
            return null;
        }

        PlaceEntity place = itineraryPlace.getPlace();
        if (place == null) {
            // Still try to build a minimal DTO from itineraryPlace denormalized data
            PlaceDTO dto = new PlaceDTO();
            dto.setId(itineraryPlace.getPlaceId()); // Use placeId from itineraryPlace
            dto.setName(itineraryPlace.getName() != null ? itineraryPlace.getName() : "Unknown Place");
            dto.setDescription(itineraryPlace.getDescription());
            dto.setAddress("Address not available");

            // Set default location to avoid null pointer
            dto.setLocation(new GeoPoint(0.0, 0.0));

            // Itinerary-specific fields
            dto.setItineraryPlaceRecordId(itineraryPlace.getId());
            dto.setPinned(itineraryPlace.isPinned());
            dto.setNote(itineraryPlace.getNote());
            dto.setAddedAt(itineraryPlace.getAddedAt());

            return dto;
        }

        PlaceDTO dto = new PlaceDTO();

        // Basic place fields with null safety
        dto.setId(place.getId());
        dto.setAddress(place.getAddress() != null ? place.getAddress() : "Address not available");
        dto.setImageUrl(place.getImageUrl());

        // Use denormalized fields from ItineraryPlaceEntity with fallback to place entity
        dto.setName(itineraryPlace.getName() != null ? itineraryPlace.getName() :
                    (place.getName() != null ? place.getName() : "Unknown Place"));
        dto.setDescription(itineraryPlace.getDescription() != null ? itineraryPlace.getDescription() :
                          place.getDescription());

        // Itinerary-specific fields
        dto.setItineraryPlaceRecordId(itineraryPlace.getId());
        dto.setPinned(itineraryPlace.isPinned());
        dto.setNote(itineraryPlace.getNote());
        dto.setAddedAt(itineraryPlace.getAddedAt());

        // Convert coordinates to GeoPoint with null safety
        if (place.getLatitude() != null && place.getLongitude() != null) {
            GeoPoint location = new GeoPoint(
                place.getLatitude().doubleValue(),
                place.getLongitude().doubleValue()
            );
            dto.setLocation(location);
        } else {
            // Set default location if coordinates are missing
            dto.setLocation(new GeoPoint(0.0, 0.0));
        }

        // Convert contact info from JSONB
        ContactDTO contact = extractContactInfo(place);
        if (contact != null) {
            dto.setContact(contact);
        }

        // Convert opening hours from JSONB
        OpeningHoursDTO openingHours = extractOpeningHours(place);
        if (openingHours != null) {
            dto.setOpeningHours(openingHours);
        }

        return dto;
    }
    
    /**
     * Extract contact information from entity
     */
    private ContactDTO extractContactInfo(PlaceEntity entity) {
        ContactDTO contact = new ContactDTO();
        boolean hasContact = false;
        
        // Use direct fields first
        if (entity.getWebsite() != null) {
            contact.setWebsite(entity.getWebsite());
            hasContact = true;
        }
        
        if (entity.getPhone() != null) {
            contact.setPhone(entity.getPhone());
            hasContact = true;
        }
        
        // Try to extract from contactInfo JSONB if direct fields are null
        if (!hasContact && entity.getContactInfo() != null) {
            Map<String, Object> contactInfo = entity.getContactInfo();
            
            Object website = contactInfo.get("website");
            if (website instanceof String) {
                contact.setWebsite((String) website);
                hasContact = true;
            }
            
            Object phone = contactInfo.get("phone");
            if (phone instanceof String) {
                contact.setPhone((String) phone);
                hasContact = true;
            }
        }
        
        return hasContact ? contact : null;
    }
    
    /**
     * Extract opening hours from entity
     */
    private OpeningHoursDTO extractOpeningHours(PlaceEntity entity) {
        if (entity.getOpeningHours() == null) {
            return null;
        }
        
        Map<String, Object> hoursData = entity.getOpeningHours();
        OpeningHoursDTO openingHours = new OpeningHoursDTO();
        
        try {
            // Parse normalized hours from nested weekday objects
            List<DailyHours> normalizedHours = parseNormalizedHours(hoursData);
            openingHours.setNormalized(normalizedHours);
            
            // Generate readable raw text
            String rawText = generateRawText(hoursData);
            openingHours.setRaw(rawText);
            
        } catch (Exception e) {
            // Fallback to raw string representation if parsing fails
            openingHours.setRaw(hoursData.toString());
        }
        
        return openingHours;
    }
    
    /**
     * Parse normalized hours from JSONB weekday objects
     * Expected format: {"monday": {"open": "00:00", "close": "23:59"}, ...}
     */
    private List<DailyHours> parseNormalizedHours(Map<String, Object> hoursData) {
        List<DailyHours> dailyHoursList = new ArrayList<>();
        List<String> weekdays = Arrays.asList("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday");
        
        for (String weekday : weekdays) {
            Object dayData = hoursData.get(weekday);
            if (dayData instanceof Map) {
                @SuppressWarnings("unchecked")
                Map<String, Object> dayMap = (Map<String, Object>) dayData;
                
                Object openTime = dayMap.get("open");
                Object closeTime = dayMap.get("close");
                
                if (openTime instanceof String && closeTime instanceof String) {
                    TimeRange timeRange = new TimeRange((String) openTime, (String) closeTime);
                    List<TimeRange> timeRanges = new ArrayList<>();
                    timeRanges.add(timeRange);
                    
                    DailyHours dailyHours = new DailyHours(weekday, timeRanges);
                    dailyHoursList.add(dailyHours);
                }
            }
        }
        
        return dailyHoursList;
    }
    
    /**
     * Generate readable raw text from hours data
     */
    private String generateRawText(Map<String, Object> hoursData) {
        StringBuilder rawText = new StringBuilder();
        List<String> weekdays = Arrays.asList("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday");
        
        for (int i = 0; i < weekdays.size(); i++) {
            String weekday = weekdays.get(i);
            Object dayData = hoursData.get(weekday);
            
            if (i > 0) {
                rawText.append(", ");
            }
            
            rawText.append(capitalizeFirst(weekday)).append(": ");
            
            if (dayData instanceof Map) {
                @SuppressWarnings("unchecked")
                Map<String, Object> dayMap = (Map<String, Object>) dayData;
                Object openTime = dayMap.get("open");
                Object closeTime = dayMap.get("close");
                
                if (openTime instanceof String && closeTime instanceof String) {
                    rawText.append(openTime).append("-").append(closeTime);
                } else {
                    rawText.append("closed");
                }
            } else {
                rawText.append("closed");
            }
        }
        
        return rawText.toString();
    }
    
    /**
     * Utility method to capitalize first letter of a string
     */
    private String capitalizeFirst(String str) {
        if (str == null || str.isEmpty()) {
            return str;
        }
        return str.substring(0, 1).toUpperCase() + str.substring(1);
    }
    
    /**
     * Utility method to safely convert BigDecimal to double
     */
    private Double bigDecimalToDouble(BigDecimal value) {
        return value != null ? value.doubleValue() : null;
    }
}