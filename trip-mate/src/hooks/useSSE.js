import { useState, useCallback, useRef } from 'react';

/**
 * SSE Hook for streaming progress updates from CRAG API
 *
 * @param {string} url - SSE endpoint URL
 * @returns {Object} { progress, result, error, isStreaming, start, abort }
 */
export default function useSSE(url) {
  const [progress, setProgress] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = useRef(null);

  const abort = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const start = useCallback(async (body) => {
    // Reset state
    setProgress({ stage: 'connecting', message: 'Connecting...', percent: 0 });
    setResult(null);
    setError(null);
    setIsStreaming(true);

    // Create abort controller for cancellation
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      let currentEvent = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          // Parse event type
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim();
            continue;
          }

          // Parse data
          if (line.startsWith('data:')) {
            try {
              const data = JSON.parse(line.slice(5).trim());

              // Handle based on event type or data.stage
              const eventType = currentEvent || data.stage;

              if (eventType === 'complete') {
                // Complete event - data is the actual response
                setResult(data);
                setProgress({ stage: 'complete', message: 'Complete', percent: 100 });
              } else if (eventType === 'error') {
                setError(data.message || 'Unknown error');
              } else if (eventType === 'progress' || data.stage) {
                // Progress event
                setProgress(data);
              }
            } catch (parseErr) {
              console.warn('Failed to parse SSE data:', line, parseErr);
            }
            currentEvent = null; // Reset after processing
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message);
        console.error('SSE error:', err);
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  }, [url]);

  const reset = useCallback(() => {
    setProgress(null);
    setResult(null);
    setError(null);
    setIsStreaming(false);
  }, []);

  return { progress, result, error, isStreaming, start, abort, reset };
}
