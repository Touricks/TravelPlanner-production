
import { Box, Typography } from '@mui/material';
function Title({ src, title, description }) {
  return (
    <>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Box
          component="img"
          src={src}
          alt="Travel"
          sx={{ width: 32, height: 32, marginRight: 1, objectFit: 'cover' }}
        />
        <Typography variant="h6" component="h1" sx={{ mr: 2 }}>
          {title}
        </Typography>
      </Box>

      {description && <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        {description}
      </Typography>}
    </>
  );
}

export default Title;