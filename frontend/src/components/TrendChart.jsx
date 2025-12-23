import React from 'react';
import { Line } from 'react-chartjs-2';
import { Box, Typography, Paper, Chip } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const TrendChart = ({ data }) => {
  if (!data || data.length < 2) {
    return null;
  }

  // Filter out score-type data (charts only for numeric)
  const numericData = data.filter(d => d.value_type !== 'score');

  if (numericData.length < 2) {
    return null;
  }

  // Sort by date (oldest first)
  const sortedData = [...numericData].sort((a, b) => 
    new Date(a.filing_date) - new Date(b.filing_date)
  );

  const dates = sortedData.map(d => d.filing_date);
  const values = sortedData.map(d => d.value || 0);
  
  const latestValue = values[values.length - 1];
  const oldestValue = values[0];
  const growthRate = ((latestValue - oldestValue) / oldestValue) * 100;
  const avgValue = values.reduce((a, b) => a + b, 0) / values.length;
  
  const periodType = data[0].period_type || 'unknown';
  const periodLabel = periodType === 'annual' ? 'Annual' : 'Quarterly';

  const getTrendIcon = () => {
    if (growthRate > 5) return <TrendingUpIcon sx={{ color: '#10B981' }} />;
    if (growthRate < -5) return <TrendingDownIcon sx={{ color: '#EF4444' }} />;
    return <TrendingFlatIcon sx={{ color: '#6B7280' }} />;
  };

  const getTrendColor = () => {
    if (growthRate > 5) return '#10B981';
    if (growthRate < -5) return '#EF4444';
    return '#6B7280';
  };

  const chartData = {
    labels: dates,
    datasets: [
      {
        label: data[0].feature || 'Value',
        data: values,
        borderColor: getTrendColor(),
        backgroundColor: getTrendColor() + '20',
        tension: 0.3,
        fill: true,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            return `Value: ${context.parsed.y.toLocaleString()}`;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: false,
        ticks: {
          callback: (value) => value.toLocaleString(),
        },
      },
    },
  };

  return (
    <Paper elevation={2} sx={{ p: 3, mt: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          {data[0].feature} - {data[0].ticker} ({periodLabel})
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip
            icon={getTrendIcon()}
            label={`${growthRate >= 0 ? '+' : ''}${growthRate.toFixed(1)}%`}
            color={growthRate > 5 ? 'success' : growthRate < -5 ? 'error' : 'default'}
          />
        </Box>
      </Box>

      <Box sx={{ height: 300 }}>
        <Line data={chartData} options={options} />
      </Box>

      <Box sx={{ display: 'flex', gap: 3, mt: 2, justifyContent: 'center' }}>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">Latest</Typography>
          <Typography variant="body2" fontWeight="bold">
            {latestValue.toLocaleString()}
          </Typography>
        </Box>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">Average</Typography>
          <Typography variant="body2" fontWeight="bold">
            {avgValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </Typography>
        </Box>
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">Growth</Typography>
          <Typography variant="body2" fontWeight="bold" color={getTrendColor()}>
            {growthRate >= 0 ? '+' : ''}{growthRate.toFixed(1)}%
          </Typography>
        </Box>
      </Box>
    </Paper>
  );
};

export default TrendChart;
