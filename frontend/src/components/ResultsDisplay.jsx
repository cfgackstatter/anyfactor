import React, { useState } from 'react';
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
  Chip,
  IconButton,
  Collapse,
  Box,
  Typography,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

const ResultsDisplay = ({ results }) => {
  const [expandedRows, setExpandedRows] = useState(new Set());

  if (!results || results.length === 0) {
    return null;
  }

  const toggleRow = (idx) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(idx)) {
      newExpanded.delete(idx);
    } else {
      newExpanded.add(idx);
    }
    setExpandedRows(newExpanded);
  };

  const formatValue = (result) => {
    if (result.error) {
      return <Alert severity="error" sx={{ py: 0 }}>{result.error}</Alert>;
    }
    
    if (result.value === null) {
      return 'Not found';
    }
    
    if (result.value_type === 'score') {
      const score = result.value;
      const color = score >= 7 ? 'success' : score >= 4 ? 'warning' : 'default';
      return <Chip label={`${score}/10`} color={color} size="small" />;
    }
    
    return result.value.toLocaleString();
  };

  return (
    <TableContainer component={Paper} sx={{ mt: 3 }}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell />
            <TableCell><strong>Ticker</strong></TableCell>
            <TableCell><strong>Feature</strong></TableCell>
            <TableCell align="right"><strong>Value</strong></TableCell>
            <TableCell><strong>Period</strong></TableCell>
            <TableCell><strong>Form</strong></TableCell>
            <TableCell><strong>Filing Date</strong></TableCell>
            <TableCell><strong>Source</strong></TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {results.map((result, idx) => (
            <React.Fragment key={idx}>
              <TableRow>
                <TableCell>
                  {result.evidence && (
                    <IconButton size="small" onClick={() => toggleRow(idx)}>
                      <ExpandMoreIcon 
                        sx={{ 
                          transform: expandedRows.has(idx) ? 'rotate(180deg)' : 'rotate(0deg)',
                          transition: '0.3s'
                        }}
                      />
                    </IconButton>
                  )}
                </TableCell>
                <TableCell>{result.ticker}</TableCell>
                <TableCell>{result.feature || '-'}</TableCell>
                <TableCell align="right">{formatValue(result)}</TableCell>
                <TableCell>{result.period_type || '-'}</TableCell>
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
              {result.evidence && (
                <TableRow>
                  <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={8}>
                    <Collapse in={expandedRows.has(idx)} timeout="auto" unmountOnExit>
                      <Box sx={{ margin: 1, p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Evidence:
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {result.evidence}
                        </Typography>
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
