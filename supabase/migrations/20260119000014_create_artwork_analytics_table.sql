-- Migration: Create artwork_analytics table
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Artwork Analytics Table
-- ============================================
CREATE TABLE IF NOT EXISTS artwork_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artwork_id UUID NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    views INTEGER DEFAULT 0,
    favorites INTEGER DEFAULT 0,
    inquiries INTEGER DEFAULT 0,
    qr_scans INTEGER DEFAULT 0,
    display_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(artwork_id, date)
);

-- Enable Row Level Security
ALTER TABLE artwork_analytics ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Artwork Analytics
-- Artists can view analytics for their own artworks
CREATE POLICY "Artists can view own artwork analytics"
    ON artwork_analytics FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM artworks
            WHERE artworks.id = artwork_analytics.artwork_id
            AND artworks.artist_id = auth.uid()
        )
    );

-- Service role can do everything
CREATE POLICY "Service role can manage artwork analytics"
    ON artwork_analytics FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_artwork_analytics_artwork_id ON artwork_analytics(artwork_id);
CREATE INDEX IF NOT EXISTS idx_artwork_analytics_date ON artwork_analytics(date);
CREATE INDEX IF NOT EXISTS idx_artwork_analytics_artwork_date ON artwork_analytics(artwork_id, date);

COMMIT;
