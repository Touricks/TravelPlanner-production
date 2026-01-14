import { Box, Typography, Checkbox, FormControlLabel, FormGroup, Radio, RadioGroup } from '@mui/material';
import { travelStyles, transportationOptions, travelPaceOptions, activityIntensityOptions } from './travelSetupOptions'
import SmallButton from "../SmallButton";

const TravelPreferences = ({ onPrev, onNext, onChange, preferences }) => {
  const handleCheckboxChange = (category, option) => {
    onChange(prev => {
      const newPrefs = { ...prev };

      if (newPrefs[category].some((o) => o.id === option.id)) {
        newPrefs[category] = newPrefs[category].filter(item => item.id !== option.id);
      } else {
        newPrefs[category] = [...newPrefs[category], option];
      }

      return newPrefs;
    });
  };

  const handleRadioChange = (category, optionId) => {
    console.log(`🔍 DEBUG - Radio change: category=${category}, optionId=${optionId}`);
    onChange(prev => {
      const newPrefs = { ...prev };
      newPrefs[category] = optionId;
      console.log(`🔍 DEBUG - Updated preferences:`, newPrefs);
      return newPrefs;
    });
  };

  const renderCheckboxGroup = (title, options, category) => (
    <>
      <Typography variant="body1" sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        {title}
      </Typography>
      <FormGroup row sx={{ flexWrap: 'wrap' }}>
        {options.map((option) => (
          <Box key={option.id} sx={{ width: '45%' }}>
            <FormControlLabel
              key={option.id}
              control={
                <Checkbox
                  size="small"
                  checked={preferences[category].some((o) => o.id === option.id)}
                  onChange={() => handleCheckboxChange(category, option)}
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

  const renderRadioGroup = (title, options, category) => (
    <>
      <Typography variant="body1" sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        {title}
      </Typography>
      <RadioGroup
        value={preferences[category] || ''}
        onChange={(e) => handleRadioChange(category, e.target.value)}
        row
        sx={{ flexWrap: 'wrap' }}
      >
        {options.map((option) => (
          <Box key={option.id} sx={{ width: '45%' }}>
            <FormControlLabel
              value={option.id}
              control={<Radio size="small" />}
              label={
                <Box display="flex" alignItems="center" gap={1}>
                  <span>{option.icon}</span>
                  <span>{option.label}</span>
                </Box>
              }
            />
          </Box>
        ))}
      </RadioGroup>
    </>
  );

  return (
    <Box sx={{ mx: 'auto' }}>
      {renderCheckboxGroup(
        "What's your travel style?",
        travelStyles,
        "travelStyle"
      )}

      {renderRadioGroup(
        "How do you prefer to get around?",
        transportationOptions,
        "transportation"
      )}

      {renderRadioGroup(
        "What's your travel pace?",
        travelPaceOptions,
        "travelPace"
      )}

      {renderRadioGroup(
        "What's your preferred activity intensity?",
        activityIntensityOptions,
        "activityIntensity"
      )}

      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <SmallButton variant="outlined" onClick={onPrev}>
          Prev
        </SmallButton>
        <SmallButton variant="outlined" onClick={onNext}>
          Next
        </SmallButton>
      </Box>
    </Box>
  );
};

export default TravelPreferences;