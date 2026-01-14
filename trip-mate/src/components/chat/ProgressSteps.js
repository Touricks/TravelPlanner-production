import React from 'react';
import { Box, Stepper, Step, StepLabel, LinearProgress, Typography, Paper, Fade } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import VerifiedIcon from '@mui/icons-material/Verified';
import ExploreIcon from '@mui/icons-material/Explore';

const STAGES = [
  { key: 'collector', label: 'Understanding', icon: <AutoAwesomeIcon /> },
  { key: 'validator', label: 'Validating', icon: <VerifiedIcon /> },
  { key: 'search', label: 'Searching', icon: <SearchIcon /> },
  { key: 'grading', label: 'Evaluating', icon: <CheckCircleIcon /> },
  { key: 'generator', label: 'Generating', icon: <ExploreIcon /> },
];

/**
 * Progress steps component for SSE streaming feedback
 *
 * @param {Object} progress - Current progress state { stage, message, percent }
 */
export default function ProgressSteps({ progress }) {
  if (!progress || progress.stage === 'connecting') {
    return null;
  }

  // Find current stage index
  const currentIndex = STAGES.findIndex(s => s.key === progress.stage);
  const isComplete = progress.stage === 'complete';

  return (
    <Fade in>
      <Paper
        elevation={0}
        sx={{
          mx: 2,
          mb: 2,
          p: 2,
          bgcolor: 'background.paper',
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 2,
        }}
      >
        {/* Progress Bar */}
        <LinearProgress
          variant="determinate"
          value={progress.percent || 0}
          sx={{
            mb: 2,
            height: 6,
            borderRadius: 3,
            bgcolor: 'grey.200',
            '& .MuiLinearProgress-bar': {
              borderRadius: 3,
              bgcolor: isComplete ? 'success.main' : 'primary.main',
            },
          }}
        />

        {/* Status Message */}
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ mb: 2, minHeight: 20 }}
        >
          {progress.message || 'Processing...'}
        </Typography>

        {/* Step Indicators */}
        <Stepper
          activeStep={isComplete ? STAGES.length : currentIndex}
          alternativeLabel
          sx={{
            '& .MuiStepLabel-label': {
              fontSize: '0.75rem',
              mt: 0.5,
            },
          }}
        >
          {STAGES.map((stage, index) => (
            <Step
              key={stage.key}
              completed={isComplete || index < currentIndex}
            >
              <StepLabel
                StepIconComponent={() => (
                  <Box
                    sx={{
                      width: 24,
                      height: 24,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      bgcolor: (isComplete || index < currentIndex)
                        ? 'success.main'
                        : index === currentIndex
                          ? 'primary.main'
                          : 'grey.300',
                      color: (isComplete || index <= currentIndex) ? 'white' : 'grey.600',
                      fontSize: '0.875rem',
                    }}
                  >
                    {(isComplete || index < currentIndex) ? (
                      <CheckCircleIcon sx={{ fontSize: 16 }} />
                    ) : (
                      index + 1
                    )}
                  </Box>
                )}
              >
                {stage.label}
              </StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>
    </Fade>
  );
}
