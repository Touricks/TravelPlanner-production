import { Card, CardMedia, CardActionArea, CardContent, Typography, Box, IconButton } from "@mui/material";
import PlaceIcon from '@mui/icons-material/Place';
import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
// import AccessTimeIcon from '@mui/icons-material/AccessTime';

export default function AttractionCard({ image, title, category, id, selected, onClick, onSelected, onDelete }) {
  return (
    <Card
      sx={{ height: 80, width: '100%', minWidth: 360, borderRadius: 2, backgroundColor: selected ? "rgb(233 251 240 / 75%)" : "" }}
      onClick={onClick}
    >
      <CardActionArea sx={{ display: "flex", alignItems: "center", }}>
        <Typography variant="h6" color="text.secondary" sx={{ px: 3 }}>
          {id}
        </Typography>

        <CardMedia
          component="img"
          sx={{ width: 60, height: 60, borderRadius: 2 }}
          image={image}
          alt={title}
        />

        <CardContent sx={{ flex: 1, pl: 2 }}>
          <Box display="flex" alignItems="center" gap={1}>
            <PlaceIcon fontSize="small" />
            <Typography variant="subtitle1" fontWeight="bold">{title}</Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={1} mt={0.5}>
            {/* <AccessTimeIcon fontSize="small" color="action" /> */}
            <Typography variant="body2" color="text.secondary">{category}</Typography>
          </Box>
        </CardContent>

        <IconButton sx={{ mr: 0.5 }} component="span" onClick={(e) => {
          e.stopPropagation();
          onSelected?.();
        }}>
          {selected ? <RemoveIcon /> : <AddIcon />}
        </IconButton>
        {onDelete && (
          <IconButton
            sx={{ mr: 1, color: 'error.light' }}
            component="span"
            onClick={(e) => {
              e.stopPropagation();
              onDelete?.();
            }}
            title="Remove from itinerary"
          >
            <DeleteOutlineIcon fontSize="small" />
          </IconButton>
        )}
      </CardActionArea>
    </Card>
  );
}