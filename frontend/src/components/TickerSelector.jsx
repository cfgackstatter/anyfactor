import React, { useState } from 'react';
import { TextField, Chip, Box, Stack } from '@mui/material';
import { MAX_TICKERS } from '../constants';

const TICKER_RE = /^[A-Z0-9.-]{1,10}$/;

const TickerSelector = ({ tickers, setTickers }) => {
  const [input, setInput] = useState('');
  const atLimit = tickers.length >= MAX_TICKERS;

  const handleKeyDown = (e) => {
    if (e.key !== 'Enter' || !input.trim() || atLimit) return;
    e.preventDefault();
    const ticker = input.trim().toUpperCase();
    if (!TICKER_RE.test(ticker)) return;
    if (!tickers.includes(ticker)) setTickers([...tickers, ticker]);
    setInput('');
  };

  return (
    <Box>
      <TextField
        fullWidth
        label="Tickers"
        placeholder="AAPL ↵"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={atLimit}
        helperText={atLimit ? `Max ${MAX_TICKERS}` : `${tickers.length}/${MAX_TICKERS}`}
      />
      {tickers.length > 0 && (
        <Stack direction="row" flexWrap="wrap" useFlexGap spacing={0.5} sx={{ mt: 0.75 }}>
          {tickers.map((ticker) => (
            <Chip
              key={ticker}
              label={ticker}
              onDelete={() => setTickers(tickers.filter((t) => t !== ticker))}
              variant="outlined"
            />
          ))}
        </Stack>
      )}
    </Box>
  );
};

export default TickerSelector;
