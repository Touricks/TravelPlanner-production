package org.laioffer.planner.planning;

import org.laioffer.planner.planning.ai.model.AiPlaceInfo;
import org.laioffer.planner.planning.ai.model.AiPlanResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Service
public class PlanningLLMService {

    private static final Logger logger = LoggerFactory.getLogger(PlanningLLMService.class);
    private static final int MAX_RETRIES = 3;

    private final PlanningAiService planningAiService;

    public PlanningLLMService(PlanningAiService planningAiService) {
        this.planningAiService = planningAiService;
    }

    public AiPlanResponse generatePlan(
            UUID itineraryId,
            String destinationCity,
            LocalDate startDate,
            LocalDate endDate,
            String travelMode,
            Integer budgetInCents,
            Double budgetInDollars,
            LocalTime dailyStart,
            LocalTime dailyEnd,
            List<AiPlaceInfo> interestedPlaces) throws Exception {

        // Build prompt programmatically to avoid Mustache template issues
        String prompt = buildPrompt(destinationCity, startDate, endDate, travelMode,
                budgetInCents, budgetInDollars, dailyStart, dailyEnd, interestedPlaces);

        List<String> errorLog = new ArrayList<>();

        for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
            try {
                logger.debug("LangChain4j planning attempt {} for itinerary {}", attempt, itineraryId);

                AiPlanResponse response = planningAiService.generatePlan(prompt);

                if (response != null && response.getDays() != null && !response.getDays().isEmpty()) {
                    logger.info("Successfully generated plan with {} days for itinerary {} using LangChain4j",
                            response.getDays().size(), itineraryId);
                    return response;
                }

                errorLog.add("No valid days were returned from the AI service");

            } catch (Exception e) {
                String errorMessage = "Attempt " + attempt + " failed: " + e.getMessage();
                errorLog.add(errorMessage);

                logger.warn("LangChain4j planning attempt {} failed for itinerary {}: {}",
                        attempt, itineraryId, e.getMessage());

                if (attempt == MAX_RETRIES) {
                    logger.error("All {} attempts failed for itinerary {}. Error log: {}",
                            MAX_RETRIES, itineraryId, errorLog);
                    throw new Exception("Failed to generate plan after " + MAX_RETRIES + " attempts. Last error: " + e.getMessage(), e);
                }

                // Exponential backoff: wait 1s, 2s, 4s between attempts
                long waitTime = (long) Math.pow(2, attempt - 1) * 1000;
                Thread.sleep(waitTime);
            }
        }

        throw new Exception("Failed to generate valid plan after " + MAX_RETRIES + " attempts");
    }

    private String buildPrompt(String destinationCity, LocalDate startDate, LocalDate endDate,
                                String travelMode, Integer budgetInCents, Double budgetInDollars,
                                LocalTime dailyStart, LocalTime dailyEnd, List<AiPlaceInfo> interestedPlaces) {
        StringBuilder prompt = new StringBuilder();

        prompt.append("Create an optimized travel itinerary for ").append(destinationCity).append(".\n\n");

        prompt.append("CRITICAL CONSTRAINT:\n");
        prompt.append("- You MUST ONLY schedule the ").append(interestedPlaces.size()).append(" places listed below\n");
        prompt.append("- DO NOT add, suggest, or create any places not in this list\n");
        prompt.append("- Every placeId in your response MUST exactly match a placeId from the list\n");
        prompt.append("- IMPORTANT: Each place can ONLY be scheduled ONCE in the entire itinerary - NO DUPLICATES\n");
        prompt.append("- DO NOT schedule the same placeId multiple times across different days\n");
        prompt.append("- If there's extra time, suggest \"free time\", \"lunch break\", or \"rest\" instead of new places\n\n");

        prompt.append("Trip Details:\n");
        prompt.append("- Destination: ").append(destinationCity).append("\n");
        prompt.append("- Start Date: ").append(startDate).append("\n");
        prompt.append("- End Date: ").append(endDate).append("\n");
        prompt.append("- Travel Mode: ").append(travelMode).append("\n");
        prompt.append("- Budget: $").append(budgetInDollars).append(" (").append(budgetInCents).append(" cents)\n");
        prompt.append("- Daily Schedule: ").append(dailyStart).append(" to ").append(dailyEnd).append("\n\n");

        prompt.append("Places to Schedule (").append(interestedPlaces.size()).append(" locations):\n");
        for (AiPlaceInfo place : interestedPlaces) {
            prompt.append("- Place ID: ").append(place.getPlaceId()).append("\n");
            prompt.append("  Name: ").append(place.getName() != null ? place.getName() : "Unknown").append("\n");

            if (place.getAddress() != null && !place.getAddress().isEmpty()) {
                prompt.append("  Address: ").append(place.getAddress()).append("\n");
            }

            if (place.getLatitude() != null && place.getLongitude() != null) {
                prompt.append("  Location: ").append(place.getLatitude()).append(", ").append(place.getLongitude()).append("\n");
            }

            if (place.getDescription() != null && !place.getDescription().isEmpty()) {
                prompt.append("  Description: ").append(place.getDescription()).append("\n");
            }

            if (place.isPinned()) {
                prompt.append("  ⭐ PRIORITY: This is a must-visit place\n");
            }

            if (place.getNote() != null && !place.getNote().isEmpty()) {
                prompt.append("  User Note: ").append(place.getNote()).append("\n");
            }

            prompt.append("\n");
        }

        prompt.append("Requirements:\n");
        prompt.append("1. ONLY use the ").append(interestedPlaces.size()).append(" places listed above - NO additional places allowed\n");
        prompt.append("2. Each place can ONLY appear ONCE in the entire itinerary - do NOT schedule duplicates\n");
        prompt.append("3. Create a day-by-day schedule from ").append(startDate).append(" to ").append(endDate).append("\n");
        prompt.append("4. Prioritize all pinned places - they MUST be included\n");
        prompt.append("5. Optimize the route to minimize backtracking\n");
        prompt.append("6. Respect the daily time window (").append(dailyStart).append(" - ").append(dailyEnd).append(")\n");
        prompt.append("7. Allocate realistic visit durations for each place\n");
        prompt.append("8. Include transportation time and mode between stops\n");
        prompt.append("9. Ensure the schedule is achievable and not overly packed\n");
        prompt.append("10. If you cannot fit all places, that's OK - do not add unlisted places to fill time\n\n");

        prompt.append("For each stop, provide:\n");
        prompt.append("- Exact place ID (UUID) from the list above\n");
        prompt.append("- Arrival and departure times\n");
        prompt.append("- Duration of visit in minutes\n");
        prompt.append("- Activity description (what to do there)\n");
        prompt.append("- Transportation mode to next location\n");
        prompt.append("- Transportation duration in minutes\n");

        return prompt.toString();
    }
}
