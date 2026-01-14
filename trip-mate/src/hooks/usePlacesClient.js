import { useState, useRef, useEffect, useCallback } from "react";

export default function usePlacesClient(options = {}) {
  const [ready, setReady] = useState(false);
  const serviceRef = useRef(null);      // AutocompleteService
  const placesServiceRef = useRef(null); // PlacesService
  const sessionTokenRef = useRef(null);

  useEffect(() => {
    const g = window.google;
    if (!g?.maps?.places) return;

    // Prediction service
    serviceRef.current = new g.maps.places.AutocompleteService();

    // Details service requires a host (map or div). Use provided host or an offscreen div
    const host = options.host || document.createElement("div");
    placesServiceRef.current = new g.maps.places.PlacesService(host);

    // Start a fresh session
    sessionTokenRef.current = new g.maps.places.AutocompleteSessionToken();

    setReady(true);
  }, [options.host]);

  const ensureSession = useCallback(() => {
    if (!sessionTokenRef.current) {
      sessionTokenRef.current = new window.google.maps.places.AutocompleteSessionToken();
    }
    return sessionTokenRef.current;
  }, []);

  const refreshSession = useCallback(() => {
    sessionTokenRef.current = new window.google.maps.places.AutocompleteSessionToken();
  }, []);

  return {
    ready,
    service: serviceRef.current,
    placesService: placesServiceRef.current,
    ensureSession,
    refreshSession,
  };
}