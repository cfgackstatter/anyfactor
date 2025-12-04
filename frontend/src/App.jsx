import React, { useState } from 'react';
import {
  Container,
  Typography,
  Button,
  Box,
  Paper,
  AppBar,
  Toolbar,
  TextField,
} from '@mui/material';
import FeatureInput from './components/FeatureInput';
import TickerSelector from './components/TickerSelector';
import ResultsDisplay from './components/ResultsDisplay';
import LoadingOverlay from './components/LoadingOverlay';
import { extractFeature } from './api';

function App() {
  const [feature, setFeature] = useState('');
  const [tickers, setTickers] = useState([]);
  const [numFilings, setNumFilings] = useState(5);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleExtract = async () => {
    if (!feature || tickers.length === 0) {
      setError('Please enter a feature and at least one ticker');
      return;
    }

    setLoading(true);
    setError('');
    setResults([]);

    try {
      const data = await extractFeature(tickers, feature, numFilings);
      setResults(data.results);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <AppBar position="static" sx={{ backgroundColor: '#1E3A8A' }}>
        <Toolbar>
          <Typography variant="h6" component="div">
            AnyFactor - AI SEC Data Extraction
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom>
            Extract Financial Features
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            Use AI to extract any numerical feature from SEC 10-K and 10-Q filings
          </Typography>

          <Box sx={{ mt: 3 }}>
            <FeatureInput value={feature} onChange={setFeature} />
            <TickerSelector tickers={tickers} setTickers={setTickers} />
            
            <TextField
              type="number"
              label="Number of Filings"
              value={numFilings}
              onChange={(e) => setNumFilings(Math.max(1, Math.min(20, parseInt(e.target.value) || 5)))}
              inputProps={{ min: 1, max: 20 }}
              helperText="Extract from 1-20 most recent filings per ticker"
              margin="normal"
              sx={{ width: '250px' }}
            />

            {error && (
              <Typography color="error" sx={{ mt: 2 }}>
                {error}
              </Typography>
            )}

            <Button
              variant="contained"
              size="large"
              fullWidth
              onClick={handleExtract}
              disabled={loading}
              sx={{ mt: 3, backgroundColor: '#10B981', '&:hover': { backgroundColor: '#059669' } }}
            >
              Extract Data
            </Button>
          </Box>

          <ResultsDisplay results={results} />
        </Paper>
      </Container>

      <LoadingOverlay open={loading} message="Analyzing SEC filings with AI..." />
    </>
  );
}

export default App;
