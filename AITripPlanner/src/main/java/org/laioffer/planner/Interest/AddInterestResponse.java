package org.laioffer.planner.Interest;

import org.laioffer.planner.model.place.PlaceDTO;

public class AddInterestResponse {
    private PlaceDTO place;
    private boolean pinned;
    
    public AddInterestResponse() {}
    
    public AddInterestResponse(PlaceDTO place, boolean pinned) {
        this.place = place;
        this.pinned = pinned;
    }
    
    public PlaceDTO getPlace() {
        return place;
    }
    
    public void setPlace(PlaceDTO place) {
        this.place = place;
    }
    
    public boolean isPinned() {
        return pinned;
    }
    
    public void setPinned(boolean pinned) {
        this.pinned = pinned;
    }
    
    @Override
    public String toString() {
        return "AddInterestResponse{" +
                "place=" + place +
                ", pinned=" + pinned +
                '}';
    }
}