import { useState, useEffect } from "react";
import {
  Card,
  CardMedia,
  CardActionArea,
  CardContent,
  Typography,
  Box,
  Chip,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import PlaceIcon from "@mui/icons-material/Place";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";
import { getItineraryFirstPlaceImage, getItineraryImage } from "../../api";
import usePlacePhoto from "../../hooks/usePlacePhoto";

export default function PlanCardWithPhoto({ itinerary }) {
  const [firstPlace, setFirstPlace] = useState(null);
  const [fallbackImageUrl, setFallbackImageUrl] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    getItineraryFirstPlaceImage(itinerary.id).then(setFirstPlace);
    getItineraryImage(itinerary.id).then(setFallbackImageUrl);
  }, [itinerary.id]);

  const { photoUrl } = usePlacePhoto(firstPlace);

  const handleCardClick = () => navigate(`/plan/${itinerary.id}`);
  const formatTravelMode = (travelMode) =>
    travelMode?.toLowerCase().replace("_", " ");
  const formatTravelPace = (travelPace) =>
    travelPace?.toLowerCase().replace("_", " ");

  const getTravelPaceColor = (travelPace) => {
    switch (travelPace?.toUpperCase()) {
      case "RELAXED":
        return "success";
      case "MODERATE":
        return "primary";
      case "PACKED":
        return "warning";
      default:
        return "primary";
    }
  };

  const formatDateRange = (startDate, endDate) => {
    if (!startDate || !endDate) return ""; // Guard against missing dates
    const start = new Date(startDate);
    const end = new Date(endDate);
    const options = { month: "short", day: "numeric" };
    if (start.getFullYear() === end.getFullYear()) {
      return `${start.toLocaleDateString(
        "en-US",
        options
      )} - ${end.toLocaleDateString("en-US", options)}, ${start.getFullYear()}`;
    }
    return `${start.toLocaleDateString("en-US", {
      ...options,
      year: "numeric",
    })} - ${end.toLocaleDateString("en-US", { ...options, year: "numeric" })}`;
  };

  const getImageUrl = () => {
    if (photoUrl) return photoUrl;
    if (fallbackImageUrl) return fallbackImageUrl;
    return "/images/destinations/default.jpg";
  };

  return (
    <Card
      sx={{
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        borderRadius: 2,
        overflow: "hidden",
        transition: "transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out",
        "&:hover": { transform: "translateY(-4px)", boxShadow: 4 },
      }}
    >
      <CardActionArea
        onClick={handleCardClick}
        sx={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "stretch",
        }}
      >
        {/* FIX #1: USE ASPECT RATIO FOR CONSISTENT IMAGE HEIGHT */}
        <CardMedia
          component="img"
          sx={{
            width: "100%",
            aspectRatio: "16/9", // Enforce aspect ratio
            objectFit: "cover",
          }}
          image={getImageUrl()}
          alt={itinerary.destinationCity}
          loading="lazy"
        />

        <CardContent
          sx={{
            p: 2,
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <Box>
            <Box display="flex" alignItems="center" gap={1} mb={1}>
              <PlaceIcon fontSize="small" color="primary" />
              <Typography
                variant="h6"
                fontWeight="bold"
                noWrap
                sx={{ overflow: "hidden", textOverflow: "ellipsis" }}
              >
                {itinerary.destinationCity}
              </Typography>
            </Box>

            {/* FIX #2: RESERVE SPACE FOR DATE */}
            <Box
              display="flex"
              alignItems="center"
              gap={1}
              mb={2}
              sx={{ minHeight: "24px" }}
            >
              {itinerary.startDate && itinerary.endDate && (
                <>
                  <CalendarTodayIcon fontSize="small" color="action" />
                  <Typography variant="body2" color="text.secondary">
                    {formatDateRange(itinerary.startDate, itinerary.endDate)}
                  </Typography>
                </>
              )}
            </Box>
          </Box>

          {/* FIX #2: RESERVE SPACE FOR CHIPS */}
          <Box
            display="flex"
            flexWrap="wrap"
            gap={1}
            alignItems="center"
            sx={{ minHeight: "32px" }}
          >
            {itinerary.travelMode && (
              <Chip
                label={formatTravelMode(itinerary.travelMode)}
                size="small"
                variant="outlined"
                sx={{ textTransform: "capitalize" }}
              />
            )}
            {itinerary.travelPace && (
              <Chip
                label={formatTravelPace(itinerary.travelPace)}
                size="small"
                variant="outlined"
                color={getTravelPaceColor(itinerary.travelPace)}
                sx={{ textTransform: "capitalize" }}
              />
            )}
          </Box>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}
