const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export const extractFeature = async (tickers, feature, limit = 5, onProgress) => {
  const response = await fetch(`${API_BASE_URL}/api/extract`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ tickers, feature, limit }),
  });

  if (!response.ok) {
    throw new Error('Failed to extract feature');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    const lines = text.split('\n').filter(line => line.trim());

    for (const line of lines) {
      try {
        const message = JSON.parse(line);
        
        if (message.type === 'progress' && onProgress) {
          onProgress(message);
        } else if (message.type === 'complete') {
          return message;
        }
      } catch (e) {
        console.error('Failed to parse message:', e);
      }
    }
  }
};
