import React, { useMemo, useState } from 'react';
import {
  AppBar,
  Box,
  Button,
  Container,
  Stack,
  TextField,
  Toolbar,
  Typography,
  Alert,
} from '@mui/material';
import FeatureInput from './components/FeatureInput';
import TickerSelector from './components/TickerSelector';
import ResultsDisplay from './components/ResultsDisplay';
import LoadingOverlay from './components/LoadingOverlay';
import TrendChart from './components/TrendChart';
import { extractFeature } from './api';
import { DEFAULT_FILINGS, MAX_FILINGS, MAX_TICKERS } from './constants';

function groupChartSeries(results) {
  const grouped = new Map();
  for (const result of results) {
    if (result.value == null || result.error || result.value_type === 'score') continue;
    const key = `${result.ticker}-${result.feature}-${result.period_type || 'unknown'}`;
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key).push(result);
  }
  return [...grouped.values()];
}

function progressMessage(tickers, progress) {
  const stage = progress.stage ? ` · ${progress.stage}` : '';
  if (tickers.length > 1) {
    return `${progress.ticker} ${progress.current}/${progress.total}${stage} (${progress.ticker_current}/${progress.ticker_total})`;
  }
  return `${progress.ticker} ${progress.current}/${progress.total}${stage}`;
}

function App() {
  const [feature, setFeature] = useState('');
  const [tickers, setTickers] = useState([]);
  const [numFilings, setNumFilings] = useState(DEFAULT_FILINGS);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [error, setError] = useState('');

  const chartData = useMemo(() => groupChartSeries(results), [results]);
  const canRun = Boolean(feature.trim()) && tickers.length > 0 && !loading;

  const handleExtract = async () => {
    if (!feature || tickers.length === 0) {
      setError('Enter a feature and at least one ticker.');
      return;
    }

    setLoading(true);
    setError('');
    setResults([]);
    setLoadingMessage('Running extraction…');

    try {
      const data = await extractFeature(
        tickers,
        feature,
        numFilings,
        (progress) => setLoadingMessage(progressMessage(tickers, progress)),
      );
      setResults(data.results ?? []);
    } catch (err) {
      setError(err.message || 'Extraction failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', pb: 4 }}>
      <AppBar position="sticky">
        <Toolbar>
          <Stack direction="row" spacing={1.5} alignItems="baseline" sx={{ flexGrow: 1 }}>
            <Typography
              component="div"
              sx={{
                fontFamily: '"IBM Plex Mono", monospace',
                fontWeight: 600,
                letterSpacing: '0.08em',
                fontSize: '0.9rem',
              }}
            >
              ANYFACTOR
            </Typography>
            <Typography variant="caption" sx={{ display: { xs: 'none', sm: 'block' } }}>
              SEC feature extraction for quant research
            </Typography>
          </Stack>
          <Typography variant="caption" className="mono">
            10-K / 10-Q · XBRL + LLM
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 2.5, px: { xs: 1.5, sm: 2 } }}>
        <Box
          className="af-panel"
          sx={{
            bgcolor: 'background.paper',
            border: '1px solid',
            borderColor: 'divider',
            p: 1.5,
          }}
        >
          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={1}
            alignItems={{ md: 'flex-start' }}
          >
            <Box sx={{ flex: 2, minWidth: 0 }}>
              <FeatureInput value={feature} onChange={setFeature} onSubmit={handleExtract} />
            </Box>
            <Box sx={{ flex: 2, minWidth: 0 }}>
              <TickerSelector tickers={tickers} setTickers={setTickers} />
            </Box>
            <TextField
              type="number"
              label="Filings"
              value={numFilings}
              onChange={(e) =>
                setNumFilings(
                  Math.max(1, Math.min(MAX_FILINGS, parseInt(e.target.value, 10) || DEFAULT_FILINGS)),
                )
              }
              inputProps={{ min: 1, max: MAX_FILINGS }}
              sx={{ width: { xs: '100%', md: 96 } }}
              helperText={`1–${MAX_FILINGS}`}
            />
            <Button
              variant="contained"
              onClick={handleExtract}
              disabled={!canRun}
              sx={{ mt: { md: 0.25 }, height: 32, alignSelf: { md: 'flex-start' }, minWidth: 108 }}
            >
              Extract
            </Button>
          </Stack>

          <Typography variant="caption" sx={{ display: 'block', mt: 1 }}>
            Tip: standard metrics (revenue, book value, R&amp;D, employees) resolve via XBRL when available.
            Max {MAX_TICKERS} tickers.
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mt: 1 }}>
              {error}
            </Alert>
          )}
        </Box>

        {results.length > 0 && (
          <Box className="af-results" sx={{ mt: 1.5 }}>
            <Stack
              direction="row"
              justifyContent="space-between"
              alignItems="center"
              sx={{ mb: 0.75 }}
            >
              <Typography variant="h2">Results</Typography>
              <Typography variant="caption" className="mono">
                {results.length} row{results.length === 1 ? '' : 's'}
              </Typography>
            </Stack>
            <ResultsDisplay results={results} />
          </Box>
        )}

        {chartData.map((data, idx) => (
          <TrendChart
            key={`${data[0]?.ticker}-${data[0]?.feature}-${data[0]?.period_type}-${idx}`}
            data={data}
          />
        ))}
      </Container>

      <LoadingOverlay open={loading} message={loadingMessage} />
    </Box>
  );
}

export default App;
