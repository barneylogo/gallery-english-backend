-- Migration: Create corporate_favorites table
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Corporate Favorites Table
-- ============================================
CREATE TABLE IF NOT EXISTS corporate_favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    corporate_id UUID NOT NULL REFERENCES corporates(id) ON DELETE CASCADE,
    artwork_id UUID NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    space_id UUID REFERENCES corporate_spaces(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(corporate_id, artwork_id, space_id)
);

-- Enable Row Level Security
ALTER TABLE corporate_favorites ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Corporate Favorites
-- Corporates can view and manage their own favorites
CREATE POLICY "Corporates can manage own favorites"
    ON corporate_favorites FOR ALL
    USING (auth.uid() = corporate_id)
    WITH CHECK (auth.uid() = corporate_id);

-- Service role can do everything
CREATE POLICY "Service role can manage corporate favorites"
    ON corporate_favorites FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_corporate_favorites_corporate_id ON corporate_favorites(corporate_id);
CREATE INDEX IF NOT EXISTS idx_corporate_favorites_artwork_id ON corporate_favorites(artwork_id);
CREATE INDEX IF NOT EXISTS idx_corporate_favorites_space_id ON corporate_favorites(space_id);

COMMIT;
