import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, Button, CircularProgress, Alert, Paper } from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import RefreshIcon from '@mui/icons-material/Refresh';
import UndoIcon from '@mui/icons-material/Undo';
import { useNavigate, useSearchParams } from 'react-router-dom';

import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import POICarousel from './POICarousel';
import PlanPreview from './PlanPreview';
import ProgressSteps from './ProgressSteps';
import { sendChatMessage, saveSession, getSSEChatUrl, getItineraryBySession } from '../../api/crag';
import { useAuth } from '../../auth/AuthContext';
import useSSE from '../../hooks/useSSE';

export default function ChatContainer() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const restoreSessionId = searchParams.get('session');
  const { user, token } = useAuth();
  const messagesEndRef = useRef(null);

  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);
  const [planReady, setPlanReady] = useState(false);
  const [recommendedPois, setRecommendedPois] = useState([]);
  const [suggestedPlan, setSuggestedPlan] = useState(null);

  // SSE streaming hook
  const {
    progress: sseProgress,
    result: sseResult,
    error: sseError,
    isStreaming,
    start: startSSE,
    reset: resetSSE,
  } = useSSE(getSSEChatUrl());

  // Auto-scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle SSE result
  useEffect(() => {
    if (sseResult) {
      // Update session ID if new
      if (sseResult.session_id && sseResult.session_id !== sessionId) {
        setSessionId(sseResult.session_id);
      }
      // Add AI response
      setMessages((prev) => [...prev, { type: 'ai', content: sseResult.message }]);
      handleResponse(sseResult);
      setIsLoading(false);
      resetSSE();
    }
  }, [sseResult]);

  // Handle SSE error
  useEffect(() => {
    if (sseError) {
      setError(`Streaming error: ${sseError}`);
      setIsLoading(false);
    }
  }, [sseError]);

  // Initialize session with greeting or restore from URL parameter
  useEffect(() => {
    if (restoreSessionId) {
      restoreFromSession(restoreSessionId);
    } else {
      initSession();
    }
  }, [restoreSessionId]);

  const initSession = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await sendChatMessage(null, '');
      setSessionId(response.session_id);
      setMessages([{ type: 'ai', content: response.message }]);
      handleResponse(response);
    } catch (err) {
      setError('Failed to connect to AI service. Please try again.');
      console.error('Init session error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const restoreFromSession = async (sid) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await sendChatMessage(sid, '');  // Empty message triggers fast restore
      setSessionId(sid);
      setMessages([{ type: 'ai', content: response.message }]);
      handleResponse(response);
    } catch (err) {
      setError('Failed to restore session. Session may have expired.');
      console.error('Restore session error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResponse = (response) => {
    if (response.plan_ready) {
      setPlanReady(true);
    }
    if (response.recommended_pois && response.recommended_pois.length > 0) {
      setRecommendedPois(response.recommended_pois);
    }
    if (response.suggested_plan) {
      setSuggestedPlan(response.suggested_plan);
    }
  };

  const handleSend = async (message) => {
    if (!message.trim() || isLoading) return;

    // Add user message
    setMessages((prev) => [...prev, { type: 'user', content: message }]);
    setIsLoading(true);
    setError(null);

    // Use SSE streaming for progress feedback
    startSSE({
      session_id: sessionId,
      message: message,
    });
  };

  const handleSave = async () => {
    if (!sessionId || !planReady) return;

    setIsSaving(true);
    setError(null);

    try {
      const response = await saveSession(sessionId, token);

      if (response.status === 'success' && response.itinerary_id) {
        // Navigate to the saved itinerary
        navigate(`/plan/${response.itinerary_id}`);
      } else {
        setError('Failed to save plan. Please try again.');
      }
    } catch (err) {
      setError('Failed to save plan. Please try again.');
      console.error('Save error:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setSessionId(null);
    setMessages([]);
    setPlanReady(false);
    setRecommendedPois([]);
    setSuggestedPlan(null);
    setError(null);
    resetSSE();
    initSession();
  };

  // Abandon current plan and return to the last saved plan
  const handleAbandon = async () => {
    if (!restoreSessionId) return;

    setIsLoading(true);
    try {
      const result = await getItineraryBySession(restoreSessionId);
      if (result?.itinerary_id) {
        navigate(`/plan/${result.itinerary_id}`);
      } else {
        setError('Could not find the original plan. Please try "Start Over" instead.');
      }
    } catch (err) {
      setError('Failed to return to the saved plan.');
      console.error('Abandon error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 64px)', // Subtract header height
        bgcolor: 'background.default',
      }}
    >
      {/* Header */}
      <Paper
        elevation={1}
        sx={{
          p: 2,
          borderRadius: 0,
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Typography variant="h6" fontWeight="bold">
          AI Trip Planner
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Tell me about your travel plans and I'll help you create the perfect itinerary
        </Typography>
      </Paper>

      {/* Messages Area */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          py: 2,
        }}
      >
        {error && (
          <Alert severity="error" sx={{ mx: 2, mb: 2 }}>
            {error}
          </Alert>
        )}

        {messages.map((msg, index) => (
          <ChatMessage key={index} type={msg.type} content={msg.content} />
        ))}

        {/* Progress Steps (SSE streaming) */}
        {isLoading && isStreaming && <ProgressSteps progress={sseProgress} />}

        {/* Fallback spinner when not streaming */}
        {isLoading && !isStreaming && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}

        {/* POI Carousel */}
        {recommendedPois.length > 0 && <POICarousel pois={recommendedPois} />}

        {/* Plan Preview */}
        {suggestedPlan && <PlanPreview plan={suggestedPlan} />}

        {/* Action Buttons */}
        {planReady && (
          <Box sx={{ display: 'flex', gap: 2, px: 2, py: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              startIcon={isSaving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
              onClick={handleSave}
              disabled={isSaving || isLoading}
              sx={{ minWidth: 150 }}
            >
              {isSaving ? 'Saving...' : 'Save and View'}
            </Button>
            {restoreSessionId && (
              <Button
                variant="outlined"
                color="warning"
                startIcon={<UndoIcon />}
                onClick={handleAbandon}
                disabled={isSaving || isLoading}
              >
                Abandon this plan
              </Button>
            )}
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleReset}
              disabled={isSaving || isLoading}
            >
              Start Over
            </Button>
          </Box>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </Box>
  );
}
