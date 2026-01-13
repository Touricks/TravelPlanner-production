package org.laioffer.planner.itinerary;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.laioffer.planner.model.itinerary.CreateItineraryRequest;
import org.laioffer.planner.model.itinerary.TravelMode;
import org.laioffer.planner.model.common.TravelPace;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.time.OffsetDateTime;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.mock;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ItineraryController.class)
class ItineraryControllerTest {

    @TestConfiguration
    static class TestConfig {
        @Bean
        @Primary
        public ItineraryService mockItineraryService() {
            return mock(ItineraryService.class);
        }
    }

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private ItineraryService itineraryService;

    @Test
    @WithMockUser(username = "test@example.com")
    void testCreateItinerary_Success() throws Exception {
        // Given
        CreateItineraryRequest request = new CreateItineraryRequest();
        request.setDestinationCity("San Francisco");
        request.setStartDate(OffsetDateTime.parse("2024-03-01T10:00:00-08:00"));
        request.setEndDate(OffsetDateTime.parse("2024-03-05T18:00:00-08:00"));
        request.setTravelMode(TravelMode.DRIVING);
        request.setBudgetLimitCents(500000);
        request.setTravelPace(TravelPace.MODERATE);

        String requestJson = objectMapper.writeValueAsString(request);

        // Mock the service call
        doNothing().when(itineraryService).createItinerary(any(), any());

        // When & Then
        mockMvc.perform(post("/api/itineraries")
                .contentType(MediaType.APPLICATION_JSON)
                .content(requestJson))
                .andExpect(status().isCreated());
    }
}