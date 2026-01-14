import React, { useState } from 'react';
import {
  Box,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Stack,
  Divider,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import PlaceIcon from '@mui/icons-material/Place';

function StopItem({ stop }) {
  return (
    <Box sx={{ display: 'flex', gap: 2, py: 1.5 }}>
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          minWidth: 60,
        }}
      >
        <Typography variant="caption" color="text.secondary">
          {stop.arrival_time}
        </Typography>
        <Box
          sx={{
            width: 2,
            flex: 1,
            bgcolor: 'primary.main',
            my: 0.5,
          }}
        />
        <Typography variant="caption" color="text.secondary">
          {stop.departure_time}
        </Typography>
      </Box>
      <Box sx={{ flex: 1 }}>
        <Stack direction="row" spacing={1} alignItems="center">
          <PlaceIcon color="primary" fontSize="small" />
          <Typography variant="subtitle2" fontWeight="bold">
            {stop.poi_name}
          </Typography>
        </Stack>
        <Stack direction="row" spacing={1} sx={{ mt: 0.5 }}>
          <Chip
            icon={<AccessTimeIcon />}
            label={`${stop.duration_minutes} min`}
            size="small"
            variant="outlined"
          />
        </Stack>
        {stop.activity && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mt: 1 }}
          >
            {stop.activity}
          </Typography>
        )}
      </Box>
    </Box>
  );
}

function DayAccordion({ day, index, defaultExpanded }) {
  return (
    <Accordion defaultExpanded={defaultExpanded}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack direction="row" spacing={2} alignItems="center">
          <CalendarTodayIcon color="primary" />
          <Box>
            <Typography variant="subtitle1" fontWeight="bold">
              Day {day.day_number || index + 1}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {day.date} {day.theme && `- ${day.theme}`}
            </Typography>
          </Box>
          <Chip label={`${day.stops?.length || 0} stops`} size="small" />
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        <Divider sx={{ mb: 2 }} />
        {day.stops?.map((stop, stopIndex) => (
          <StopItem key={stopIndex} stop={stop} />
        ))}
      </AccordionDetails>
    </Accordion>
  );
}

export default function PlanPreview({ plan }) {
  if (!plan || !plan.days || plan.days.length === 0) return null;

  return (
    <Box sx={{ my: 2, px: 2 }}>
      <Typography variant="subtitle1" fontWeight="bold" sx={{ mb: 1 }}>
        Suggested Itinerary
      </Typography>
      <Box sx={{ mb: 1 }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <Typography variant="body2" color="text.secondary">
            {plan.destination}
          </Typography>
          {plan.start_date && plan.end_date && (
            <Typography variant="body2" color="text.secondary">
              {plan.start_date} - {plan.end_date}
            </Typography>
          )}
          <Chip
            label={`${plan.total_days || plan.days.length} days`}
            size="small"
            color="primary"
            variant="outlined"
          />
        </Stack>
      </Box>
      <Box>
        {plan.days.map((day, index) => (
          <DayAccordion
            key={index}
            day={day}
            index={index}
            defaultExpanded={index === 0}
          />
        ))}
      </Box>
    </Box>
  );
}
