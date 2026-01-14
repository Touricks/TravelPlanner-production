import React from "react";
import { InfoWindow } from "@react-google-maps/api";
import { Box, Typography, Chip, Button, Link, IconButton } from "@mui/material";
import { Phone as PhoneIcon, Language as WebsiteIcon, LocationOn as LocationIcon, PushPin as PinIcon } from "@mui/icons-material";

function getLatLng(location) {
  const lat = typeof location?.lat === "function" ? location.lat() : location?.lat;
  const lng = typeof location?.lng === "function" ? location.lng() : location?.lng;
  return { lat, lng };
}

export default function MapPlacePopup({ selected, onClose, maxWidth = 320 }) {
  // Handle both old Google Places format and new backend format
  const isBackendFormat = selected?.description; // Backend format has description
  
  if (!selected || (!selected?.geometry?.location && !selected?.location)) return null;

  // Get position from either format
  const position = selected?.geometry?.location 
    ? getLatLng(selected.geometry.location)
    : selected?.location || { lat: selected?.latitude, lng: selected?.longitude };
  
  // Extract data based on format
  const name = selected.name || "";
  const description = selected.description || "";
  const address = selected.address || selected.formatted_address || selected.vicinity || "";
  const phone = selected.contact?.phone || "";
  const website = selected.contact?.website || "";
  const imageUrl = selected.imageUrl || "";
  const isPinned = selected.pinned || false;
  const categories = selected.categories || [];
  
  // Legacy Google Places data
  const rating = selected.rating;
  const total = selected.user_ratings_total || 0;

  return (
    <InfoWindow position={position} onCloseClick={onClose}>
      <Box sx={{ 
        fontFamily: "system-ui, -apple-system, Arial", 
        maxWidth, 
        p: 1 
      }}>
        {/* Header with name and pin status */}
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, mb: 1 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, flex: 1, lineHeight: 1.2 }}>
            {name}
          </Typography>
          {isBackendFormat && isPinned && (
            <PinIcon sx={{ color: '#d32f2f', fontSize: 18 }} />
          )}
        </Box>

        {/* Categories */}
        {categories.length > 0 && (
          <Box sx={{ mb: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
            {categories.slice(0, 3).map((category, index) => (
              <Chip 
                key={index}
                label={category.replace(/_/g, ' ')} 
                size="small" 
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: 20 }}
              />
            ))}
          </Box>
        )}

        {/* Description (for backend format) */}
        {description && (
          <Typography variant="body2" sx={{ color: "#666", mb: 1, fontSize: '0.85rem' }}>
            {description}
          </Typography>
        )}

        {/* Address */}
        {address && (
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5, mb: 1 }}>
            <LocationIcon sx={{ fontSize: 14, color: '#666', mt: 0.2 }} />
            <Typography variant="body2" sx={{ color: "#666", fontSize: '0.8rem' }}>
              {address}
            </Typography>
          </Box>
        )}

        {/* Rating (for Google Places format) */}
        {rating != null && (
          <Typography variant="body2" sx={{ color: "#333", mb: 1, fontSize: '0.85rem' }}>
            ⭐ {rating} ({total} reviews)
          </Typography>
        )}

        {/* Contact information */}
        <Box sx={{ display: 'flex', gap: 0.5, mb: 1, flexWrap: 'wrap' }}>
          {phone && (
            <Button
              size="small"
              startIcon={<PhoneIcon />}
              href={`tel:${phone}`}
              sx={{ minWidth: 'auto', px: 1, py: 0.5, fontSize: '0.7rem' }}
            >
              Call
            </Button>
          )}
          {website && (
            <Button
              size="small"
              startIcon={<WebsiteIcon />}
              component={Link}
              href={website}
              target="_blank"
              rel="noopener noreferrer"
              sx={{ minWidth: 'auto', px: 1, py: 0.5, fontSize: '0.7rem' }}
            >
              Website
            </Button>
          )}
        </Box>

        {/* Image */}
        {imageUrl && (
          <Box sx={{ mt: 1 }}>
            <img 
              src={imageUrl} 
              alt={name}
              style={{ 
                width: '100%', 
                maxHeight: '120px', 
                objectFit: 'cover', 
                borderRadius: '4px' 
              }}
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
          </Box>
        )}
      </Box>
    </InfoWindow>
  );
}
