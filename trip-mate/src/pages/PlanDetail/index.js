import { useRef, useState, useEffect } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";

import {
  Box,
  Typography,
  Button,
  CircularProgress,
  ButtonGroup,
  Menu,
  MenuItem,
  Badge
} from "@mui/material";
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown';
import HistoryIcon from '@mui/icons-material/History';
import VisibilityIcon from '@mui/icons-material/Visibility';
import AddIcon from '@mui/icons-material/Add';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import PageContainer from "../../layouts/PageContainer";
import AttractionsList from "../../components/attraction/AttractionsList";
import { MapCanvas, MapPlacePopup, PlaceMarker } from "../../components/maps";
import useMapMarkers from "../../hooks/useMapMarkers";
import {
  getTripProcess,
  getTripAttractions,
  getTrip,
  getTripPlan,
  getItineraryById,
  getItineraryRecommendations,
  updateInterest,
  deletePlace,
  addPlace,
  planItinerary,
  getPlanHistory,
} from "../../api";
import { dedupPlaces } from "../../utils/map";
import { markerIcon, blueMarkerIcon, redMarkerIcon } from "../../assets";
import ItineraryTimeline from "../../components/ItineraryTimeline";
import PlanHistoryDrawer from "../../components/PlanHistoryDrawer";
import AddPlaceModal from "../../components/AddPlaceModal";

const DEFAULT_CENTER = { lat: 37.7749, lng: -122.4194 };

