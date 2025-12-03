import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Link,
  Alert,
} from '@mui/material';

const ResultsDisplay = ({ results }) => {
  if (!results || results.length === 0) {
    return null;
  }

  return (
    <TableContainer component={Paper} sx={{ mt: 3 }}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell><strong>Ticker</strong></TableCell>
            <TableCell><strong>Feature</strong></TableCell>
            <TableCell align="right"><strong>Value</strong></TableCell>
            <TableCell><strong>Form</strong></TableCell>
            <TableCell><strong>Filing Date</strong></TableCell>
            <TableCell><strong>Source</strong></TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {results.map((result, idx) => (
            <TableRow key={idx}>
              <TableCell>{result.ticker}</TableCell>
              <TableCell>{result.feature || '-'}</TableCell>
              <TableCell align="right">
                {result.error ? (
                  <Alert severity="error" sx={{ py: 0 }}>{result.error}</Alert>
                ) : result.value !== null ? (
                  result.value.toLocaleString()
                ) : (
                  'Not found'
                )}
              </TableCell>
              <TableCell>{result.form_type || '-'}</TableCell>
              <TableCell>{result.filing_date || '-'}</TableCell>
              <TableCell>
                {result.filing_url && (
                  <Link href={result.filing_url} target="_blank" rel="noopener">
                    View Filing
                  </Link>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default ResultsDisplay;
