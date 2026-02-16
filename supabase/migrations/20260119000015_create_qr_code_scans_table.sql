-- Migration: Create qr_code_scans table
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- QR Code Scans Table
-- ============================================
CREATE TABLE IF NOT EXISTS qr_code_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artwork_id UUID NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    space_id UUID REFERENCES corporate_spaces(id),
    scanned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_agent TEXT,
    ip_address INET,
    referrer TEXT
);

-- Enable Row Level Security
ALTER TABLE qr_code_scans ENABLE ROW LEVEL SECURITY;

-- RLS Policies for QR Code Scans
-- Artists can view scans for their own artworks
CREATE POLICY "Artists can view own artwork scans"
    ON qr_code_scans FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM artworks
            WHERE artworks.id = qr_code_scans.artwork_id
            AND artworks.artist_id = auth.uid()
        )
    );

-- Corporates can view scans for their spaces
CREATE POLICY "Corporates can view own space scans"
    ON qr_code_scans FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM corporate_spaces
            WHERE corporate_spaces.id = qr_code_scans.space_id
            AND corporate_spaces.corporate_id = auth.uid()
        )
    );

-- Service role can insert and view all
CREATE POLICY "Service role can manage qr scans"
    ON qr_code_scans FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_qr_scans_artwork_id ON qr_code_scans(artwork_id);
CREATE INDEX IF NOT EXISTS idx_qr_scans_space_id ON qr_code_scans(space_id);
CREATE INDEX IF NOT EXISTS idx_qr_scans_scanned_at ON qr_code_scans(scanned_at);

COMMIT;
