package org.laioffer.planner.model.place;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonInclude;
import org.laioffer.planner.model.common.GeoPoint;

import java.time.LocalDateTime;
import java.util.UUID;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class PlaceDTO {
    private UUID id;
    private String name;
    private GeoPoint location;
    private String address;
    private ContactDTO contact;
    private String imageUrl;
    private String description;
    private OpeningHoursDTO openingHours;

    // Itinerary-specific fields
    private UUID itineraryPlaceRecordId;
    private Boolean pinned;
    private String note;

    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
    private LocalDateTime addedAt;

    public PlaceDTO() {}

    public PlaceDTO(UUID id, String name, GeoPoint location, String address) {
        this.id = id;
        this.name = name;
        this.location = location;
        this.address = address;
    }

    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public GeoPoint getLocation() {
        return location;
    }

    public void setLocation(GeoPoint location) {
        this.location = location;
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public ContactDTO getContact() {
        return contact;
    }

    public void setContact(ContactDTO contact) {
        this.contact = contact;
    }

    public String getImageUrl() {
        return imageUrl;
    }

    public void setImageUrl(String imageUrl) {
        this.imageUrl = imageUrl;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public OpeningHoursDTO getOpeningHours() {
        return openingHours;
    }

    public void setOpeningHours(OpeningHoursDTO openingHours) {
        this.openingHours = openingHours;
    }

    public UUID getItineraryPlaceRecordId() {
        return itineraryPlaceRecordId;
    }

    public void setItineraryPlaceRecordId(UUID itineraryPlaceRecordId) {
        this.itineraryPlaceRecordId = itineraryPlaceRecordId;
    }

    public Boolean getPinned() {
        return pinned;
    }

    public void setPinned(Boolean pinned) {
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

    public void setAddedAt(LocalDateTime addedAt) {
        this.addedAt = addedAt;
    }

    @Override
    public String toString() {
        return "PlaceDTO{" +
                "id=" + id +
                ", name='" + name + '\'' +
                ", location=" + location +
                ", address='" + address + '\'' +
                ", contact=" + contact +
                ", imageUrl='" + imageUrl + '\'' +
                ", description='" + description + '\'' +
                ", openingHours=" + openingHours +
                '}';
    }
}
