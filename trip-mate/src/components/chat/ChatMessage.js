import React from 'react';
import { Box, Paper, Typography, Avatar } from '@mui/material';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';

export default function ChatMessage({ type, content }) {
  const isUser = type === 'user';

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 2,
        px: 2,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexDirection: isUser ? 'row-reverse' : 'row',
          alignItems: 'flex-start',
          maxWidth: '80%',
          gap: 1,
        }}
      >
        <Avatar
          sx={{
            bgcolor: isUser ? '#95EC69' : 'grey.300',
            width: 36,
            height: 36,
            color: isUser ? '#000' : 'inherit',
          }}
        >
          {isUser ? <PersonIcon /> : <SmartToyIcon />}
        </Avatar>
        <Paper
          elevation={1}
          sx={{
            p: 2,
            bgcolor: isUser ? '#95EC69' : '#F5F5F5',
            color: isUser ? '#000' : 'text.primary',
            borderRadius: 2,
            borderTopRightRadius: isUser ? 0 : 2,
            borderTopLeftRadius: isUser ? 2 : 0,
          }}
        >
          <Typography
            variant="body1"
            sx={{
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
          >
            {content}
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
}
