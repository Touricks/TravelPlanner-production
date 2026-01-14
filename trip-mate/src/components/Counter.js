import { Stack, IconButton, Typography } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import RemoveIcon from "@mui/icons-material/Remove";

export default function Counter({
  value,
  onChange,
  min = 0,
  max = 16,
  size = "small",
}) {
  const handleDec = () => {
    if (value > min) onChange(value - 1);
  };

  const handleInc = () => {
    if (value < max) onChange(value + 1);
  };

  return (
    <Stack direction="row" alignItems="center" spacing={2}>
      <IconButton
        onClick={handleDec}
        disabled={value <= min}
        size={size}
        sx={{ border: 1, borderColor: "divider", width: 26, height: 26 }}
      >
        <RemoveIcon sx={{ fontSize: 20 }} color={value <= min ? '' : 'primary'}  />
      </IconButton>

      <Typography variant="body1" sx={{ width: 24, textAlign: "center", userSelect: 'none'}}>
        {value}
      </Typography>

      <IconButton
        onClick={handleInc}
        disabled={value >= max}
        size={size}
        sx={{ border: 1, borderColor: "divider", width: 26, height: 26 }}
      >
        <AddIcon sx={{ fontSize: 20 }} color={ value >= max ? '' :'primary'}  />
      </IconButton>
    </Stack>
  );
}
