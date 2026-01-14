import { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  CircularProgress,
  Alert,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import PlacesAutocomplete from "../PlacesAutocomplete";

/**
 * Modal for searching and adding new places to an itinerary
 */
export default function AddPlaceModal({ open, onClose, onAdd, loading }) {
  const [selectedPlace, setSelectedPlace] = useState(null);
  const [error, setError] = useState(null);

  const handlePlaceSelect = (placeDetail) => {
    console.log("Place selected:", placeDetail);
    setSelectedPlace(placeDetail);
    setError(null);
  };

  const handleAdd = async () => {
    if (!selectedPlace) {
      setError("Please select a place first");
      return;
    }

    // Extract place data for the API
    const placeData = {
      googlePlaceId: selectedPlace.place_id,
      name: selectedPlace.name,
      address: selectedPlace.formatted_address || selectedPlace.vicinity || "",
      latitude: selectedPlace.geometry?.location?.lat(),
      longitude: selectedPlace.geometry?.location?.lng(),
      description: selectedPlace.editorial_summary?.overview || "",
      source: "google_places",
    };

    console.log("Adding place:", placeData);

    try {
      await onAdd(placeData);
      // Reset state and close on success
      setSelectedPlace(null);
      setError(null);
      onClose();
    } catch (err) {
      setError(err.message || "Failed to add place");
    }
  };

  const handleClose = () => {
    setSelectedPlace(null);
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add Place to Itinerary</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 1 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Search for a place to add to your itinerary
          </Typography>

          <PlacesAutocomplete
            onSelect={handlePlaceSelect}
            onClear={() => setSelectedPlace(null)}
            placeholder="Search for a place (e.g., Everglades National Park)..."
            types={['establishment']}
            filterOptions={(x) => x}
            sx={{ width: "100%", mb: 2 }}
          />

          {selectedPlace && (
            <Box
              sx={{
                mt: 2,
                p: 2,
                bgcolor: "grey.50",
                borderRadius: 1,
                border: "1px solid",
                borderColor: "grey.200",
              }}
            >
              <Typography variant="subtitle1" fontWeight="bold">
                {selectedPlace.name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {selectedPlace.formatted_address || selectedPlace.vicinity}
              </Typography>
              {selectedPlace.editorial_summary?.overview && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  {selectedPlace.editorial_summary.overview}
                </Typography>
              )}
            </Box>
          )}

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleAdd}
          variant="contained"
          disabled={!selectedPlace || loading}
          startIcon={loading ? <CircularProgress size={16} /> : <AddIcon />}
        >
          {loading ? "Adding..." : "Add to Itinerary"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
