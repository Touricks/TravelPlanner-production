import { Box, Radio, RadioGroup, FormControlLabel } from '@mui/material';
import { budgetOptions } from './travelSetupOptions';
import SmallButton from "../SmallButton";

function TravelBudget({ onPrev, onNext, budget, onChange }) {
  const renderLabel = (option) => {
    if (!option.icon) {
      return option.label;
    }

    return (
      <Box display="flex" alignItems="center">
        {option.icon}
        <Box sx={{ marginLeft: 1 }}>
          {option.label}
        </Box>
      </Box>
    );
  };
  return <>
    <Box sx={{ display: "flex", justifyContent: "center", mt: 2 }}>
      <RadioGroup value={budget}
        onChange={(e) => onChange(e.target.value)}>
        {budgetOptions.map((option) => (
          <FormControlLabel
            key={option.id}
            value={option.id}
            control={<Radio />}
            label={renderLabel(option)}
          />
        ))}
      </RadioGroup>
    </Box>
    <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
      <SmallButton variant="outlined" onClick={onPrev}>
        Prev
      </SmallButton>
      <SmallButton variant="outlined" onClick={onNext}>
        Next
      </SmallButton>
    </Box>
  </>;

}
export default TravelBudget;