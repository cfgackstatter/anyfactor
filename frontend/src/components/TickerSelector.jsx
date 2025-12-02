import React from 'react';
import { TextField, Chip, Box } from '@mui/material';

const TickerSelector = ({ tickers, setTickers }) => {
  const [input, setInput] = React.useState('');

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && input.trim()) {
      e.preventDefault();
      const newTicker = input.trim().toUpperCase();
      if (!tickers.includes(newTicker)) {
        setTickers([...tickers, newTicker]);
      }
      setInput('');
    }
  };

  const handleDelete = (tickerToDelete) => {
    setTickers(tickers.filter((t) => t !== tickerToDelete));
  };

  return (
    <Box>
      <TextField
        fullWidth
        label="Add Tickers"
        placeholder="Type ticker and press Enter (e.g., AAPL)"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        variant="outlined"
        margin="normal"
      />
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
        {tickers.map((ticker) => (
          <Chip
            key={ticker}
            label={ticker}
            onDelete={() => handleDelete(ticker)}
            color="primary"
          />
        ))}
      </Box>
    </Box>
  );
};

export default TickerSelector;
