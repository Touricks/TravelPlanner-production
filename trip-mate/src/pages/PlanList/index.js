import { useState, useEffect } from "react";
import { Box, Typography, Container } from "@mui/material";
import { getUserItineraries } from "../../api";
import PlansList from "../../components/plan/PlansList";

export default function PlanList() {
  const [itineraries, setItineraries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchItineraries = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await getUserItineraries();
        setItineraries(response.items);
      } catch (err) {
        setError(err.message);
        console.error("Failed to fetch itineraries:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchItineraries();
  }, []);

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      {" "}
      {/* Changed from lg to xl for more width */}
      <Box mb={4}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Your Trip Plans
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage and view your travel itineraries
        </Typography>
      </Box>
      <PlansList itineraries={itineraries} loading={loading} error={error} />
    </Container>
  );
}
