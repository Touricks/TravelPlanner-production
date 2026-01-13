package org.laioffer.planner.model.planning;

import java.util.List;

public class PlannedDay {
    private String date;
    private List<PlannedStop> stops;
    
    public PlannedDay() {}
    
    public PlannedDay(String date, List<PlannedStop> stops) {
        this.date = date;
        this.stops = stops;
    }
    
    public String getDate() {
        return date;
    }
    
    public void setDate(String date) {
        this.date = date;
    }
    
    public List<PlannedStop> getStops() {
        return stops;
    }
    
    public void setStops(List<PlannedStop> stops) {
        this.stops = stops;
    }
    
    @Override
    public String toString() {
        return "PlannedDay{" +
                "date='" + date + '\'' +
                ", stops=" + stops +
                '}';
    }
}