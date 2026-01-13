package org.laioffer.planner.itinerary.model.llm;

import dev.langchain4j.model.output.structured.Description;
import org.laioffer.planner.model.common.GeoPoint;
import org.laioffer.planner.model.place.ContactDTO;
import org.laioffer.planner.model.place.OpeningHoursDTO;

public class LLMRecommendedPOI {

    @Description("Name of the tourist attraction or point of interest")
    private String name;

    @Description("Full street address of the location")
    private String address;

    @Description("Brief description of the attraction (required)")
    private String description;

    @Description("Geographic location with latitude and longitude coordinates (lat: -90 to 90, lng: -180 to 180)")
    private GeoPoint location;

    @Description("Contact information including website and phone (optional)")
    private ContactDTO contact;

    @Description("URL to an image of the attraction (optional)")
    private String imageUrl;

    @Description("Opening hours information as raw text (optional, e.g., 'Mon-Fri 9:00-17:00')")
    private OpeningHoursDTO openingHours;

    public LLMRecommendedPOI() {}

    // Getters and Setters
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getAddress() { return address; }
    public void setAddress(String address) { this.address = address; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public GeoPoint getLocation() { return location; }
    public void setLocation(GeoPoint location) { this.location = location; }

    public ContactDTO getContact() { return contact; }
    public void setContact(ContactDTO contact) { this.contact = contact; }

    public String getImageUrl() { return imageUrl; }
    public void setImageUrl(String imageUrl) { this.imageUrl = imageUrl; }

    public OpeningHoursDTO getOpeningHours() { return openingHours; }
    public void setOpeningHours(OpeningHoursDTO openingHours) { this.openingHours = openingHours; }
}
