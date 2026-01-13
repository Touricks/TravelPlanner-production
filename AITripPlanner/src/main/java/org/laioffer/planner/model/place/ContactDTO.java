package org.laioffer.planner.model.place;

import com.fasterxml.jackson.annotation.JsonInclude;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class ContactDTO {
    private String website;
    private String phone;

    public ContactDTO() {}

    public ContactDTO(String website, String phone) {
        this.website = website;
        this.phone = phone;
    }

    public String getWebsite() {
        return website;
    }

    public void setWebsite(String website) {
        this.website = website;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }

    @Override
    public String toString() {
        return "ContactDTO{" +
                "website='" + website + '\'' +
                ", phone='" + phone + '\'' +
                '}';
    }
}
