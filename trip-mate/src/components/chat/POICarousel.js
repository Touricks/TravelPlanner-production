import React from 'react';
import { Box, Card, CardContent, CardMedia, Typography, Chip, Rating, Stack, CircularProgress } from '@mui/material';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import usePlacePhoto from '../../hooks/usePlacePhoto';

function POICard({ poi }) {
  // Use usePlacePhoto hook to fetch photo from Google Places API when image_url is not available
  const { photoUrl, loading } = usePlacePhoto(
    poi.image_url ? null : {
      name: poi.name,
      address: poi.city || '',
      location: (poi.latitude && poi.longitude) ? {
        lat: poi.latitude,
        lng: poi.longitude
      } : undefined
    }
  );

  const displayUrl = poi.image_url || photoUrl;

  return (
    <Card
      sx={{
        minWidth: 280,
        maxWidth: 280,
        flexShrink: 0,
        borderRadius: 2,
        boxShadow: 2,
        '&:hover': {
          boxShadow: 4,
          transform: 'translateY(-2px)',
          transition: 'all 0.2s ease-in-out',
        },
      }}
    >
      <CardMedia
        component="div"
        sx={{
          height: 140,
          bgcolor: 'grey.200',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {loading ? (
          <CircularProgress size={24} />
        ) : displayUrl ? (
          <Box
            component="img"
            src={displayUrl}
            alt={poi.name}
            sx={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : (
          <LocationOnIcon sx={{ fontSize: 48, color: 'grey.400' }} />
        )}
      </CardMedia>
      <CardContent sx={{ p: 2 }}>
        <Typography variant="subtitle1" fontWeight="bold" noWrap>
          {poi.name}
        </Typography>
        {poi.city && (
          <Typography variant="body2" color="text.secondary" noWrap>
            {poi.city}
          </Typography>
        )}
        <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 1 }}>
          {poi.rating && (
            <Rating value={poi.rating} precision={0.1} size="small" readOnly />
          )}
          {poi.primary_category && (
            <Chip label={poi.primary_category} size="small" variant="outlined" />
          )}
        </Stack>
        {poi.description && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              mt: 1,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {poi.description}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}

export default function POICarousel({ pois }) {
  if (!pois || pois.length === 0) return null;

  return (
    <Box sx={{ my: 2, px: 2 }}>
      <Typography variant="subtitle1" fontWeight="bold" sx={{ mb: 1 }}>
        Recommended Places ({pois.length})
      </Typography>
      <Box
        sx={{
          display: 'flex',
          gap: 2,
          overflowX: 'auto',
          pb: 2,
          '&::-webkit-scrollbar': {
            height: 8,
          },
          '&::-webkit-scrollbar-track': {
            bgcolor: 'grey.100',
            borderRadius: 4,
          },
          '&::-webkit-scrollbar-thumb': {
            bgcolor: 'grey.400',
            borderRadius: 4,
          },
        }}
      >
        {pois.map((poi, index) => (
          <POICard key={poi.id || index} poi={poi} />
        ))}
      </Box>
    </Box>
  );
}
