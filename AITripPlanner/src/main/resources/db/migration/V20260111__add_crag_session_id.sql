-- Migration: Add crag_session_id to itineraries table
-- Date: 2026-01-11
-- Purpose: Link itinerary to CRAG session for conversation recovery

-- Add the column (nullable, as non-CRAG itineraries won't have session)
ALTER TABLE itineraries
ADD COLUMN IF NOT EXISTS crag_session_id VARCHAR(64);

-- Add unique constraint (allows NULL, but each session can only link to one itinerary)
ALTER TABLE itineraries
ADD CONSTRAINT uk_itineraries_crag_session_id UNIQUE (crag_session_id);

-- Add index for faster lookups (optional, unique constraint already creates an index)
-- CREATE INDEX IF NOT EXISTS idx_itineraries_crag_session_id ON itineraries(crag_session_id);
