import { Box, Typography, Tooltip } from '@mui/material';
import Counter from '../Counter';
import SmallButton from '../SmallButton';
function Treavelers({
  adults = 1,
  children = 0,
  infants = 0,
  elderly = 0,
  pets = 0,
  onAdultsChange,
  onChildrenChange,
  onInfantsChange,
  onElderlyChange,
  onPetsChange,
  onNext,
  onPrev
}) {
  return (
    <>
      <Box sx={{ display: "flex", flexDirection: 'column', justifyContent: "center", paddingRight: 20 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 0.5 }}>
          <Box>
            <Typography variant="body1">Adults</Typography>
            <Typography variant="body2" color="text.secondary">Ages 13 or above</Typography>
          </Box>

          <Counter label="Adults" value={adults} onChange={onAdultsChange} min={1} max={16} />
        </Box>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 0.5 }}>
          <Box>
            <Typography variant="body1">Children</Typography>
            <Typography variant="body2" color="text.secondary">Ages 2–12</Typography>
          </Box>
          <Counter label="Children" value={children} onChange={onChildrenChange} min={0} max={16} />
        </Box>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 0.5 }}>
          <Box>
            <Typography variant="body1">Infants</Typography>
            <Typography variant="body2" color="text.secondary">Under 2</Typography>
          </Box>
          <Counter label="Infants" value={infants} onChange={onInfantsChange} min={0} max={16} />
        </Box>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 0.5 }}>
          <Box>
            <Typography variant="body1">Elderly</Typography>
            <Typography variant="body2" color="text.secondary">Ages 65+</Typography>
          </Box>
          <Counter label="Elderly" value={elderly} onChange={onElderlyChange} min={0} max={16} />
        </Box>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Box>
            <Typography variant="body1">Pets</Typography>
            <Tooltip arrow title="A service animal is not considered a pet, so you don’t need to include it here.">
              <Typography variant="body2" color="text.secondary" sx={{ cursor: "help" }} >
                Bringing a service animal?
              </Typography>
            </Tooltip>
          </Box>
          <Counter label="Pets" value={pets} min={0} onChange={onPetsChange} max={4} />
        </Box>
      </Box>
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <SmallButton variant="outlined" onClick={onPrev}>
          Prev
        </SmallButton>
        <SmallButton variant="outlined" onClick={onNext}>
          Next
        </SmallButton>
      </Box>
    </>
  );
}

export default Treavelers;