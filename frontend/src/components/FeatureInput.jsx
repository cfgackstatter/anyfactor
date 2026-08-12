import React from 'react';
import { TextField } from '@mui/material';

const FeatureInput = ({ value, onChange, onSubmit }) => {
  return (
    <TextField
      fullWidth
      label="Feature"
      placeholder="revenue, book value, AI exposure…"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' && onSubmit) onSubmit();
      }}
    />
  );
};

export default FeatureInput;
