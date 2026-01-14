import { useState, useEffect } from "react";
import AttractionCard from "./AttractionCard";
import usePlacePhoto from "../../hooks/usePlacePhoto";

/**
 * AttractionCard wrapper that fetches real place photos from Google Places API
 */
export default function AttractionCardWithPhoto({ attraction, selected, onClick, onSelected, onDelete }) {
  const [fallbackImage, setFallbackImage] = useState(null);
  
  // Use the place photo hook to fetch real images
  const { photoUrl, loading: photoLoading, error } = usePlacePhoto({
    name: attraction.name,
    address: attraction.address,
    location: attraction.location
  });

  // Set fallback image from backend if available
  useEffect(() => {
    if (attraction.imageUrl) {
      setFallbackImage(attraction.imageUrl);
    }
  }, [attraction.imageUrl]);

  // Determine which image to use
  const getImageUrl = () => {
    if (photoUrl) {
      return photoUrl; // Google Places photo (highest priority)
    }
    if (fallbackImage) {
      return fallbackImage; // Backend provided image
    }
    // Default fallback image
    return "https://images.squarespace-cdn.com/content/v1/5c7f5f60797f746a7d769cab/1708063049157-NMFAB7KBRBY2IG2BWP4E/the+golden+gate+bridge+san+francisco.jpg";
  };

  return (
    <AttractionCard
      selected={selected}
      onClick={onClick}
      onSelected={onSelected}
      onDelete={onDelete}
      image={getImageUrl()}
      title={attraction.name}
      category={attraction.categories?.join(", ") || attraction.category || ""}
      id={attraction.marker_id}
    />
  );
}