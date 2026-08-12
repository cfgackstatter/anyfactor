const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
const API_KEY = process.env.REACT_APP_EXTRACT_API_KEY || '';

async function readErrorMessage(response) {
  try {
    const body = await response.json();
    if (body?.error) return body.error;
  } catch {
    /* ignore */
  }
  if (response.status === 401) return 'Unauthorized — check REACT_APP_EXTRACT_API_KEY';
  if (response.status === 429) return 'Rate limit exceeded — try again later';
  return 'Failed to extract feature';
}

function handleStreamMessage(message, onProgress) {
  if (message.type === 'progress') {
    onProgress?.(message);
    return null;
  }
  if (message.type === 'complete') return message;
  if (message.type === 'error') {
    throw new Error(message.error || 'Extraction failed');
  }
  return null;
}

export async function extractFeature(tickers, feature, limit = 5, onProgress) {
  const headers = { 'Content-Type': 'application/json' };
  if (API_KEY) headers['X-API-Key'] = API_KEY;

  const response = await fetch(`${API_BASE_URL}/api/extract`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ tickers, feature, limit }),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      let message;
      try {
        message = JSON.parse(trimmed);
      } catch (err) {
        console.error('Failed to parse message:', err);
        continue;
      }
      const doneMsg = handleStreamMessage(message, onProgress);
      if (doneMsg) return doneMsg;
    }
  }

  const leftover = buffer.trim();
  if (leftover) {
    try {
      const doneMsg = handleStreamMessage(JSON.parse(leftover), onProgress);
      if (doneMsg) return doneMsg;
    } catch (err) {
      if (err instanceof SyntaxError) {
        console.error('Failed to parse final buffer:', err);
      } else {
        throw err;
      }
    }
  }

  throw new Error('Incomplete response from server');
}
