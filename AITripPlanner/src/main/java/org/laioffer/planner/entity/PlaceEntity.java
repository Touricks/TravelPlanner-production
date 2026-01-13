package org.laioffer.planner.entity;

import io.hypersistence.utils.hibernate.type.json.JsonType;
import jakarta.persistence.*;
import org.hibernate.annotations.Type;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

@Entity
@Table(name = "places")
@EntityListeners(AuditingEntityListener.class)
public class PlaceEntity {
    
    @Id
    @GeneratedValue
    private UUID id;
    
    @Column(nullable = false)
    private String name;
    
    @Column(nullable = false, columnDefinition = "TEXT")
    private String address;
    
    @Column(precision = 10, scale = 8)
    private BigDecimal latitude;
    
    @Column(precision = 11, scale = 8)
    private BigDecimal longitude;
    
    @Column(length = 500)
    private String website;
    
    @Column(length = 50)
    private String phone;
    
    @Column(name = "image_url", columnDefinition = "TEXT")
    private String imageUrl;
    
    @Column(columnDefinition = "TEXT")
    private String description;
    
    // JSONB fields
    @Type(JsonType.class)
    @Column(name = "opening_hours", columnDefinition = "jsonb")
    private Map<String, Object> openingHours;
    
    @Type(JsonType.class)
    @Column(name = "contact_info", columnDefinition = "jsonb")
    private Map<String, Object> contactInfo;
    
    @Type(JsonType.class)
    @Column(columnDefinition = "jsonb")
    private Map<String, Object> metadata;
    
    @Type(JsonType.class)
    @Column(name = "raw_data", columnDefinition = "jsonb")
    private Map<String, Object> rawData;
    
    @Column(length = 50)
    private String source;
    
    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
    
    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    // Relationships
    @OneToMany(mappedBy = "place")
    private Set<ItineraryPlaceEntity> itineraryPlaces = new HashSet<>();
    
    // Constructors
    public PlaceEntity() {}
    
    // Getters and Setters
    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public String getAddress() { return address; }
    public void setAddress(String address) { this.address = address; }
    
    public BigDecimal getLatitude() { return latitude; }
    public void setLatitude(BigDecimal latitude) { this.latitude = latitude; }
    
    public BigDecimal getLongitude() { return longitude; }
    public void setLongitude(BigDecimal longitude) { this.longitude = longitude; }
    
    public String getWebsite() { return website; }
    public void setWebsite(String website) { this.website = website; }
    
    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }
    
    public String getImageUrl() { return imageUrl; }
    public void setImageUrl(String imageUrl) { this.imageUrl = imageUrl; }
    
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    
    public Map<String, Object> getOpeningHours() { return openingHours; }
    public void setOpeningHours(Map<String, Object> openingHours) { this.openingHours = openingHours; }
    
    public Map<String, Object> getContactInfo() { return contactInfo; }
    public void setContactInfo(Map<String, Object> contactInfo) { this.contactInfo = contactInfo; }
    
    public Map<String, Object> getMetadata() { return metadata; }
    public void setMetadata(Map<String, Object> metadata) { this.metadata = metadata; }
    
    public Map<String, Object> getRawData() { return rawData; }
    public void setRawData(Map<String, Object> rawData) { this.rawData = rawData; }
    
    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }
    
    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    
    public Set<ItineraryPlaceEntity> getItineraryPlaces() { return itineraryPlaces; }
    public void setItineraryPlaces(Set<ItineraryPlaceEntity> itineraryPlaces) { this.itineraryPlaces = itineraryPlaces; }
}