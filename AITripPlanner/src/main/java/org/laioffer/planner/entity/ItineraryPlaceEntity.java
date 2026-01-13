package org.laioffer.planner.entity;

import jakarta.persistence.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "itinerary_places", uniqueConstraints = {
    @UniqueConstraint(columnNames = {"itinerary_id", "place_id"})
})
@EntityListeners(AuditingEntityListener.class)
public class ItineraryPlaceEntity {
    
    @Id
    @GeneratedValue
    private UUID id;
    
    @Column(name = "itinerary_id", nullable = false)
    private UUID itineraryId;
    
    @Column(name = "place_id", nullable = false)
    private UUID placeId;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "itinerary_id", insertable = false, updatable = false)
    private ItineraryEntity itinerary;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "place_id", insertable = false, updatable = false)
    private PlaceEntity place;
    
    @Column(name = "name", nullable = false)
    private String name;
    
    @Column(name = "description", columnDefinition = "TEXT")
    private String description;
    
    @Column(nullable = false)
    private boolean pinned = false;
    
    @Column(columnDefinition = "TEXT")
    private String note;
    
    @CreatedDate
    @Column(name = "added_at", nullable = false, updatable = false)
    private LocalDateTime addedAt;
    
    // Constructors
    public ItineraryPlaceEntity() {}
    
    public ItineraryPlaceEntity(ItineraryEntity itinerary, PlaceEntity place) {
        this.itinerary = itinerary;
        this.place = place;
        this.itineraryId = itinerary.getId();
        this.placeId = place.getId();
        // Copy name and description from place entity
        this.name = place.getName();
        this.description = place.getDescription();
    }
    
    public ItineraryPlaceEntity(ItineraryEntity itinerary, PlaceEntity place, boolean pinned) {
        this(itinerary, place);
        this.pinned = pinned;
    }
    
    public ItineraryPlaceEntity(ItineraryEntity itinerary, PlaceEntity place, boolean pinned, String note) {
        this(itinerary, place, pinned);
        this.note = note;
    }
    
    // Getters and Setters
    public UUID getId() {
        return id;
    }
    
    public void setId(UUID id) {
        this.id = id;
    }
    
    public UUID getItineraryId() {
        return itineraryId;
    }
    
    public void setItineraryId(UUID itineraryId) {
        this.itineraryId = itineraryId;
    }
    
    public UUID getPlaceId() {
        return placeId;
    }
    
    public void setPlaceId(UUID placeId) {
        this.placeId = placeId;
    }
    
    public ItineraryEntity getItinerary() {
        return itinerary;
    }
    
    public void setItinerary(ItineraryEntity itinerary) {
        this.itinerary = itinerary;
    }
    
    public PlaceEntity getPlace() {
        return place;
    }
    
    public void setPlace(PlaceEntity place) {
        this.place = place;
    }
    
    public String getName() {
        return name;
    }
    
    public void setName(String name) {
        this.name = name;
    }
    
    public String getDescription() {
        return description;
    }
    
    public void setDescription(String description) {
        this.description = description;
    }
    
    public boolean isPinned() {
        return pinned;
    }
    
    public void setPinned(boolean pinned) {
        this.pinned = pinned;
    }
    
    public String getNote() {
        return note;
    }
    
    public void setNote(String note) {
        this.note = note;
    }
    
    public LocalDateTime getAddedAt() {
        return addedAt;
    }
    
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof ItineraryPlaceEntity)) return false;
        ItineraryPlaceEntity that = (ItineraryPlaceEntity) o;
        return getId() != null && getId().equals(that.getId());
    }
    
    @Override
    public int hashCode() {
        return getId() != null ? getId().hashCode() : 0;
    }
    
    @Override
    public String toString() {
        return "ItineraryPlaceEntity{" +
                "id=" + id +
                ", pinned=" + pinned +
                ", note='" + note + '\'' +
                ", addedAt=" + addedAt +
                '}';
    }
}