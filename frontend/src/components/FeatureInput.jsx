import React from 'react';
import { TextField } from '@mui/material';

const FeatureInput = ({ value, onChange }) => {
  return (
    <TextField
      fullWidth
      label="Feature to Extract"
      placeholder="e.g., book value, total revenue, number of employees"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      variant="outlined"
      margin="normal"
    />
  );
};

export default FeatureInput;
