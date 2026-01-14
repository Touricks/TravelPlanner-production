import { useState, useEffect } from "react";
import useDebounced from './useDebounced';
import usePlacesClient from './usePlacesClient';
export default function usePlacesPredictions({
  minLength = 2,
  debounceMs = 250,
  includedPrimaryTypes,
  excludedPrimaryTypes,
  includedRegionCodes,
  locationBias,
  locationRestriction,
  // Legacy API params (AutocompleteService)
  types,  // e.g., ['establishment'], ['geocode'], ['address'], ['(cities)']
  componentRestrictions,  // e.g., { country: 'us' }
}) {
  const [input, setInput] = useState("");
  const [options, setOptions] = useState([]);
  const { service, ensureSession, ready } = usePlacesClient();

  const requestPredictions = useDebounced((text) => {
    if (!service || text.trim().length < minLength) {
      setOptions([]);
      return;
    }

    // Use legacy AutocompleteService API format
    const req = {
      input: text,
      sessionToken: ensureSession(),
    };

    // Legacy API uses 'types' not 'includedPrimaryTypes'
    if (types && types.length > 0) {
      req.types = types;
    }
    if (componentRestrictions) {
      req.componentRestrictions = componentRestrictions;
    }
    if (locationBias) {
      // Convert to legacy format if needed
      if (locationBias.center && locationBias.radius) {
        req.location = new window.google.maps.LatLng(locationBias.center.lat, locationBias.center.lng);
        req.radius = locationBias.radius;
      }
    }

    service.getPlacePredictions(req, (preds, status) => {
      if (status === window.google.maps.places.PlacesServiceStatus.OK) {
        setOptions(preds || []);
      } else {
        setOptions([]);
      }
    });
  }, debounceMs);

  useEffect(() => {
    requestPredictions(input);
  }, [input, requestPredictions]);
  return { input, setInput, options, ready };
}