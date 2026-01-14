import { useMemo } from 'react';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { Box, Typography, Grid } from '@mui/material';
import SmallButton from "../SmallButton";

const TravelDatePicker = ({ startDate, endDate, onEndDateChange, onStartDateChange, onClear, onNext }) => {
  // today - minStartDate
  const today = useMemo(() => {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d;
  }, []);
  // minEndDate, ensure endDate is same or after startDate
  const minEndDate = useMemo(() => {
    if (startDate) {
      const d = new Date(startDate);
      d.setHours(0, 0, 0, 0);
      return d; // allow same day return
    }
    return today;
  }, [startDate, today]);


  // handleStartDateChange
  const handleStartDateChange = (newDate) => {
    onStartDateChange(newDate);
    // clear endDate if it's before or same as new startDate
    if (endDate && newDate && endDate <= newDate) {
      onEndDateChange(null);
    }
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <>
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <Typography variant="body1" sx={{ mb: 2, display: 'flex', alignItems: 'center', }}>
              📅 Start Date
            </Typography>
            <DatePicker
              value={startDate}
              onChange={handleStartDateChange}
              minDate={today}
              slotProps={{
                textField: {
                  size: 'small',
                  fullWidth: true,
                  placeholder: 'Select start date',
                },
              }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="body1" sx={{ mb: 2, display: 'flex', alignItems: 'center', }}>
              📅 End Date
            </Typography>
            <DatePicker
              value={endDate}
              onChange={(v) => onEndDateChange(v)}
              minDate={minEndDate}
              disabled={!startDate}
              slotProps={{
                textField: {
                  size: 'small',
                  fullWidth: true,
                  placeholder: 'Select return date',
                  helperText: !startDate ? 'Please select start date first' : '',
                }
              }}
            />
          </Grid>
        </Grid>

        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
          <SmallButton variant="outlined" onClick={onClear} disabled={!startDate && !endDate}  >
            Clear Dates
          </SmallButton>
          <SmallButton variant="outlined" onClick={onNext} disabled={!startDate || !endDate}>
            Next
          </SmallButton>
        </Box>
      </>

    </LocalizationProvider>
  );
};

export default TravelDatePicker;