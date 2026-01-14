import {
  Box,
  Typography,
  Checkbox,
  FormControlLabel,
  FormGroup,
  TextField,
} from '@mui/material';
import { dietaryOptions } from './travelSetupOptions';
import SmallButton from "../SmallButton";


const TravelSpecialRequests = ({ onPrev, mustSee = '', onMustSeeChange, dietaryRestrictions = [], onDietaryRestrictionsChange }) => {
  const handleCheckboxChange = (option) => {
    onDietaryRestrictionsChange && onDietaryRestrictionsChange(prev => {
      let newValue = [...prev];
      if (option.id === 'none') {
        // if "None" is selected, clear all other selections
        newValue = newValue.some((o) => o.id === option.id) ? [] : [option];
      } else if (newValue.some((o) => o.id === 'none')) {
        // if "None" is already selected, remove it when another option is selected
        newValue = [option];
      } else {
        // normal toggle behavior
        if (newValue.some((o) => o.id === option.id)) {
          newValue = newValue.filter(item => item.id !== option.id);
        } else {
          newValue = [...newValue, option];
        }
      }
      return newValue;
    });
  };

  const renderCheckboxGroup = (title, options, category) => (
    <>
      <Typography variant="body1" sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        {title}
      </Typography>
      <FormGroup row sx={{ flexWrap: 'wrap' }}>
        {options.map((option) => (
          <Box key={option.id} sx={{ width: '50%' }}>
            <FormControlLabel
              key={option.id}
              control={
                <Checkbox
                  size="small"
                  checked={dietaryRestrictions.some((o) => o.id === option.id)}
                  onChange={() => handleCheckboxChange(option)}
                />
              }
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  <span>{option.icon}</span>
                  <span>{option.label}</span>
                </Box>
              }
            />
          </Box>
        ))}
      </FormGroup>
    </>
  );

  return (
    <Box sx={{ mx: 'auto' }}>

      {renderCheckboxGroup(
        "Any dietary restrictions?",
        dietaryOptions,
        "dietaryRestrictions"
      )}

      <Box sx={{ mt: 2 }}>
        <Typography variant="boday1" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
          Must-see places?
        </Typography>
        <TextField
          fullWidth
          multiline
          rows={3}
          placeholder="Any specific places you definitely want to visit? (Optional)"
          value={mustSee}
          onChange={(e) => onMustSeeChange(e.target.value)}
          variant="outlined"
          size="small"
        />
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          e.g., Golden Gate Bridge, Alcatraz, specific restaurants, etc.
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <SmallButton variant="outlined" onClick={onPrev}>
          Prev
        </SmallButton>
      </Box>
    </Box>
  );
};

export default TravelSpecialRequests;