export default function PlanDetail() {
  const { id } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const mapRef = useRef(null);
  const [destination, setDestination] = useState("");
  const [attractions, setAttractions] = useState([]);
  const [interests, setInterests] = useState([]);
  const [selectedAttraction, setSelectedAttraction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState();
  const [displayPlan, setDisplayPlan] = useState(false);
  const [err, setErr] = useState(null);
  const [mapCenter, setMapCenter] = useState(DEFAULT_CENTER);
  const [generationStatus, setGenerationStatus] = useState({
    pending: false,
    error: null,
    message: null
  });
  const [planHistory, setPlanHistory] = useState([]);
  const [planHistoryLoading, setPlanHistoryLoading] = useState(false);
  const [planHistoryError, setPlanHistoryError] = useState(null);
  const [showHistoryDrawer, setShowHistoryDrawer] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [showAddPlaceModal, setShowAddPlaceModal] = useState(false);
  const [addingPlace, setAddingPlace] = useState(false);
  const [cragSessionId, setCragSessionId] = useState(null);

  const {
    markers,
    selected,
    setSelected,
    addFromPlace,
    clearMarkers,
    removeMarker,
    fitToPlaces,
    zoomMapToPlace,
  } = useMapMarkers(mapRef);

  const onMapLoad = (map) => (mapRef.current = map);

  // Function to calculate center from attractions
  const calculateMapCenter = (attractions) => {
    if (!attractions || attractions.length === 0) {
      return DEFAULT_CENTER;
    }

    // Filter out attractions without valid coordinates
    const validAttractions = attractions.filter(
      a => a.location?.lat && a.location?.lng && 
           !isNaN(a.location.lat) && !isNaN(a.location.lng)
    );

    if (validAttractions.length === 0) {
      return DEFAULT_CENTER;
    }

    // Calculate the average center point
    const centerLat = validAttractions.reduce((sum, a) => sum + a.location.lat, 0) / validAttractions.length;
    const centerLng = validAttractions.reduce((sum, a) => sum + a.location.lng, 0) / validAttractions.length;

    return { lat: centerLat, lng: centerLng };
  };

  useEffect(() => {
    if (!id) return;
    const ac = new AbortController();
    const { signal } = ac;
    let pollingInterval = null;

    async function loadRecommendations(itineraryData) {
      const recommendationsData = await getItineraryRecommendations(id, 0, 50);
      const recommendations = recommendationsData?.items || [];

      const transformedAttractions = recommendations.map((place, index) => ({
        ...place,
        marker_id: index + 1,
        place_id: place.id,
        latitude: place.location?.lat || 37.7749,
        longitude: place.location?.lng || -122.4194,
        location: {
          lat: place.location?.lat || 37.7749,
          lng: place.location?.lng || -122.4194
        },
        name: place.name,
        address: place.address,
        categories: place.categories || [],
        itineraryPlaceId: place.itineraryPlaceRecordId,
        pinned: place.pinned || false,
      }));

      setAttractions(transformedAttractions);

      const pinnedPlaceIds = transformedAttractions
        .filter(place => place.pinned)
        .map(place => place.place_id);
      setInterests(pinnedPlaceIds);

      const newCenter = calculateMapCenter(transformedAttractions);
      setMapCenter(newCenter);

      transformedAttractions.forEach((p, i) => {
        const placeWithGeometry = {
          ...p,
          geometry: {
            location: {
              lat: p.latitude || 37.7749,
              lng: p.longitude || -122.4194
            }
          }
        };
        addFromPlace(placeWithGeometry, i);
      });

      const placesForFitting = transformedAttractions.map(p => ({
        ...p,
        location: {
          lat: p.latitude || 37.7749,
          lng: p.longitude || -122.4194
        }
      }));
      fitToPlaces(placesForFitting);
    }

    async function pollGenerationStatus(itineraryData, pollCount = 0) {
      const MAX_POLLS = 12; // 12 polls * 5 seconds = 60 seconds max

      if (pollCount >= MAX_POLLS) {
        setGenerationStatus({
          pending: false,
          error: 'Recommendation generation timed out. Please refresh the page.',
          message: null
        });
        setLoading(false);
        return;
      }

      try {
        const updatedItinerary = await getItineraryById(id);
        const aiMetadata = updatedItinerary?.aiMetadata || {};

        if (aiMetadata.generation_pending === false) {
          // Generation completed
          if (aiMetadata.generation_error) {
            setGenerationStatus({
              pending: false,
              error: aiMetadata.generation_error,
              message: null
            });
          } else {
            setGenerationStatus({
              pending: false,
              error: null,
              message: `Successfully generated ${aiMetadata.generated_places_count || 0} recommendations`
            });
            await loadRecommendations(updatedItinerary);
          }
          setLoading(false);
        } else {
          // Still generating, continue polling
          pollingInterval = setTimeout(() => {
            pollGenerationStatus(itineraryData, pollCount + 1);
          }, 5000);
        }
      } catch (e) {
        if (e.name !== "AbortError") {
          setGenerationStatus({
            pending: false,
            error: 'Failed to check generation status',
            message: null
          });
          setLoading(false);
        }
      }
    }

    async function run() {
      try {
        setLoading(true);
        setErr(null);
        setAttractions([]);
        clearMarkers();

        // Fetch itinerary details first
        const itineraryData = await getItineraryById(id);

        // Set basic trip info
        setDestination(itineraryData?.destinationCity ?? null);
        console.log('Itinerary loaded, cragSessionId:', itineraryData?.cragSessionId);
        setCragSessionId(itineraryData?.cragSessionId ?? null);
        if (itineraryData?.destinationCity) {
          searchParams.set("destination", itineraryData.destinationCity);
          setSearchParams(searchParams);
        }

        // Check AI generation status
        const aiMetadata = itineraryData?.aiMetadata || {};

        if (aiMetadata.generation_pending === true) {
          // AI is still generating recommendations
          setGenerationStatus({
            pending: true,
            error: null,
            message: 'This may take 30-60 seconds...'
          });
          // Start polling
          pollGenerationStatus(itineraryData);
        } else if (aiMetadata.generation_error) {
          // Generation failed
          setGenerationStatus({
            pending: false,
            error: aiMetadata.generation_error,
            message: null
          });
          setLoading(false);
        } else {
          // Generation already completed
          setGenerationStatus({
            pending: false,
            error: null,
            message: null
          });
          await loadRecommendations(itineraryData);
          setLoading(false);
        }

      } catch (e) {
        if (e.name !== "AbortError") setErr(e);
        setLoading(false);
      }
    }

    run();

    // Cleanup: cancel the request and clear polling
    return () => {
      ac.abort();
      if (pollingInterval) {
        clearTimeout(pollingInterval);
      }
    };
  }, [
    id,
    clearMarkers,
    addFromPlace,
    fitToPlaces,
    setSearchParams,
    searchParams,
  ]);

  const attractionClickHandler = (a) => {
    setSelectedAttraction(a);
    zoomMapToPlace(a);
  };
  const attractionSelectedHandler = async (attraction) => {
    // Check current state from both interests array and attraction's pinned property
    const isCurrentlyInInterests = interests.includes(attraction.place_id);
    const isCurrentlyPinned = attraction.pinned || false;
    
    // Use the most reliable source of truth - check both states for consistency
    const currentlySelected = isCurrentlyInInterests || isCurrentlyPinned;
    const newPinnedStatus = !currentlySelected; // Toggle the current state

    console.log('Toggle operation:', {
      place: attraction.name,
      isCurrentlyInInterests,
      isCurrentlyPinned,
      currentlySelected,
      newPinnedStatus
    });

    // Store original state for potential revert
    const originalInterests = [...interests];
    const originalAttractions = attractions.map(attr => ({ ...attr }));

    // Update frontend state IMMEDIATELY for instant visual feedback
    let updatedInterests;
    if (newPinnedStatus) {
      // Add to interests (pin the place)
      updatedInterests = [...interests, attraction.place_id];
    } else {
      // Remove from interests (unpin the place)
      updatedInterests = interests.filter(id => id !== attraction.place_id);
    }
    
    setInterests(updatedInterests);

    // Update the attraction's pinned status in the local state for immediate feedback
    setAttractions(prevAttractions =>
      prevAttractions.map(attr =>
        attr.place_id === attraction.place_id
          ? { ...attr, pinned: newPinnedStatus }
          : attr
      )
    );

    // Then make the API call in the background
    try {
      console.log('Calling updateInterest with:', {
        itineraryId: id, // Pass the itinerary ID from URL params
        placeId: attraction.place_id, // Pass the place ID (not itineraryPlaceId)
        pinned: newPinnedStatus
      });
      await updateInterest(id, attraction.place_id, newPinnedStatus);
      console.log('API call successful');
    } catch (error) {
      console.error('Failed to update interest:', error);
      
      // If API call fails, revert the frontend state to what it was before
      setInterests(originalInterests);
      
      // Revert the attraction's pinned status to original state
      setAttractions(originalAttractions);
      
      // TODO: Show user-friendly error message
      alert('Failed to update interest. Please try again.');
    }
  };

  const handleDeletePlace = async (attraction) => {
    if (!window.confirm(`Remove "${attraction.name}" from this itinerary?`)) {
      return;
    }

    // Store original state for potential revert
    const originalAttractions = [...attractions];
    const originalInterests = [...interests];
    const originalMarkers = [...markers];

    // Optimistic UI update - remove and renumber immediately
    setAttractions(prev =>
      prev.filter(a => a.place_id !== attraction.place_id)
          .map((a, idx) => ({ ...a, marker_id: idx + 1 }))
    );
    setInterests(prev => prev.filter(id => id !== attraction.place_id));
    removeMarker(attraction.place_id);

    // Clear selected attraction if it's the deleted one
    if (selectedAttraction?.place_id === attraction.place_id) {
      setSelectedAttraction(null);
    }

    try {
      console.log('Deleting place:', { itineraryId: id, placeId: attraction.place_id });
      await deletePlace(id, attraction.place_id);
      console.log('Place deleted successfully');
    } catch (error) {
      console.error('Failed to delete place:', error);
      // Revert on error
      setAttractions(originalAttractions);
      setInterests(originalInterests);
      // Note: markers will be restored by the removeMarker being reverted via attractions
      alert('Failed to remove place. Please try again.');
    }
  };

  const handleAddPlace = async (placeData) => {
    setAddingPlace(true);
    try {
      console.log('Adding place to itinerary:', { itineraryId: id, placeData });
      const response = await addPlace(id, placeData);
      console.log('Place added successfully:', response);

      // Add the new place to the attractions list
      const locationData = response.place?.location || {
        lat: placeData.latitude,
        lng: placeData.longitude
      };
      const newAttraction = {
        id: response.place?.id,
        place_id: response.place?.id,
        marker_id: attractions.length + 1,
        name: response.place?.name || placeData.name,
        address: response.place?.address || placeData.address,
        location: locationData,
        latitude: placeData.latitude,
        longitude: placeData.longitude,
        categories: response.place?.categories || [],
        pinned: response.pinned ?? true,
        itineraryPlaceId: response.place?.itineraryPlaceRecordId,
        // Add geometry wrapper for map marker compatibility
        geometry: {
          location: locationData
        },
      };

      setAttractions(prev => [...prev, newAttraction]);
      if (newAttraction.pinned) {
        setInterests(prev => [...prev, newAttraction.place_id]);
      }

      // Add marker to map
      addFromPlace(newAttraction);
    } catch (error) {
      console.error('Failed to add place:', error);
      throw error;
    } finally {
      setAddingPlace(false);
    }
  };

  const togglePlanDisplay = async () => {
    if (!displayPlan) {
      try {
        setLoading(true);

        // Build the plan request based on current interests
        // According to OpenAPI spec, if interestPlaceIds is omitted, it uses all current interests
        const planRequest = {
          // Optional: include specific place IDs if needed
          // interestPlaceIds: interests,

          // Optional: override dates if needed
          // startDate: "2025-10-01T15:00:00+08:00",
          // endDate: "2025-10-05T20:00:00+08:00",

          // Optional planning preferences
          travelMode: "DRIVING", // Default, could be made configurable
          dailyStart: "09:00",
          dailyEnd: "20:00",
          avoidCrowds: false,
          minimizeTransfers: false,
          balanceCategories: true
        };

        console.log('Calling planItinerary with:', { itineraryId: id, planRequest });
        const planData = await planItinerary(id, planRequest);
        setPlan(planData);
        console.log('Plan generated successfully:', planData);
      } catch (error) {
        console.error('Failed to generate plan:', error);
        setErr(error);
        // Don't switch to plan view if the API call failed
        return;
      } finally {
        setLoading(false);
      }
    }
    setDisplayPlan((prev) => !prev);
  };

  // Handle dropdown menu
  const handleMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  // Load plan history
  const loadPlanHistory = async () => {
    try {
      setPlanHistoryLoading(true);
      setPlanHistoryError(null);
      const history = await getPlanHistory(id);
      setPlanHistory(Array.isArray(history) ? history : []);
      setShowHistoryDrawer(true);
    } catch (error) {
      console.error('Failed to load plan history:', error);
      setPlanHistoryError('Failed to load plan history');
    } finally {
      setPlanHistoryLoading(false);
    }
    handleMenuClose();
  };

  // Select a historical plan to view
  const handleSelectHistoricalPlan = (selectedPlan) => {
    setPlan(selectedPlan);
    setDisplayPlan(true);
    setShowHistoryDrawer(false);
  };

  // View the latest plan without generating a new one
  const viewLatestPlan = async () => {
    try {
      setLoading(true);
      const history = await getPlanHistory(id);
      if (Array.isArray(history) && history.length > 0) {
        // Get the most recent plan (first in the sorted list)
        setPlan(history[0]);
        setDisplayPlan(true);
      } else {
        alert('No saved plans found. Please generate a plan first.');
      }
    } catch (error) {
      console.error('Failed to load latest plan:', error);
      alert('Failed to load latest plan. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageContainer maxWidth={false}>
      <Box
        sx={{ display: "flex", overflow: "hidden" }}
        height={{ xs: "calc(100vh - 56px)", sm: "calc(100vh - 64px)" }}
      >
        <Box sx={{ display: "flex", flexDirection: "column", flex: 1, px: 4, bgcolor: "#fafafa" }}>
          <Box
            sx={{
              flexShrink: 0,
              mb: 2,
              py: 2,
              px: 3,
              mx: -4,
              mt: -2,
              bgcolor: "white",
              borderBottom: "2px solid #e0e0e0",
              boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
            }}
          >
            {/* Row 1: Titles */}
            <Box sx={{ display: "flex", alignItems: "center", mb: 1.5 }}>
              <Typography variant="h6" fontWeight="bold">
                Recommendations({attractions.length})
              </Typography>
              <Typography sx={{ ml: 4 }} variant="h6" fontWeight="bold">
                Places to visit ({interests.length})
              </Typography>
            </Box>
            {/* Row 2: Buttons */}
            <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
              {!displayPlan && (
                <Button
                  variant="contained"
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => setShowAddPlaceModal(true)}
                  disabled={loading}
                  color="primary"
                >
                  Add Place
                </Button>
              )}
              {!displayPlan && (
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<VisibilityIcon />}
                  onClick={viewLatestPlan}
                  disabled={loading}
                >
                  View Latest Plan
                </Button>
              )}
              {!displayPlan && (
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<ChatBubbleOutlineIcon />}
                  onClick={() => {
                    console.log('Continue Chat clicked, cragSessionId:', cragSessionId);
                    if (cragSessionId) {
                      navigate(`/chat?session=${cragSessionId}`);
                    } else {
                      alert('No CRAG session available for this itinerary');
                    }
                  }}
                  disabled={loading || !cragSessionId}
                >
                  Continue Chat
                </Button>
              )}
              <ButtonGroup variant="outlined" size="small" disabled={loading}>
                <Button onClick={togglePlanDisplay}>
                  {displayPlan ? "Back" : "Generate Plan"}
                </Button>
                <Button
                  size="small"
                  onClick={handleMenuClick}
                  sx={{ px: 1 }}
                >
                  <ArrowDropDownIcon />
                </Button>
              </ButtonGroup>
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
              >
                <MenuItem onClick={loadPlanHistory}>
                  <HistoryIcon sx={{ mr: 1, fontSize: 20 }} />
                  View Plan History
                  {planHistory.length > 0 && (
                    <Badge
                      badgeContent={planHistory.length}
                      color="primary"
                      sx={{ ml: 1 }}
                    />
                  )}
                </MenuItem>
              </Menu>
            </Box>
          </Box>
          <Box
            sx={{
              pb: 10,
              flex: 1,
              overflow: "scroll",
              "&::-webkit-scrollbar": {
                display: "none", // Chrome / Safari
              },
            }}
          >
            {err && (
              <Box sx={{ mb: 2, p: 2, bgcolor: "error.light", borderRadius: 1 }}>
                <Typography color="error" variant="body2">
                  Error: {err.message || 'Failed to load data'}
                </Typography>
              </Box>
            )}
            {generationStatus.pending && (
              <Box
                sx={{
                  mb: 2,
                  p: 4,
                  borderRadius: 3,
                  textAlign: 'center',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)',
                  position: 'relative',
                  overflow: 'hidden',
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'rgba(255, 255, 255, 0.05)',
                    pointerEvents: 'none'
                  }
                }}
              >
                <CircularProgress
                  size={40}
                  sx={{
                    color: 'white',
                    mb: 2
                  }}
                />
                <Typography
                  variant="h5"
                  sx={{
                    color: 'white',
                    fontWeight: 600,
                    mb: 1.5,
                    position: 'relative',
                    zIndex: 1
                  }}
                >
                  AI is working on your recommendations
                </Typography>
                <Typography
                  variant="body1"
                  sx={{
                    color: 'rgba(255, 255, 255, 0.9)',
                    position: 'relative',
                    zIndex: 1
                  }}
                >
                  {generationStatus.message}
                </Typography>
              </Box>
            )}
            {generationStatus.error && (
              <Box sx={{ mb: 2, p: 2, bgcolor: "warning.light", borderRadius: 1 }}>
                <Typography color="warning.dark" variant="body2">
                  {generationStatus.error}
                </Typography>
              </Box>
            )}
            {!displayPlan && (
              <AttractionsList
                attractions={attractions}
                selected={interests}
                loading={loading}
                onClick={attractionClickHandler}
                onSelected={attractionSelectedHandler}
                onDelete={handleDeletePlace}
              />
            )}
            {displayPlan && plan && <ItineraryTimeline response={plan} destination={destination} />}
            {displayPlan && !plan && loading && (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <Typography>Generating your personalized itinerary...</Typography>
              </Box>
            )}
          </Box>
        </Box>

        <Box
          style={{
            width: "60%",
            transition: "width 280ms ease-in-out",
            flexShrink: 0,
          }}
        >
          <MapCanvas
            center={mapCenter}
            onLoad={onMapLoad}
            height={{ xs: "calc(100vh - 56px)", sm: "calc(100vh - 64px)" }}
          >
            {markers.map((m) => (
              <PlaceMarker
                key={m.id}
                onSelect={() => setSelected(m.place)}
                position={m.position}
                place={m.place}
                iconUrl={
                  interests.includes(m?.place?.place_id)
                    ? redMarkerIcon
                    : m.place?.marker_id === selectedAttraction?.marker_id
                    ? blueMarkerIcon
                    : markerIcon
                }
                size={32}
                labelText={m.place?.marker_id}
                isSelectedAttraction={
                  m.place?.marker_id === selectedAttraction?.marker_id
                }
              />
            ))}

            {selected && (
              <MapPlacePopup
                selected={selected}
                onClose={() => setSelected(null)}
              />
            )}
          </MapCanvas>
        </Box>
      </Box>

      {/* Plan History Drawer */}
      <PlanHistoryDrawer
        open={showHistoryDrawer}
        onClose={() => setShowHistoryDrawer(false)}
        planHistory={planHistory}
        loading={planHistoryLoading}
        error={planHistoryError}
        onSelectPlan={handleSelectHistoricalPlan}
      />

      {/* Add Place Modal */}
      <AddPlaceModal
        open={showAddPlaceModal}
        onClose={() => setShowAddPlaceModal(false)}
        onAdd={handleAddPlace}
        loading={addingPlace}
      />
    </PageContainer>
  );
}
