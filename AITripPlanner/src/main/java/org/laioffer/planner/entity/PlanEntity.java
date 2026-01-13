package org.laioffer.planner.entity;

import io.hypersistence.utils.hibernate.type.json.JsonType;
import jakarta.persistence.*;
import org.hibernate.annotations.Type;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.Map;
import java.util.UUID;

@Entity
@Table(name = "plans")
@EntityListeners(AuditingEntityListener.class)
public class PlanEntity {

    @Id
    @GeneratedValue
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "itinerary_id", nullable = false)
    private ItineraryEntity itinerary;

    @Type(JsonType.class)
    @Column(name = "plan_data", columnDefinition = "jsonb", nullable = false)
    private Map<String, Object> planData;

    @Column(name = "version", nullable = false)
    private Integer version;

    @Column(name = "is_active", nullable = false)
    private Boolean isActive = true;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    // Constructors
    public PlanEntity() {}

    public PlanEntity(ItineraryEntity itinerary, Map<String, Object> planData, Integer version) {
        this.itinerary = itinerary;
        this.planData = planData;
        this.version = version;
        this.isActive = true;
    }

    // Getters and Setters
    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }

    public ItineraryEntity getItinerary() {
        return itinerary;
    }

    public void setItinerary(ItineraryEntity itinerary) {
        this.itinerary = itinerary;
    }

    public Map<String, Object> getPlanData() {
        return planData;
    }

    public void setPlanData(Map<String, Object> planData) {
        this.planData = planData;
    }

    public Integer getVersion() {
        return version;
    }

    public void setVersion(Integer version) {
        this.version = version;
    }

    public Boolean getIsActive() {
        return isActive;
    }

    public void setIsActive(Boolean isActive) {
        this.isActive = isActive;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }
}
