package org.laioffer.planner.model.common;

import com.fasterxml.jackson.annotation.JsonProperty;

public class PageMeta {
    private int page;
    private int size;

    @JsonProperty("totalElements")
    private long totalElements;

    @JsonProperty("totalPages")
    private int totalPages;

    public PageMeta() {}

    public PageMeta(int page, int size, long totalElements, int totalPages) {
        this.page = page;
        this.size = size;
        this.totalElements = totalElements;
        this.totalPages = totalPages;
    }

    public int getPage() {
        return page;
    }

    public void setPage(int page) {
        this.page = page;
    }

    public int getSize() {
        return size;
    }

    public void setSize(int size) {
        this.size = size;
    }

    public long getTotalElements() {
        return totalElements;
    }

    public void setTotalElements(long totalElements) {
        this.totalElements = totalElements;
    }

    public int getTotalPages() {
        return totalPages;
    }

    public void setTotalPages(int totalPages) {
        this.totalPages = totalPages;
    }

    @Override
    public String toString() {
        return "PageMeta{" +
                "page=" + page +
                ", size=" + size +
                ", totalElements=" + totalElements +
                ", totalPages=" + totalPages +
                '}';
    }
}
