-- Migration: Update artists table with additional fields
-- Created: 2026-01-19
-- Description: Adds education, exhibitions, awards, website, instagram fields to artists table
BEGIN;
-- Add new columns to artists table
ALTER TABLE artists
ADD COLUMN IF NOT EXISTS education TEXT,
    ADD COLUMN IF NOT EXISTS exhibitions JSONB,
    ADD COLUMN IF NOT EXISTS awards JSONB,
    ADD COLUMN IF NOT EXISTS website TEXT,
    ADD COLUMN IF NOT EXISTS instagram TEXT;
-- Add index for created_at if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_artists_created_at ON artists(created_at);
COMMIT;