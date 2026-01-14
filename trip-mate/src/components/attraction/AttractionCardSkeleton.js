import { Card, CardActionArea, CardContent, Typography, Box, Skeleton } from "@mui/material";
import PlaceIcon from '@mui/icons-material/Place';

export default function AttractionCardSkeleton() {
  return (
    <Card sx={{ height: 80, width: '100%', minWidth: 360, borderRadius: 2 }}   >
      <CardActionArea sx={{ display: "flex", alignItems: "center", }}>
        <Typography variant="h6" color="text.secondary" sx={{ px: 3 }}>
          <Skeleton variant="text" width={20} />
        </Typography>

        <Skeleton
          variant="rectangular"
          width={60}
          height={60}
          sx={{ borderRadius: 2 }}
        />

        <CardContent sx={{ flex: 1, pl: 2 }}>
          <Box display="flex" alignItems="center" gap={1}>
            <PlaceIcon fontSize="small" color="disabled" />
            <Skeleton variant="text" width="70%" height={20} />
          </Box>
          <Box display="flex" alignItems="center" gap={1} mt={0.5}>
            <Skeleton variant="text" width="40%" height={16} />
          </Box>
        </CardContent>
      </CardActionArea>
    </Card>
  );
}