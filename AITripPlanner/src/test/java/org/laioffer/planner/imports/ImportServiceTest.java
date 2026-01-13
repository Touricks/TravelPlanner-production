package org.laioffer.planner.imports;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.laioffer.planner.entity.ItineraryEntity;
import org.laioffer.planner.entity.PlaceEntity;
import org.laioffer.planner.entity.PlanEntity;
import org.laioffer.planner.entity.UserEntity;
import org.laioffer.planner.model.imports.*;
import org.laioffer.planner.repository.*;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ImportServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private ItineraryRepository itineraryRepository;

    @Mock
    private PlaceRepository placeRepository;

    @Mock
    private ItineraryPlaceRepository itineraryPlaceRepository;

    @Mock
    private PlanRepository planRepository;

    private ImportServiceImpl importService;

    @BeforeEach
    void setUp() {
        importService = new ImportServiceImpl(
                userRepository,
                itineraryRepository,
                placeRepository,
                itineraryPlaceRepository,
                planRepository
        );
    }

    @Test
    void shouldImportPlanWithNewPOIs() {
        // Given
        Long userId = 1L;
        UserEntity user = new UserEntity();
        user.setId(userId);
        user.setEmail("test@example.com");

        when(userRepository.findById(userId)).thenReturn(Optional.of(user));

        // Mock itinerary save to return entity with ID
        when(itineraryRepository.save(any(ItineraryEntity.class))).thenAnswer(invocation -> {
            ItineraryEntity saved = invocation.getArgument(0);
            saved.setId(UUID.randomUUID());
            return saved;
        });

        // Mock place save to return entity with ID
        when(placeRepository.save(any(PlaceEntity.class))).thenAnswer(invocation -> {
            PlaceEntity saved = invocation.getArgument(0);
            saved.setId(UUID.randomUUID());
            return saved;
        });

        // Mock plan repository
        when(planRepository.findMaxVersionByItineraryId(any())).thenReturn(0);

        // Create request
        ImportPlanRequest request = buildTestRequest();

        // When
        ImportPlanResponse response = importService.importPlan(userId, request);

        // Then
        assertThat(response.getItineraryId()).isNotNull();
        assertThat(response.getStatus()).isEqualTo("success");
        assertThat(response.getImportedPoisCount()).isEqualTo(2);
        assertThat(response.getPlanVersion()).isEqualTo(1);

        // Verify interactions
        verify(itineraryRepository, times(1)).save(any(ItineraryEntity.class));
        verify(placeRepository, times(2)).save(any(PlaceEntity.class));
        verify(itineraryPlaceRepository, times(2)).save(any());
        verify(planRepository, times(1)).save(any(PlanEntity.class));
    }

    @Test
    void shouldSetCorrectItineraryFields() {
        // Given
        Long userId = 1L;
        UserEntity user = new UserEntity();
        user.setId(userId);

        when(userRepository.findById(userId)).thenReturn(Optional.of(user));

        ArgumentCaptor<ItineraryEntity> itineraryCaptor = ArgumentCaptor.forClass(ItineraryEntity.class);
        when(itineraryRepository.save(itineraryCaptor.capture())).thenAnswer(invocation -> {
            ItineraryEntity saved = invocation.getArgument(0);
            saved.setId(UUID.randomUUID());
            return saved;
        });
        when(placeRepository.save(any())).thenAnswer(invocation -> {
            PlaceEntity saved = invocation.getArgument(0);
            saved.setId(UUID.randomUUID());
            return saved;
        });
        when(planRepository.findMaxVersionByItineraryId(any())).thenReturn(0);

        ImportPlanRequest request = buildTestRequest();

        // When
        importService.importPlan(userId, request);

        // Then
        ItineraryEntity captured = itineraryCaptor.getValue();
        assertThat(captured.getDestinationCity()).isEqualTo("Tokyo");
        assertThat(captured.getUser()).isEqualTo(user);
        assertThat(captured.getAiMetadata()).containsEntry("source", "crag");
    }

    @Test
    void shouldSetCorrectPlaceFields() {
        // Given
        Long userId = 1L;
        UserEntity user = new UserEntity();
        user.setId(userId);

        when(userRepository.findById(userId)).thenReturn(Optional.of(user));
        when(itineraryRepository.save(any())).thenAnswer(invocation -> {
            ItineraryEntity saved = invocation.getArgument(0);
            saved.setId(UUID.randomUUID());
            return saved;
        });

        ArgumentCaptor<PlaceEntity> placeCaptor = ArgumentCaptor.forClass(PlaceEntity.class);
        when(placeRepository.save(placeCaptor.capture())).thenAnswer(invocation -> {
            PlaceEntity saved = invocation.getArgument(0);
            saved.setId(UUID.randomUUID());
            return saved;
        });
        when(planRepository.findMaxVersionByItineraryId(any())).thenReturn(0);

        ImportPlanRequest request = buildTestRequest();

        // When
        importService.importPlan(userId, request);

        // Then
        List<PlaceEntity> capturedPlaces = placeCaptor.getAllValues();
        assertThat(capturedPlaces).hasSize(2);

        PlaceEntity firstPlace = capturedPlaces.get(0);
        assertThat(firstPlace.getName()).isEqualTo("Senso-ji Temple");
        assertThat(firstPlace.getLatitude().doubleValue()).isEqualTo(35.7148);
        assertThat(firstPlace.getLongitude().doubleValue()).isEqualTo(139.7967);
        assertThat(firstPlace.getSource()).isEqualTo("crag");
    }

    @Test
    void shouldThrowExceptionForUnknownUser() {
        // Given
        Long userId = 999L;
        when(userRepository.findById(userId)).thenReturn(Optional.empty());

        ImportPlanRequest request = buildTestRequest();

        // When/Then
        org.junit.jupiter.api.Assertions.assertThrows(
                IllegalArgumentException.class,
                () -> importService.importPlan(userId, request)
        );
    }

    /**
     * Build a test ImportPlanRequest with sample data.
     */
    private ImportPlanRequest buildTestRequest() {
        ImportPlanRequest request = new ImportPlanRequest();
        request.setCragSessionId("test-session-123");

        // User features
        ImportedUserFeatures features = new ImportedUserFeatures();
        features.setDestination("Tokyo");
        features.setTravelDays(3);
        features.setBudgetCents(150000);
        features.setInterests(Arrays.asList("culture", "food"));
        features.setTravelPace("MODERATE");
        request.setUserFeatures(features);

        // POIs
        ImportedPOI poi1 = new ImportedPOI();
        poi1.setExternalId("poi-001");
        poi1.setName("Senso-ji Temple");
        poi1.setLatitude(35.7148);
        poi1.setLongitude(139.7967);
        poi1.setAddress("2-3-1 Asakusa, Taito City");
        poi1.setCity("Tokyo");
        poi1.setDescription("Tokyo's oldest temple");
        poi1.setPrimaryCategory("HISTORICAL");

        ImportedPOI poi2 = new ImportedPOI();
        poi2.setExternalId("poi-002");
        poi2.setName("Shibuya Crossing");
        poi2.setLatitude(35.6595);
        poi2.setLongitude(139.7004);
        poi2.setAddress("Shibuya, Tokyo");
        poi2.setCity("Tokyo");
        poi2.setDescription("Famous pedestrian crossing");
        poi2.setPrimaryCategory("LANDMARK");

        request.setPois(Arrays.asList(poi1, poi2));

        // Plan
        ImportedPlan plan = new ImportedPlan();
        plan.setDestination("Tokyo");
        plan.setStartDate("2025-03-01T10:00:00+09:00");
        plan.setEndDate("2025-03-03T18:00:00+09:00");

        ImportedStop stop1 = new ImportedStop();
        stop1.setPoiExternalId("poi-001");
        stop1.setPoiName("Senso-ji Temple");
        stop1.setArrivalTime("10:00");
        stop1.setDepartureTime("12:00");
        stop1.setDurationMinutes(120);
        stop1.setActivity("Morning temple visit");

        ImportedStop stop2 = new ImportedStop();
        stop2.setPoiExternalId("poi-002");
        stop2.setPoiName("Shibuya Crossing");
        stop2.setArrivalTime("14:00");
        stop2.setDepartureTime("15:30");
        stop2.setDurationMinutes(90);
        stop2.setActivity("Explore Shibuya area");

        ImportedDay day1 = new ImportedDay();
        day1.setDate("2025-03-01");
        day1.setStops(Arrays.asList(stop1, stop2));

        plan.setDays(Arrays.asList(day1));
        request.setPlan(plan);

        return request;
    }
}
