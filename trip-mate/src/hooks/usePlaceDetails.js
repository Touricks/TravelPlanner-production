import { useCallback } from "react";
import usePlacesClient from "./usePlacesClient";
export default function usePlaceDetails() {
  const { placesService, ensureSession, refreshSession } = usePlacesClient();

  const fetchDetails = useCallback(
    (placeId, fields) =>
      new Promise((resolve, reject) => {
        if (!placesService) return reject(new Error("PlacesService not ready"));
        const sessionToken = ensureSession();
        placesService.getDetails(
          { placeId, fields, sessionToken },
          (place, status) => {
            const g = window.google;
            if (status === g.maps.places.PlacesServiceStatus.OK && place) {
              resolve(place);
            } else {
              reject(new Error(`getDetails failed: ${status}`));
            }
          }
        );
      }),
    [placesService, ensureSession]
  );

  return { fetchDetails, refreshSession };
}