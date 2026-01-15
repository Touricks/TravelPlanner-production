package org.laioffer.planner.model.itinerary;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Collections;
import java.util.List;

/**
 * Response containing pinned POIs for CRAG integration.
 *
 * This DTO uses a flat structure compatible with CRAG's POI format,
 * avoiding nested objects like GeoPoint for easier consumption.
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class PinnedPOIResponse {

    @JsonProperty("pois")
    private List<PinnedPOIDTO> pois;

    public PinnedPOIResponse() {
        this.pois = Collections.emptyList();
    }

    public PinnedPOIResponse(List<PinnedPOIDTO> pois) {
        this.pois = pois != null ? pois : Collections.emptyList();
    }

    public List<PinnedPOIDTO> getPois() {
        return pois;
    }

    public void setPois(List<PinnedPOIDTO> pois) {
        this.pois = pois;
    }

    /**
     * Simplified POI DTO for CRAG consumption.
     * Uses flat structure with separate lat/lng fields.
     */
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class PinnedPOIDTO {
        private String id;
        private String name;
        private Double latitude;
        private Double longitude;
        private String address;
        private String city;
        private String description;
        private Double rating;
        private String primaryCategory;
        private String imageUrl;
        private String openingHours;

        public PinnedPOIDTO() {}

        // Getters and Setters
        public String getId() {
            return id;
        }

        public void setId(String id) {
            this.id = id;
        }

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public Double getLatitude() {
            return latitude;
        }

        public void setLatitude(Double latitude) {
            this.latitude = latitude;
        }

        public Double getLongitude() {
            return longitude;
        }

        public void setLongitude(Double longitude) {
            this.longitude = longitude;
        }

        public String getAddress() {
            return address;
        }

        public void setAddress(String address) {
            this.address = address;
        }

        public String getCity() {
            return city;
        }

        public void setCity(String city) {
            this.city = city;
        }

        public String getDescription() {
            return description;
        }

        public void setDescription(String description) {
            this.description = description;
        }

        public Double getRating() {
            return rating;
        }

        public void setRating(Double rating) {
            this.rating = rating;
        }

        public String getPrimaryCategory() {
            return primaryCategory;
        }

        public void setPrimaryCategory(String primaryCategory) {
            this.primaryCategory = primaryCategory;
        }

        public String getImageUrl() {
            return imageUrl;
        }

        public void setImageUrl(String imageUrl) {
            this.imageUrl = imageUrl;
        }

        public String getOpeningHours() {
            return openingHours;
        }

        public void setOpeningHours(String openingHours) {
            this.openingHours = openingHours;
        }

        @Override
        public String toString() {
            return "PinnedPOIDTO{" +
                    "id='" + id + '\'' +
                    ", name='" + name + '\'' +
                    ", latitude=" + latitude +
                    ", longitude=" + longitude +
                    ", city='" + city + '\'' +
                    '}';
        }
    }

    @Override
    public String toString() {
        return "PinnedPOIResponse{" +
                "pois=" + pois +
                '}';
    }
}
