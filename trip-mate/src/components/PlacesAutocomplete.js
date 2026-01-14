import { useMemo } from "react";
import { Box, Chip, TextField, Autocomplete } from "@mui/material";
import { levelFromPrediction, levelLabel, defaultFilterOptions } from "../utils/map";
import usePlacesPredictions from "../hooks/usePlacesPredictions";
import usePlaceDetails from "../hooks/usePlaceDetails";

// UI: Option item renderer
function OptionItem({ props, option }) {
  const level = levelFromPrediction(option);
  const label = levelLabel(level);
  return (
    <li {...props} key={option.place_id}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, width: "100%" }}>
        <span aria-hidden>📍</span>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Box sx={{ fontWeight: 700, lineHeight: 1.2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {option.structured_formatting?.main_text ?? option.description}
          </Box>
          <Box sx={{ fontSize: 12, opacity: 0.75, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {option.structured_formatting?.secondary_text}
          </Box>
        </Box>
        {label && (
          <Chip
            label={label}
            size="small"
            sx={{
              bgcolor: "secondary",
              color: "primary",
              fontWeight: 700,
              borderRadius: "12px",
              px: 0.5
            }}
          />
        )}
      </Box>
    </li>
  );
}


/**
 * Place Autocomplete (Google Places)
 *
 * Props:
 * - onSelect(placeDetail)  // Returns detail including geometry.location when a place is selected
 * - placeholder
 * - fields: Required fields from Place Details (defaults are sufficient)
 * - types / componentRestrictions / locationBias: Prediction controls
 * - minLength: Minimum input length to trigger prediction (default: 2)
 * - debounceMs: Debounce delay in milliseconds
 * - sx / size / variant: Passed through to MUI
 */
export default function PlacesAutocomplete({
  onSelect,
  onClear,
  placeholder = "Where to?",
  fields = ["geometry", "name", "place_id", "formatted_address", "editorial_summary", "types", "address_components"],
  includedPrimaryTypes = ["locality", "administrative_area_level_1", "country"],
  excludedPrimaryTypes = ["administrative_area_level_2", "administrative_area_level_3", "postal_code"],
  includedRegionCodes = ["US", "CA", "CN", "JP"],
  locationBias,               // { radius, center }
  locationRestriction,        // { north, south, east, west }
  // Legacy API params
  types,                      // e.g., ['establishment'] for POIs
  componentRestrictions,      // e.g., { country: 'us' }
  filterOptions: customFilterOptions, // Custom filter function, defaults to defaultFilterOptions
  minLength = 2,
  debounceMs = 250,
  size = "small",
  variant = "outlined",
  sx,
}) {

  const predParams = useMemo(
    () => ({
      minLength,
      debounceMs,
      includedPrimaryTypes,
      excludedPrimaryTypes,
      includedRegionCodes,
      locationBias,
      locationRestriction,
      types,
      componentRestrictions,
    }),
    [
      minLength,
      debounceMs,
      includedPrimaryTypes,
      excludedPrimaryTypes,
      includedRegionCodes,
      locationBias,
      locationRestriction,
      types,
      componentRestrictions,
    ]
  );

  const { input, setInput, options, ready } = usePlacesPredictions(predParams);
  const { fetchDetails, refreshSession } = usePlaceDetails();


  return (
    <Autocomplete
      disabled={!ready}
      freeSolo
      options={options}
      filterOptions={customFilterOptions || defaultFilterOptions}
      getOptionLabel={(o) => (typeof o === "string" ? o : o.description)}
      onInputChange={(_, v) => setInput(v)}
      onChange={async (_, val) => {
        if (val === null) {
          onClear?.();
        }
        if (!val?.place_id) return;
        try {
          const detail = await fetchDetails(val.place_id, fields);
          refreshSession();
          onSelect?.(detail);
        } catch (e) {
          console.error(e);
        }
      }}
      renderInput={(params) => (
        <TextField {...params} placeholder={placeholder} size={size} variant={variant} />
      )}
      renderOption={(props, option) => (
        <OptionItem key={option.place_id} props={props} option={option} />
      )}
      noOptionsText={input.trim().length < minLength ? "Type more characters" : "No places found"}
      sx={{
        width: 360,
        "& .MuiAutocomplete-paper": {
          borderRadius: 8,
          boxShadow: "0 8px 24px rgba(0,0,0,0.12)",
        },
        ...sx,
      }}
    />
  );
}