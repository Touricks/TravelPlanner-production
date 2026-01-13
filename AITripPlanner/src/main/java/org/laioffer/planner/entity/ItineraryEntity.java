package org.laioffer.planner.entity;

import io.hypersistence.utils.hibernate.type.json.JsonType;
import jakarta.persistence.*;
import org.hibernate.annotations.Type;
import org.laioffer.planner.model.common.ActivityIntensity;
import org.laioffer.planner.model.common.TravelPace;
import org.laioffer.planner.model.itinerary.TravelMode;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

@Entity
@Table(name = "itineraries")
@EntityListeners(AuditingEntityListener.class)
public class ItineraryEntity {

    @Id
    @GeneratedValue
    private UUID id;
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private UserEntity user;

    @Column(name = "destination_city", nullable = false)
    private String destinationCity;

    @Column(name = "start_date", nullable = false)
    private java.time.OffsetDateTime startDate;

    @Column(name = "end_date", nullable = false)
    private java.time.OffsetDateTime endDate;

    @Enumerated(EnumType.STRING)
    @Column(name = "travel_mode")
    private TravelMode travelMode;

    @Column(name = "budget_in_cents", nullable = false)
    private Integer budgetInCents;

    @Column(name = "budget_per_meal_cents")
    private Integer budgetPerMealCents;

    // User preference fields
    @Enumerated(EnumType.STRING)
    @Column(name = "travel_pace", nullable = false)
    private TravelPace travelPace;

    @Enumerated(EnumType.STRING)
    @Column(name = "activity_intensity")
    private ActivityIntensity activityIntensity;

    @Column(name = "number_of_travelers")
    private Integer numberOfTravelers;

    @Column(name = "has_children")
    private Boolean hasChildren;

    @Column(name = "has_elderly")
    private Boolean hasElderly;

    @Column(name = "prefer_popular_attractions")
    private Boolean preferPopularAttractions;

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "itinerary_preferred_categories",
                     joinColumns = @JoinColumn(name = "itinerary_id"))
    @Column(name = "category")
    private List<String> preferredCategories;

    @Column(name = "additional_preferences", columnDefinition = "text")
    private String additionalPreferences;

    // JSONB fields for AI recommendations
    @Type(JsonType.class)
    @Column(name = "seeded_recommendations", columnDefinition = "jsonb")
    private Map<String, Object> seededRecommendations;

    @Type(JsonType.class)
    @Column(name = "ai_metadata", columnDefinition = "jsonb")
    private Map<String, Object> aiMetadata;

    @Column(name = "crag_session_id", length = 64, unique = true)
    private String cragSessionId;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    // Relationships
    @OneToMany(mappedBy = "itinerary", cascade = CascadeType.ALL, orphanRemoval = true)
    private Set<ItineraryPlaceEntity> itineraryPlaces = new HashSet<>();

    // Constructors
    public ItineraryEntity() {}

    // Getters and Setters
    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public UserEntity getUser() { return user; }
    public void setUser(UserEntity user) { this.user = user; }

    public String getDestinationCity() { return destinationCity; }
    public void setDestinationCity(String destinationCity) { this.destinationCity = destinationCity; }

    public java.time.OffsetDateTime getStartDate() { return startDate; }
    public void setStartDate(java.time.OffsetDateTime startDate) { this.startDate = startDate; }

    public java.time.OffsetDateTime getEndDate() { return endDate; }
    public void setEndDate(java.time.OffsetDateTime endDate) { this.endDate = endDate; }

    public TravelMode getTravelMode() { return travelMode; }
    public void setTravelMode(TravelMode travelMode) { this.travelMode = travelMode; }

    public Integer getBudgetInCents() { return budgetInCents; }
    public void setBudgetInCents(Integer budgetInCents) { this.budgetInCents = budgetInCents; }

    public Integer getBudgetPerMealCents() { return budgetPerMealCents; }
    public void setBudgetPerMealCents(Integer budgetPerMealCents) { this.budgetPerMealCents = budgetPerMealCents; }

    public TravelPace getTravelPace() { return travelPace; }
    public void setTravelPace(TravelPace travelPace) { this.travelPace = travelPace; }

    public ActivityIntensity getActivityIntensity() { return activityIntensity; }
    public void setActivityIntensity(ActivityIntensity activityIntensity) { this.activityIntensity = activityIntensity; }

    public Integer getNumberOfTravelers() { return numberOfTravelers; }
    public void setNumberOfTravelers(Integer numberOfTravelers) { this.numberOfTravelers = numberOfTravelers; }

    public Boolean getHasChildren() { return hasChildren; }
    public void setHasChildren(Boolean hasChildren) { this.hasChildren = hasChildren; }

    public Boolean getHasElderly() { return hasElderly; }
    public void setHasElderly(Boolean hasElderly) { this.hasElderly = hasElderly; }

    public Boolean getPreferPopularAttractions() { return preferPopularAttractions; }
    public void setPreferPopularAttractions(Boolean preferPopularAttractions) { this.preferPopularAttractions = preferPopularAttractions; }

    public List<String> getPreferredCategories() { return preferredCategories; }
    public void setPreferredCategories(List<String> preferredCategories) { this.preferredCategories = preferredCategories; }

    public String getAdditionalPreferences() { return additionalPreferences; }
    public void setAdditionalPreferences(String additionalPreferences) { this.additionalPreferences = additionalPreferences; }

    public Map<String, Object> getSeededRecommendations() { return seededRecommendations; }
    public void setSeededRecommendations(Map<String, Object> seededRecommendations) { this.seededRecommendations = seededRecommendations; }

    public Map<String, Object> getAiMetadata() { return aiMetadata; }
    public void setAiMetadata(Map<String, Object> aiMetadata) { this.aiMetadata = aiMetadata; }

    public String getCragSessionId() { return cragSessionId; }
    public void setCragSessionId(String cragSessionId) { this.cragSessionId = cragSessionId; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }

    public Set<ItineraryPlaceEntity> getItineraryPlaces() { return itineraryPlaces; }
    public void setItineraryPlaces(Set<ItineraryPlaceEntity> itineraryPlaces) { this.itineraryPlaces = itineraryPlaces; }

    // Helper methods for managing the relationship
    public void addPlace(PlaceEntity place) {
        addPlace(place, false, null);
    }

    public void addPlace(PlaceEntity place, boolean pinned) {
        addPlace(place, pinned, null);
    }

    public void addPlace(PlaceEntity place, boolean pinned, String note) {
        ItineraryPlaceEntity itineraryPlace = new ItineraryPlaceEntity(this, place, pinned, note);
        itineraryPlaces.add(itineraryPlace);
        place.getItineraryPlaces().add(itineraryPlace);
    }

    public void removePlace(PlaceEntity place) {
        ItineraryPlaceEntity itineraryPlace = itineraryPlaces.stream()
            .filter(ip -> ip.getPlace().equals(place))
            .findFirst()
            .orElse(null);
        if (itineraryPlace != null) {
            itineraryPlaces.remove(itineraryPlace);
            place.getItineraryPlaces().remove(itineraryPlace);
            itineraryPlace.setItinerary(null);
            itineraryPlace.setPlace(null);
        }
    }
}
