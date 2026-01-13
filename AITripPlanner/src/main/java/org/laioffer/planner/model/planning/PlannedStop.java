package org.laioffer.planner.model.planning;

import com.fasterxml.jackson.annotation.JsonInclude;
import org.laioffer.planner.model.place.PlaceDTO;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class PlannedStop {
    private int order;
    private PlaceDTO place;
    private String arrivalLocal;
    private String departLocal;
    private int stayMinutes;
    private String note;
    
    public PlannedStop() {}
    
    public PlannedStop(int order, PlaceDTO place, String arrivalLocal, String departLocal, int stayMinutes) {
        this.order = order;
        this.place = place;
        this.arrivalLocal = arrivalLocal;
        this.departLocal = departLocal;
        this.stayMinutes = stayMinutes;
    }
    
    public int getOrder() {
        return order;
    }
    
    public void setOrder(int order) {
        this.order = order;
    }
    
    public PlaceDTO getPlace() {
        return place;
    }
    
    public void setPlace(PlaceDTO place) {
        this.place = place;
    }
    
    public String getArrivalLocal() {
        return arrivalLocal;
    }
    
    public void setArrivalLocal(String arrivalLocal) {
        this.arrivalLocal = arrivalLocal;
    }
    
    public String getDepartLocal() {
        return departLocal;
    }
    
    public void setDepartLocal(String departLocal) {
        this.departLocal = departLocal;
    }
    
    public int getStayMinutes() {
        return stayMinutes;
    }
    
    public void setStayMinutes(int stayMinutes) {
        this.stayMinutes = stayMinutes;
    }
    
    public String getNote() {
        return note;
    }
    
    public void setNote(String note) {
        this.note = note;
    }
    
    @Override
    public String toString() {
        return "PlannedStop{" +
                "order=" + order +
                ", place=" + place +
                ", arrivalLocal='" + arrivalLocal + '\'' +
                ", departLocal='" + departLocal + '\'' +
                ", stayMinutes=" + stayMinutes +
                ", note='" + note + '\'' +
                '}';
    }
}