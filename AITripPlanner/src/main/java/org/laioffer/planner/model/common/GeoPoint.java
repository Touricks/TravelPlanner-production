package org.laioffer.planner.model.common;

import com.fasterxml.jackson.annotation.JsonProperty;

public class GeoPoint {
    @JsonProperty("lat")
    private double latitude;

    @JsonProperty("lng")
    private double longitude;

    public GeoPoint() {}

    public GeoPoint(double latitude, double longitude) {
        this.latitude = latitude;
        this.longitude = longitude;
    }

    public double getLatitude() {
        return latitude;
    }

    public void setLatitude(double latitude) {
        this.latitude = latitude;
    }

    public double getLongitude() {
        return longitude;
    }

    public void setLongitude(double longitude) {
        this.longitude = longitude;
    }

    @Override
    public String toString() {
        return "GeoPoint{" +
                "lat=" + latitude +
                ", lng=" + longitude +
                '}';
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        GeoPoint geoPoint = (GeoPoint) o;
        return Double.compare(geoPoint.latitude, latitude) == 0 &&
               Double.compare(geoPoint.longitude, longitude) == 0;
    }

    @Override
    public int hashCode() {
        return java.util.Objects.hash(latitude, longitude);
    }
}
