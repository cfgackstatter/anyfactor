import React from 'react';
import { Line } from 'react-chartjs-2';
import { Box, Typography, Stack } from '@mui/material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler);

function formatCompact(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return String(value);
  const abs = Math.abs(n);
  if (abs >= 1e12) return `${(n / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `${(n / 1e3).toFixed(2)}K`;
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

const TrendChart = ({ data }) => {
  if (!data || data.length < 2) return null;

  const numericData = data.filter((d) => d.value_type !== 'score');
  if (numericData.length < 2) return null;

  const sortedData = [...numericData].sort(
    (a, b) => new Date(a.filing_date) - new Date(b.filing_date),
  );

  const dates = sortedData.map((d) => d.filing_date);
  const values = sortedData.map((d) => d.value ?? 0);
  const latestValue = values[values.length - 1];
  const oldestValue = values[0];
  const growthRate =
    oldestValue === 0 ? null : ((latestValue - oldestValue) / Math.abs(oldestValue)) * 100;
  const avgValue = values.reduce((a, b) => a + b, 0) / values.length;

  const periodLabel = data[0].period_type === 'annual' ? 'Annual' : 'Quarterly';
  const lineColor =
    growthRate == null ? '#5B6B75' : growthRate > 5 ? '#1B7F5A' : growthRate < -5 ? '#B42318' : '#5B6B75';
  const growthLabel =
    growthRate == null ? 'n/a' : `${growthRate >= 0 ? '+' : ''}${growthRate.toFixed(1)}%`;

  const chartData = {
    labels: dates,
    datasets: [
      {
        data: values,
        borderColor: lineColor,
        backgroundColor: `${lineColor}14`,
        borderWidth: 1.5,
        pointRadius: 2.5,
        pointHoverRadius: 4,
        tension: 0.15,
        fill: true,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 450 },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => formatCompact(ctx.parsed.y),
        },
      },
    },
    scales: {
      x: {
        grid: { color: 'rgba(11,31,42,0.06)' },
        ticks: { font: { size: 10, family: 'IBM Plex Mono' }, color: '#5B6B75', maxRotation: 0 },
      },
      y: {
        beginAtZero: false,
        grid: { color: 'rgba(11,31,42,0.06)' },
        ticks: {
          font: { size: 10, family: 'IBM Plex Mono' },
          color: '#5B6B75',
          callback: (value) => formatCompact(value),
        },
      },
    },
  };

  return (
    <Box
      className="af-results"
      sx={{
        mt: 1.5,
        bgcolor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
        p: 1.25,
      }}
    >
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
        <Typography variant="h2">
          {data[0].ticker} · {data[0].feature} · {periodLabel}
        </Typography>
        <Typography
          variant="caption"
          className="mono"
          sx={{ color: lineColor, fontWeight: 600 }}
        >
          {growthLabel}
        </Typography>
      </Stack>

      <Box sx={{ height: 180 }}>
        <Line data={chartData} options={options} />
      </Box>

      <Stack direction="row" spacing={3} sx={{ mt: 1 }}>
        {[
          ['Latest', formatCompact(latestValue)],
          ['Avg', formatCompact(avgValue)],
          ['Δ', growthLabel],
        ].map(([label, value]) => (
          <Box key={label}>
            <Typography variant="caption" display="block">
              {label}
            </Typography>
            <Typography variant="body2" className="mono" sx={{ color: 'text.primary', fontWeight: 600 }}>
              {value}
            </Typography>
          </Box>
        ))}
      </Stack>
    </Box>
  );
};

export default TrendChart;
