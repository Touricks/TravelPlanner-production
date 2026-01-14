package org.laioffer.planner.Interest;

import org.laioffer.planner.model.common.ApiError;
import org.laioffer.planner.model.common.ErrorResponse;
import org.laioffer.planner.entity.UserEntity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/itineraries")
public class InterestController {

    private static final Logger logger = LoggerFactory.getLogger(InterestController.class);
    private final InterestService interestService;

    public InterestController(InterestService interestService) {
        this.interestService = interestService;
    }

    /**
     * Add or update interest (pin/unpin) for a place in an itinerary
     *
     * @param itineraryId UUID of the itinerary
     * @param request AddInterestRequest containing placeId and pinned status
     * @param user Authenticated user from JWT token
     * @return AddInterestResponse with place details and pinned status
     */
    @PostMapping("/{itineraryId}/interests")
    public ResponseEntity<?> addInterest(
            @PathVariable UUID itineraryId,
            @Validated @RequestBody AddInterestRequest request,
            @AuthenticationPrincipal UserEntity user) {
        logger.info("Adding interest with placeId: {} to itinerary: {} for user: {}",
                request.getPlaceId(), itineraryId, user.getEmail());

        try {
            AddInterestResponse response = interestService.addInterest(itineraryId, request, user);
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            logger.error("Bad request: {}", e.getMessage());
            ErrorResponse errorResponse = new ErrorResponse(
                null,
                new ApiError("BAD_REQUEST", e.getMessage())
            );
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse);
        } catch (SecurityException e) {
            logger.error("Unauthorized access: {}", e.getMessage());
            ErrorResponse errorResponse = new ErrorResponse(
                null,
                new ApiError("FORBIDDEN", e.getMessage())
            );
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(errorResponse);
        } catch (RuntimeException e) {
            logger.error("Not found: {}", e.getMessage());
            ErrorResponse errorResponse = new ErrorResponse(
                null,
                new ApiError("NOT_FOUND", e.getMessage())
            );
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse);
        } catch (Exception e) {
            logger.error("Error adding interest: {}", e.getMessage(), e);
            ErrorResponse errorResponse = new ErrorResponse(
                null,
                new ApiError("INTERNAL_SERVER_ERROR", "An unexpected error occurred")
            );
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Remove a place from an itinerary completely (hard delete)
     *
     * @param itineraryId UUID of the itinerary
     * @param placeId UUID of the place to remove
     * @param user Authenticated user from JWT token
     * @return Success response or error
     */
    @DeleteMapping("/{itineraryId}/places/{placeId}")
    public ResponseEntity<?> deletePlace(
            @PathVariable UUID itineraryId,
            @PathVariable UUID placeId,
            @AuthenticationPrincipal UserEntity user) {
        logger.info("Deleting place: {} from itinerary: {} for user: {}",
                placeId, itineraryId, user.getEmail());

        try {
            interestService.deletePlace(itineraryId, placeId, user);
            return ResponseEntity.ok(java.util.Map.of(
                "success", true,
                "message", "Place removed from itinerary"
            ));
        } catch (IllegalArgumentException e) {
            logger.error("Bad request: {}", e.getMessage());
            ErrorResponse errorResponse = new ErrorResponse(
                null,
                new ApiError("BAD_REQUEST", e.getMessage())
            );
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse);
        } catch (SecurityException e) {
            logger.error("Unauthorized access: {}", e.getMessage());
            ErrorResponse errorResponse = new ErrorResponse(
                null,
                new ApiError("FORBIDDEN", e.getMessage())
            );
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(errorResponse);
        } catch (RuntimeException e) {
            logger.error("Not found: {}", e.getMessage());
            ErrorResponse errorResponse = new ErrorResponse(
                null,
                new ApiError("NOT_FOUND", e.getMessage())
            );
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse);
        } catch (Exception e) {
            logger.error("Error deleting place: {}", e.getMessage(), e);
            ErrorResponse errorResponse = new ErrorResponse(
                null,
                new ApiError("INTERNAL_SERVER_ERROR", "An unexpected error occurred")
            );
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Add a new place to an itinerary (from Google Places or manual entry)
     *
     * @param itineraryId UUID of the itinerary
     * @param request AddPlaceRequest containing place details
     * @param user Authenticated user from JWT token
     * @return AddInterestResponse with place details
     */
    @PostMapping("/{itineraryId}/places")
    public ResponseEntity<?> addPlace(
            @PathVariable UUID itineraryId,
            @Validated @RequestBody AddPlaceRequest request,
            @AuthenticationPrincipal UserEntity user) {
        logger.info("Adding place '{}' to itinerary: {} for user: {}",
                request.getName(), itineraryId, user.getEmail());

        try {
            AddInterestResponse response = interestService.addPlace(itineraryId, request, user);
            return ResponseEntity.status(HttpStatus.CREATED).body(response);
        } catch (IllegalArgumentException e) {
            logger.error("Bad request: {}", e.getMessage());
            ErrorResponse errorResponse = new ErrorResponse(
                null,
                new ApiError("BAD_REQUEST", e.getMessage())
            );
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse);
        } catch (IllegalStateException e) {
            logger.error("Conflict: {}", e.getMessage());
            ErrorResponse errorResponse = new ErrorResponse(
                null,
                new ApiError("CONFLICT", e.getMessage())
            );
            return ResponseEntity.status(HttpStatus.CONFLICT).body(errorResponse);
        } catch (SecurityException e) {
            logger.error("Unauthorized access: {}", e.getMessage());
            ErrorResponse errorResponse = new ErrorResponse(
                null,
                new ApiError("FORBIDDEN", e.getMessage())
            );
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(errorResponse);
        } catch (RuntimeException e) {
            logger.error("Not found: {}", e.getMessage());
            ErrorResponse errorResponse = new ErrorResponse(
                null,
                new ApiError("NOT_FOUND", e.getMessage())
            );
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(errorResponse);
        } catch (Exception e) {
            logger.error("Error adding place: {}", e.getMessage(), e);
            ErrorResponse errorResponse = new ErrorResponse(
                null,
                new ApiError("INTERNAL_SERVER_ERROR", "An unexpected error occurred")
            );
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }
}