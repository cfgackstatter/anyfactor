import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export const extractFeature = async (tickers, feature, limit = 5) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/extract`, {
      tickers,
      feature,
      limit
    });
    return response.data;
  } catch (error) {
    throw error.response?.data?.error || 'Failed to extract feature';
  }
};
