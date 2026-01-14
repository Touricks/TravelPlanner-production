import { useState, useEffect } from 'react';

/**
 * Custom hook to fetch place photos using Google Places API
 * @param {Object} place - Place object with name, address, and coordinates
 * @param {string} place.name - Place name
 * @param {string} place.address - Place address
 * @param {Object} place.location - Place coordinates {lat, lng}
 * @returns {Object} { photoUrl, loading, error }
 */
export default function usePlacePhoto(place) {
  const [photoUrl, setPhotoUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!place || !place.name || !window.google?.maps?.places) {
      return;
    }

    setLoading(true);
    setError(null);

    const service = new window.google.maps.places.PlacesService(
      document.createElement('div')
    );

    // First, search for the place to get the place_id
    const request = {
      query: `${place.name} ${place.address || ''}`,
      fields: ['place_id', 'photos', 'name'],
      location: place.location ? new window.google.maps.LatLng(place.location.lat, place.location.lng) : undefined,
      radius: 1000, // 1km radius
    };

    service.textSearch(request, (results, status) => {
      if (status === window.google.maps.places.PlacesServiceStatus.OK && results?.[0]) {
        const placeResult = results[0];
        
        // Get place details to access photos
        const detailsRequest = {
          placeId: placeResult.place_id,
          fields: ['photos']
        };

        service.getDetails(detailsRequest, (place, status) => {
          setLoading(false);
          
          if (status === window.google.maps.places.PlacesServiceStatus.OK && place?.photos?.length > 0) {
            // Get the first photo with a reasonable size
            const photo = place.photos[0];
            const photoUrl = photo.getUrl({
              maxWidth: 400,
              maxHeight: 400
            });
            setPhotoUrl(photoUrl);
          } else {
            setError('No photos found for this place');
          }
        });
      } else {
        setLoading(false);
        setError('Place not found');
      }
    });
  }, [place?.name, place?.address, place?.location?.lat, place?.location?.lng]);

  return { photoUrl, loading, error };
}