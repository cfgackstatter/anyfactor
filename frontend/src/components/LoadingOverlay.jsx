import React from 'react';
import { Backdrop, CircularProgress, Typography, Box } from '@mui/material';

const LoadingOverlay = ({ open, message }) => (
  <Backdrop
    open={open}
    sx={{
      zIndex: (theme) => theme.zIndex.modal + 1,
      backgroundColor: 'rgba(11, 31, 42, 0.45)',
      backdropFilter: 'blur(2px)',
    }}
  >
    <Box
      sx={{
        bgcolor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
        px: 2.5,
        py: 2,
        minWidth: 240,
        textAlign: 'center',
      }}
    >
      <CircularProgress size={22} thickness={4} color="primary" />
      <Typography variant="body2" sx={{ mt: 1.25, color: 'text.primary' }}>
        {message || 'Working…'}
      </Typography>
    </Box>
  </Backdrop>
);

export default LoadingOverlay;
