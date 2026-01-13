package org.laioffer.planner.model.place;

import com.fasterxml.jackson.annotation.JsonProperty;

public class TimeRange {
    @JsonProperty("startLocal")
    private String startLocal;

    @JsonProperty("endLocal")
    private String endLocal;

    public TimeRange() {}

    public TimeRange(String startLocal, String endLocal) {
        this.startLocal = startLocal;
        this.endLocal = endLocal;
    }

    public String getStartLocal() {
        return startLocal;
    }

    public void setStartLocal(String startLocal) {
        this.startLocal = startLocal;
    }

    public String getEndLocal() {
        return endLocal;
    }

    public void setEndLocal(String endLocal) {
        this.endLocal = endLocal;
    }

    @Override
    public String toString() {
        return "TimeRange{" +
                "startLocal='" + startLocal + '\'' +
                ", endLocal='" + endLocal + '\'' +
                '}';
    }
}
