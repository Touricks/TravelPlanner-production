import React, { useState, useMemo } from 'react';
import { TabContext, TabList, TabPanel } from '@mui/lab';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Slide, Tab, Box
} from '@mui/material';
import {
  Travelers,
  TravelDatePicker,
  TravelBudget,
  TravelSpecialRequests,
  TravelSummary,
  TravelPreferences,
  Title,
} from "../travel-setup";
import GlobalLoadingOverlay from '../GlobalLoadingOverlay';
import { createTrip } from '../../api';

import { friendsIcon, budgetIcon, travelIcon, calendarIcon, preferenceIcon, dishIcon } from '../../assets';

const calculateDaysDifference = (start, end) => {
  if (!start || !end) return 0;
  const diffTime = end.getTime() - start.getTime() + 1; // include the end date
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
};

const Transition = React.forwardRef(function Transition(props, ref) {
  return (
    <Slide
      direction="down"
      timeout={{ appear: 500, enter: 500, exit: 500 }}
      style={{ transformOrigin: 'center top' }}
      ref={ref}
      {...props}
    />
  );
});
const TravelSetupDialog = ({ open, onClose, title, onConfirm, destination = { name: '', place_id: '' } }) => {
  const [tabValue, setTabValue] = React.useState('1');
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [adults, setAdults] = useState(1);
  const [children, setChildren] = useState(0);
  const [infants, setInfants] = useState(0);
  const [elderly, setElderly] = useState(0);
  const [pets, setPets] = useState(0);
  const [budget, setBudget] = useState('1');
  const [preferences, setPreferences] = useState({
    travelStyle: [],
    transportation: '', // Single-select string value (DRIVING/TRANSIT/WALKING/BICYCLING)
    travelPace: '', // Single-select string value (RELAXED/MODERATE/PACKED)
    activityIntensity: '', // Single-select string value (RELAXED/MODERATE/PACKED)
  });
  const [mustSee, setMustSee] = useState('');
  const [dietaryRestrictions, setDietaryRestrictions] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  const duration = useMemo(() => {
    return calculateDaysDifference(startDate, endDate);
  }, [startDate, endDate]);
  const total = useMemo(() => adults + children + infants, [
    adults,
    children,
    infants,
  ]);

  const handleClearDates = () => {
    setStartDate(null);
    setEndDate(null);
  }
  const designTrip = async () => {
    // validations
    const start = startDate

    const end = endDate;
    if (!start || !end || !duration) {
      return alert('Please select your travel dates first.');
    }
    if (!destination?.name || !destination?.place_id) {
      return alert('Please pick a destination from the map/search first.');
    }
    // json payload
    const payload = {
      destination: destination.name, // "San Mateo, California"
      place_id: destination.place_id, // "dasae3"
      startDate: startDate.toISOString().split('T')[0], // YYYY-MM-DD format
      endDate: endDate.toISOString().split('T')[0],
      travelers: {
        adults,
        children,
        infants,
        elderly,
        pets,
      },
      budget: budget, // Keep as string to match budgetOptions.id type
      preferences: {
        travelStyle: preferences?.travelStyle.map(o => o.id) || [], // Now array of enum strings
        transportation: preferences?.transportation || '', // Single enum string value
        travelPace: preferences?.travelPace || '', // Single enum string value (RELAXED/MODERATE/PACKED)
        activityIntensity: preferences?.activityIntensity || '', // Single enum string value (LIGHT/MODERATE/INTENSE)
        mustSeePlaces: mustSee || '',   // string
      },
    };

    try {
      setSubmitting(true);
      
      // Debug authentication state
      console.log('[designTrip] Payload:', payload);
      const token = localStorage.getItem('authToken');
      console.log('[designTrip] Auth token available:', !!token);
      if (!token) {
        alert('You must be logged in to create a trip. Please log in first.');
        return;
      }
      
      const res = await createTrip(payload);
      // parent component may want to do something with the result
      if (res?.success && typeof onConfirm === 'function') {
        onConfirm(res.data, payload);
      }


    } catch (err) {
      console.error('[designTrip] error:', err);
      const msg = err?.response?.data?.message || 'Failed to design the trip. Please try again.';
      alert(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Dialog
        open={open}
        onClose={onClose}
        maxWidth="md"
        fullWidth
        slots={{
          transition: Transition,
        }}
        PaperProps={{
          sx: {
            minHeight: '620px',
            maxHeight: '80vh',
          }
        }}
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', mb: 3 }} >
          <Box
            component="img"
            src={travelIcon}
            alt="Travel"
            sx={{ width: 20, height: 20, marginRight: 1, objectFit: 'cover' }}
          />
          {title}
        </DialogTitle>
        <DialogContent sx={{ display: 'flex' }}>
          <Box sx={{ flex: 1, pr: 2 }}>
            <TabContext value={tabValue}>
              <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <TabList onChange={(e, v) => setTabValue(v)} aria-label="lab API tabs example">
                  <Tab label="When" value="1" />
                  <Tab label="Who" value="2" />
                  <Tab label="Budget" value="3" />
                  <Tab label="Preferences" value="4" />
                  <Tab label="Special Requests" value="5" />
                </TabList>
              </Box>
              <TabPanel value="1" keepMounted={true}>
                <Title
                  src={calendarIcon}
                  title="Travel Date Picker"
                  description="Select your travel dates. Only future dates are available for booking."
                />
                <TravelDatePicker
                  startDate={startDate}
                  endDate={endDate}
                  onClear={handleClearDates}
                  onStartDateChange={(r) => setStartDate(r)}
                  onEndDateChange={(r) => setEndDate(r)}
                  onNext={() => setTabValue('2')}
                />
              </TabPanel>
              <TabPanel value="2" keepMounted={true}>
                <Title
                  src={friendsIcon}
                  title="Travelers & Pets"
                  description="Tell us who’s going — adults, children, and even pets are welcome."
                />
                <Travelers
                  adults={adults}
                  children={children}
                  infants={infants}
                  elderly={elderly}
                  pets={pets}
                  onAdultsChange={(e) => setAdults(e)}
                  onChildrenChange={(e) => setChildren(e)}
                  onInfantsChange={(e) => setInfants(e)}
                  onElderlyChange={(e) => setElderly(e)}
                  onPetsChange={(e) => setPets(e)}
                  onPrev={() => setTabValue('1')}
                  onNext={() => setTabValue('3')}
                />
              </TabPanel>
              <TabPanel value="3" keepMounted={true}>
                <Title
                  src={budgetIcon}
                  title="Travel Budget"
                  description="Set your budget to get tailored options."
                />
                <TravelBudget
                  onPrev={() => setTabValue('2')}
                  onNext={() => setTabValue('4')}
                  budget={budget} onChange={(e) => setBudget(e)}
                />
              </TabPanel>
              <TabPanel value="4" keepMounted={true}>
                <Title src={preferenceIcon} title="Preferences" />
                <TravelPreferences
                  onPrev={() => setTabValue('3')}
                  onNext={() => setTabValue('5')}
                  preferences={preferences}
                  onChange={setPreferences} />
              </TabPanel>
              <TabPanel value="5" keepMounted={true}>
                <Title src={dishIcon} title="Food & Must-see" />
                <TravelSpecialRequests
                  onNext={() => setTabValue('5')}
                  onPrev={() => setTabValue('4')}
                  mustSee={mustSee}
                  onMustSeeChange={(e) => setMustSee(e)}
                  dietaryRestrictions={dietaryRestrictions}
                  onDietaryRestrictionsChange={e => setDietaryRestrictions(e)}
                />
              </TabPanel>
            </TabContext>
          </Box>
          <Box sx={{ width: 250, ml: 2 }}>
            <TravelSummary startDate={startDate} endDate={endDate} duration={duration} travelers={total} budget={budget} preferences={preferences} dietaryRestrictions={dietaryRestrictions} mustSee={mustSee} />
          </Box>

        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          {onConfirm && (
            <Button
              loading={submitting}
              loadingPosition="start"
              onClick={designTrip}
              variant="contained"
              disabled={!duration || submitting}
              title={!duration ? "Please select travel dates first" : ""}
            >
              {!duration ? "Select Dates First" : (submitting ? "Designing..." : "Design My Trip")}
            </Button>
          )}
        </DialogActions>
      </Dialog>
      <GlobalLoadingOverlay
        open={submitting}
        intervalMs={4000}
        messages={["Analyzing your preferences…",
          "Finding the best attractions for you…",
          "This may take some time. Please hold on."]}
      />
    </>
  );
};
export default TravelSetupDialog;