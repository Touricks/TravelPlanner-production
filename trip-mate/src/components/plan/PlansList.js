import { Grid, Box, Typography, CircularProgress } from "@mui/material";
import PlanCardWithPhoto from "./PlanCardWithPhoto";

export default function PlansList({ itineraries, loading, error }) {
  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="200px"
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="200px"
      >
        <Typography color="error" variant="body1">
          Failed to load itineraries. Please try again.
        </Typography>
      </Box>
    );
  }

  if (!itineraries || itineraries.length === 0) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="200px"
      >
        <Typography variant="body1" color="text.secondary">
          No itineraries found. Create your first trip plan!
        </Typography>
      </Box>
    );
  }

  return (
    <Grid container spacing={2}>
      {" "}
      {/* Reduced spacing from 3 to 2 */}
      {itineraries.map((itinerary) => (
        <Grid
          item
          xs={12} // 1 card per row on extra small screens (mobile portrait)
          sm={6} // 2 cards per row on small screens (mobile landscape/small tablet)
          md={4} // 3 cards per row on medium screens (tablet portrait) - changed from 6 to 4
          lg={3} // 4 cards per row on large screens (desktop)
          xl={2.4} // 5 cards per row on extra large screens (large desktop) - changed from 3 to 2.4
          key={itinerary.id}
          sx={{
            display: "flex", // Ensure flex behavior
            "& > *": {
              width: "100%", // Force child (card) to take full width
              minWidth: 0, // Allow shrinking if needed
            },
          }}
        >
          <PlanCardWithPhoto itinerary={itinerary} />
        </Grid>
      ))}
    </Grid>
  );
}
