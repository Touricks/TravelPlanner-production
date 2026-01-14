import React from 'react';
import {
  Drawer,
  Box,
  Typography,
  List,
  ListItem,
  ListItemButton,
  Chip,
  IconButton,
  Divider,
  CircularProgress,
  Alert
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import HistoryIcon from '@mui/icons-material/History';

function PlanHistoryDrawer({ open, onClose, planHistory, loading, error, onSelectPlan }) {
  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          width: { xs: '100%', sm: 420 },
          bgcolor: '#fafafa'
        }
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          p: 2,
          bgcolor: 'white',
          borderBottom: '1px solid #e0e0e0',
          position: 'sticky',
          top: 0,
          zIndex: 1
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <HistoryIcon color="primary" />
          <Typography variant="h6" fontWeight="bold">
            Plan History
          </Typography>
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </Box>

      {/* Content */}
      <Box sx={{ p: 2 }}>
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {!loading && !error && planHistory && planHistory.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <HistoryIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
            <Typography color="text.secondary">
              No plan history yet
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Generate your first plan to see it here
            </Typography>
          </Box>
        )}

        {!loading && !error && planHistory && planHistory.length > 0 && (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              {planHistory.length} {planHistory.length === 1 ? 'plan' : 'plans'} generated
            </Typography>
            <List sx={{ p: 0 }}>
              {planHistory.map((plan, index) => {
                const dayCount = plan.days ? plan.days.length : 0;

                return (
                  <React.Fragment key={plan.planId || index}>
                    <ListItem
                      disablePadding
                      sx={{
                        mb: 1.5,
                        bgcolor: 'white',
                        borderRadius: 2,
                        overflow: 'hidden',
                        border: '1px solid #e0e0e0',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
                        transition: 'all 0.25s ease',
                        '&:hover': {
                          boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
                          transform: 'translateY(-2px)',
                          borderColor: '#c0c0c0'
                        }
                      }}
                    >
                      <ListItemButton
                        onClick={() => onSelectPlan(plan)}
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          p: 2.5,
                          transition: 'background-color 0.2s ease',
                          '&:hover': {
                            bgcolor: 'rgba(0, 0, 0, 0.02)'
                          }
                        }}
                      >
                        <Typography variant="subtitle2" fontWeight="bold">
                          Plan #{planHistory.length - index}
                        </Typography>
                        <Chip
                          label={`${dayCount} ${dayCount === 1 ? 'day' : 'days'}`}
                          size="small"
                          variant="outlined"
                        />
                      </ListItemButton>
                    </ListItem>
                    {index < planHistory.length - 1 && <Divider sx={{ my: 1 }} />}
                  </React.Fragment>
                );
              })}
            </List>
          </>
        )}
      </Box>
    </Drawer>
  );
}

export default PlanHistoryDrawer;