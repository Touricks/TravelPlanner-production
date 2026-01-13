package org.laioffer.planner.model.itinerary;

import org.laioffer.planner.model.common.PageMeta;

import java.util.List;

public class GetItinerariesResponse {
    private List<ItinerarySummaryDTO> items;
    private PageMeta page;

    public GetItinerariesResponse() {}

    public GetItinerariesResponse(List<ItinerarySummaryDTO> items, PageMeta page) {
        this.items = items;
        this.page = page;
    }

    public List<ItinerarySummaryDTO> getItems() {
        return items;
    }

    public void setItems(List<ItinerarySummaryDTO> items) {
        this.items = items;
    }

    public PageMeta getPage() {
        return page;
    }

    public void setPage(PageMeta page) {
        this.page = page;
    }

    @Override
    public String toString() {
        return "GetItinerariesResponse{" +
                "items=" + items +
                ", page=" + page +
                '}';
    }
}
