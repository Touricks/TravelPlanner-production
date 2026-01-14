import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Typography, Box, Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions } from "@mui/material";

import { TravelSetupDialog } from "../../components/travel-setup";
import PageContainer from "../../layouts/PageContainer";
import PlacesAutocomplete from "../../components/PlacesAutocomplete";
import bg from "../../assets/bg.png";

export default function Setup() {
  const [destination, setDestination] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [openDialog, setOpenDialog] = useState(false);
  const [open, setOpen] = useState(false);
  const [countdown, setCountdown] = useState(5);
  const [data, setData] = useState({});

  const navigate = useNavigate();
  const handleConfirmDialog = ({ id }) => {
    setOpenDialog(false);
    setOpen(true);
    setData({ id })
  }
  const startPlanningHandler = () => {

    setOpenDialog(true);
    setSubmitting(true);

    setTimeout(() => {
      setSubmitting(false);
    }, 3000);
  }

  useEffect(() => {
    if (!open) return;

    const interval = setInterval(() => {
      setCountdown((prev) => prev - 1);
    }, 1000);


    const timer = setTimeout(() => {
      navigate(`/plan/${data.id}`);
    }, 5000);

    // clear timers on unmount or when dialog is closed
    return () => {
      clearInterval(interval);
      clearTimeout(timer);
    };
  }, [open, navigate, data.id]);

  const handleGoNow = () => {
    navigate(`/plan/${data.id}`);
  };


  return <PageContainer
    center
    sx={{
      pt: 20,
      backgroundImage: `url(${bg})`,
      backgroundSize: '100%',
      backgroundRepeat: 'no-repeat',
      backgroundPosition: 'bottom',
    }}>
    <Typography variant="h3" fontWeight={800} gutterBottom>
      Where do you want to go?
    </Typography>
    <Typography color="text.secondary">
      Pick one place. We'll take it from there.
    </Typography>

    <PlacesAutocomplete
      sx={{ pt: 4 }}
      size="large"
      onSelect={(v) => setDestination(v)}
      onClear={() => setDestination(null)}
    />

    <Box sx={{ my: 4 }}>
      <Button
        loading={submitting}
        loadingPosition="start"
        onClick={startPlanningHandler}
        variant="contained"
        disabled={!destination || submitting}
      >
        {!destination ? "Select a Place" : (submitting ? "Waiting..." : "Start planning")}
      </Button>

      <TravelSetupDialog
        destination={destination}
        open={openDialog}
        onClose={() => setOpenDialog(false)}
        title={`Trip to ${destination?.name}`}
        onConfirm={handleConfirmDialog}
      />


      <Dialog open={open} aria-labelledby="alert-dialog-title" aria-describedby="alert-dialog-description">
        <DialogTitle id="alert-dialog-title">
          {"🎉 Your attractions are ready!"}
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="alert-dialog-description">
            Redirecting to your itinerary in <b>{countdown} s</b>...
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleGoNow} autoFocus>
            Go Now
          </Button>
        </DialogActions>
      </Dialog>

    </Box>

  </PageContainer>
}