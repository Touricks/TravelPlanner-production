import axios from 'axios';

// CRAG API Base URL
const CRAG_API_BASE = process.env.REACT_APP_CRAG_API_BASE || 'http://localhost:8000/api/v1';

/**
 * Get SSE streaming URL for chat
 * @returns {string} SSE endpoint URL
 */
export const getSSEChatUrl = () => `${CRAG_API_BASE}/chat/stream`;

// Create axios instance for CRAG API
const cragApi = axios.create({
  baseURL: CRAG_API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Send a chat message to CRAG API
 * @param {string|null} sessionId - Session ID (null for new session)
 * @param {string} message - User message (empty string for cold start)
 * @returns {Promise<ChatResponse>}
 */
export const sendChatMessage = async (sessionId, message) => {
  const response = await cragApi.post('/chat', {
    session_id: sessionId,
    message: message,
  });
  return response.data;
};

/**
 * Save session plan to Java backend
 * @param {string} sessionId - Session ID
 * @param {string} token - JWT token for Java API
 * @returns {Promise<SaveResponse>}
 */
export const saveSession = async (sessionId, token) => {
  const response = await cragApi.post(
    `/session/${sessionId}/save`,
    {},
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
  return response.data;
};

/**
 * Recover session state (fast mode - no LLM call)
 * @param {string} sessionId - Session ID to recover
 * @returns {Promise<ChatResponse>}
 */
export const recoverSession = async (sessionId) => {
  return sendChatMessage(sessionId, '');
};

// Java API Base URL
const JAVA_API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8080/api';

/**
 * Get itinerary ID by CRAG session ID (from Java backend)
 * Used for "Abandon" feature to navigate back to saved plan
 * @param {string} sessionId - CRAG session ID
 * @returns {Promise<{itinerary_id: string}|null>}
 */
export const getItineraryBySession = async (sessionId) => {
  try {
    const response = await axios.get(`${JAVA_API_BASE}/itineraries/by-session/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to get itinerary by session:', error);
    return null;
  }
};

export default cragApi;
