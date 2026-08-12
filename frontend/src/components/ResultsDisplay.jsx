import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Link,
  Chip,
  IconButton,
  Collapse,
  Box,
  Typography,
  Stack,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

function formatCompactNumber(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return String(value);
  const abs = Math.abs(n);
  if (abs >= 1e12) return `${(n / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `${(n / 1e3).toFixed(2)}K`;
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

const ResultsDisplay = ({ results }) => {
  const [expandedRows, setExpandedRows] = useState(new Set());

  if (!results?.length) return null;

  const toggleRow = (idx) => {
    const next = new Set(expandedRows);
    if (next.has(idx)) next.delete(idx);
    else next.add(idx);
    setExpandedRows(next);
  };

  const formatValue = (result) => {
    if (result.error) {
      return (
        <Typography variant="caption" color="error.main">
          {result.error}
        </Typography>
      );
    }
    if (result.value == null) {
      return (
        <Typography variant="caption" color="text.secondary">
          —
        </Typography>
      );
    }
    if (result.value_type === 'score') {
      return <Chip label={`${result.value}/10`} size="small" />;
    }
    const formatted = formatCompactNumber(result.value);
    return result.unit ? `${formatted} ${result.unit}` : formatted;
  };

  const hasDetails = (result) =>
    Boolean(result.evidence || result.quote || result.label_matched || result.period_end || result.source);

  return (
    <TableContainer
      sx={{
        bgcolor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell sx={{ width: 36 }} />
            <TableCell>Ticker</TableCell>
            <TableCell>Feature</TableCell>
            <TableCell align="right">Value</TableCell>
            <TableCell>Period</TableCell>
            <TableCell>Form</TableCell>
            <TableCell>Filed</TableCell>
            <TableCell>Method</TableCell>
            <TableCell>Link</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {results.map((result, idx) => (
            <React.Fragment key={idx}>
              <TableRow hover sx={{ '&:last-child td': { borderBottom: hasDetails(result) && expandedRows.has(idx) ? undefined : 0 } }}>
                <TableCell sx={{ width: 36, px: 0.5 }}>
                  {hasDetails(result) && (
                    <IconButton size="small" onClick={() => toggleRow(idx)} sx={{ p: 0.25 }}>
                      <ExpandMoreIcon
                        sx={{
                          fontSize: 18,
                          transform: expandedRows.has(idx) ? 'rotate(180deg)' : 'none',
                          transition: 'transform 160ms ease',
                        }}
                      />
                    </IconButton>
                  )}
                </TableCell>
                <TableCell sx={{ fontWeight: 600 }}>{result.ticker}</TableCell>
                <TableCell sx={{ fontFamily: '"IBM Plex Sans", sans-serif' }}>
                  {result.feature || '—'}
                </TableCell>
                <TableCell align="right">{formatValue(result)}</TableCell>
                <TableCell>{result.period_type || '—'}</TableCell>
                <TableCell>{result.form_type || '—'}</TableCell>
                <TableCell>{result.filing_date || '—'}</TableCell>
                <TableCell>
                  {result.source ? (
                    <Chip
                      label={result.source.toUpperCase()}
                      variant={result.source === 'xbrl' ? 'filled' : 'outlined'}
                      color={result.source === 'xbrl' ? 'success' : 'default'}
                    />
                  ) : (
                    '—'
                  )}
                </TableCell>
                <TableCell>
                  {result.filing_url ? (
                    <Link href={result.filing_url} target="_blank" rel="noopener noreferrer">
                      SEC
                    </Link>
                  ) : (
                    '—'
                  )}
                </TableCell>
              </TableRow>
              {hasDetails(result) && (
                <TableRow>
                  <TableCell colSpan={9} sx={{ py: 0, borderBottomColor: 'divider' }}>
                    <Collapse in={expandedRows.has(idx)} timeout={180} unmountOnExit>
                      <Box sx={{ px: 1.5, py: 1, bgcolor: '#F3F6F8' }}>
                        <Stack spacing={0.5}>
                          {result.label_matched && (
                            <Typography variant="caption">
                              <strong>Label</strong> · {result.label_matched}
                            </Typography>
                          )}
                          {result.period_end && (
                            <Typography variant="caption">
                              <strong>Period end</strong> · {result.period_end}
                            </Typography>
                          )}
                          {result.confidence != null && (
                            <Typography variant="caption">
                              <strong>Confidence</strong> · {(Number(result.confidence) * 100).toFixed(0)}%
                            </Typography>
                          )}
                          {result.evidence && (
                            <Typography variant="caption">
                              <strong>Evidence</strong> · {result.evidence}
                            </Typography>
                          )}
                          {result.quote && (
                            <Typography variant="caption" sx={{ fontStyle: 'italic' }}>
                              “{result.quote}”
                            </Typography>
                          )}
                        </Stack>
                      </Box>
                    </Collapse>
                  </TableCell>
                </TableRow>
              )}
            </React.Fragment>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default ResultsDisplay;
