import * as React from "react";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Tooltip from "@mui/material/Tooltip";
import Divider from "@mui/material/Divider";
import AccessTimeIcon from "@mui/icons-material/AccessTime";
import PlaceIcon from "@mui/icons-material/Place";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import Timeline from "@mui/lab/Timeline";
import TimelineItem from "@mui/lab/TimelineItem";
import TimelineSeparator from "@mui/lab/TimelineSeparator";
import TimelineConnector from "@mui/lab/TimelineConnector";
import TimelineContent from "@mui/lab/TimelineContent";
import TimelineOppositeContent from "@mui/lab/TimelineOppositeContent";
import TimelineDot from "@mui/lab/TimelineDot";

/** Utility helpers */
const formatDate = (isoDate) => {
  const d = new Date(isoDate + "T00:00:00");
  return d.toLocaleDateString(undefined, {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
  });
};

const timeRangeLabel = (arrival, depart, minutes) => {
  return `${arrival} - ${depart} (${minutes}m)`;
};

/** Build a quick lookup for place closures keyed by `${date}::${place}` */
const buildClosureMap = (warnings) => {
  const map = new Map();
  if (!warnings) return map;
  for (const w of warnings) {
    const det = w.details?.additionalProp1;
    if (!det?.place || !det?.closureDates) continue;
    for (const d of det.closureDates) {
      map.set(`${d}::${det.place}`, { code: w.code, message: w.message });
    }
  }
  return map;
};

/**
 * Timeline component
 */
export default function ItineraryTimeline({ response, alternate = true, destination }) {
  const data = React.useMemo(() => {
    return typeof response === "string" ? JSON.parse(response) : response;
  }, [response]);

  const closureMap = React.useMemo(
    () => buildClosureMap(data.warnings),
    [data]
  );

  const generateTitle = () => {
    if (!data.days || data.days.length === 0) {
      return destination ? `${destination} Itinerary` : "Your Itinerary";
    }

    const startDate = new Date(data.days[0].date + "T00:00:00");
    const endDate = new Date(data.days[data.days.length - 1].date + "T00:00:00");
    
    const dateOptions = { month: 'short', day: 'numeric' };
    const yearOptions = { year: 'numeric' };
    
    let dateRange;
    if (data.days.length === 1) {
      dateRange = startDate.toLocaleDateString(undefined, { ...dateOptions, ...yearOptions });
    } else if (startDate.getFullYear() === endDate.getFullYear()) {
      dateRange = `${startDate.toLocaleDateString(undefined, dateOptions)} - ${endDate.toLocaleDateString(undefined, { ...dateOptions, ...yearOptions })}`;
    } else {
      dateRange = `${startDate.toLocaleDateString(undefined, { ...dateOptions, ...yearOptions })} - ${endDate.toLocaleDateString(undefined, { ...dateOptions, ...yearOptions })}`;
    }

    if (destination) {
      return `${destination} • ${dateRange}`;
    } else {
      return `Travel Itinerary • ${dateRange}`;
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" gutterBottom>
        {generateTitle()}
      </Typography>

      {data.days.map((day) => (
        <Paper key={day.date} elevation={2} sx={{ mb: 3, overflow: "hidden" }}>
          <Box sx={{ px: 2, py: 1.5, bgcolor: "background.default" }}>
            <Typography variant="h6">{formatDate(day.date)}</Typography>
          </Box>
          <Divider />

          <Box sx={{ px: 1.5, py: 2 }}>
            <Timeline position={alternate ? "alternate" : "right"}>
              {day.stops
                .slice()
                .sort((a, b) => a.order - b.order)
                .map((stop, idx, arr) => {
                  const placeName = stop.place?.name || stop.place;
                  const closed = closureMap.get(`${day.date}::${placeName}`);
                  const isLast = idx === arr.length - 1;
                  return (
                    <TimelineItem
                      key={`${day.date}-${stop.order}-${placeName}`}
                    >
                      <TimelineOppositeContent sx={{ flex: 0.25 }}>
                        <Stack
                          direction="row"
                          spacing={0.75}
                          alignItems="center"
                        >
                          <AccessTimeIcon fontSize="small" />
                          <Typography variant="body2">
                            {timeRangeLabel(
                              stop.arrivalLocal,
                              stop.departLocal,
                              stop.stayMinutes
                            )}
                          </Typography>
                        </Stack>
                      </TimelineOppositeContent>

                      <TimelineSeparator>
                        <TimelineDot color={closed ? "error" : "primary"}>
                          <PlaceIcon fontSize="small" />
                        </TimelineDot>
                        {!isLast && <TimelineConnector />}
                      </TimelineSeparator>

                      <TimelineContent>
                        <Paper variant="outlined" sx={{ p: 1.5 }}>
                          <Stack spacing={0.75}>
                            <Typography variant="subtitle1" fontWeight={600}>
                              {stop.order}. {placeName}
                            </Typography>
                            {stop.note && (
                              <Typography
                                variant="body2"
                                color="text.secondary"
                              >
                                {stop.note}
                              </Typography>
                            )}
                            <Stack direction="row" spacing={1} flexWrap="wrap">
                              <Chip
                                size="small"
                                label={`Stay: ${stop.stayMinutes}m`}
                              />
                              <Chip
                                size="small"
                                label={`Arr ${stop.arrivalLocal}`}
                              />
                              <Chip
                                size="small"
                                label={`Dep ${stop.departLocal}`}
                              />
                              {closed && (
                                <Tooltip title={closed.message}>
                                  <Chip
                                    size="small"
                                    color="error"
                                    icon={<WarningAmberIcon />}
                                    label={closed.code}
                                  />
                                </Tooltip>
                              )}
                            </Stack>
                          </Stack>
                        </Paper>
                      </TimelineContent>
                    </TimelineItem>
                  );
                })}
            </Timeline>
          </Box>
        </Paper>
      ))}

      {data.warnings && data.warnings.length > 0 && (
        <Paper
          elevation={0}
          sx={{ p: 2, border: "1px solid", borderColor: "divider" }}
        >
          <Stack spacing={1}>
            <Stack direction="row" spacing={1} alignItems="center">
              <WarningAmberIcon color="warning" />
              <Typography variant="subtitle1" fontWeight={600}>
                Warnings
              </Typography>
            </Stack>
            {data.warnings.map((w, i) => (
              <Box key={i}>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {w.code}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {w.message}
                </Typography>
              </Box>
            ))}
          </Stack>
        </Paper>
      )}
    </Box>
  );
}
