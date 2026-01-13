package org.laioffer.planner.model.place;

import java.util.List;

public class OpeningHoursDTO {
    private String raw;
    private List<DailyHours> normalized;

    public OpeningHoursDTO() {}

    public OpeningHoursDTO(String raw) {
        this.raw = raw;
    }

    public OpeningHoursDTO(String raw, List<DailyHours> normalized) {
        this.raw = raw;
        this.normalized = normalized;
    }

    public String getRaw() {
        return raw;
    }

    public void setRaw(String raw) {
        this.raw = raw;
    }

    public List<DailyHours> getNormalized() {
        return normalized;
    }

    public void setNormalized(List<DailyHours> normalized) {
        this.normalized = normalized;
    }

    @Override
    public String toString() {
        return "OpeningHoursDTO{" +
                "raw='" + raw + '\'' +
                ", normalized=" + normalized +
                '}';
    }
}
