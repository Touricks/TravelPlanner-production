package org.laioffer.planner.model.common;

import com.fasterxml.jackson.annotation.JsonProperty;

public class ErrorResponse {
    @JsonProperty("traceId")
    private String traceId;

    private ApiError error;

    public ErrorResponse() {}

    public ErrorResponse(String traceId, ApiError error) {
        this.traceId = traceId;
        this.error = error;
    }

    public String getTraceId() {
        return traceId;
    }

    public void setTraceId(String traceId) {
        this.traceId = traceId;
    }

    public ApiError getError() {
        return error;
    }

    public void setError(ApiError error) {
        this.error = error;
    }

    @Override
    public String toString() {
        return "ErrorResponse{" +
                "traceId='" + traceId + '\'' +
                ", error=" + error +
                '}';
    }
}
