package org.laioffer.planner.model.place;

import java.util.List;

public class DailyHours {
    private String weekday;
    private List<TimeRange> times;

    public DailyHours() {}

    public DailyHours(String weekday, List<TimeRange> times) {
        this.weekday = weekday;
        this.times = times;
    }

    public String getWeekday() {
        return weekday;
    }

    public void setWeekday(String weekday) {
        this.weekday = weekday;
    }

    public List<TimeRange> getTimes() {
        return times;
    }

    public void setTimes(List<TimeRange> times) {
        this.times = times;
    }

    @Override
    public String toString() {
        return "DailyHours{" +
                "weekday='" + weekday + '\'' +
                ", times=" + times +
                '}';
    }
}
