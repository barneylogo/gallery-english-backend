-- Migration: Create display_history table
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Display History Table
-- ============================================
CREATE TABLE IF NOT EXISTS display_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    space_id UUID NOT NULL REFERENCES corporate_spaces(id) ON DELETE CASCADE,
    artwork_id UUID NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    assignment_id UUID REFERENCES space_artwork_assignments(id),
    display_start_date DATE NOT NULL,
    display_end_date DATE,
    status TEXT NOT NULL 
        CHECK (status IN ('active', 'completed', 'returned', 'cancelled')),
    qr_code_scans INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    inquiries INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE display_history ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Display History
-- Corporates can view history for their spaces
CREATE POLICY "Corporates can view own space history"
    ON display_history FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM corporate_spaces
            WHERE corporate_spaces.id = display_history.space_id
            AND corporate_spaces.corporate_id = auth.uid()
        )
    );

-- Artists can view history for their artworks
CREATE POLICY "Artists can view own artwork history"
    ON display_history FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM artworks
            WHERE artworks.id = display_history.artwork_id
            AND artworks.artist_id = auth.uid()
        )
    );

-- Service role can do everything
CREATE POLICY "Service role can manage display history"
    ON display_history FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_display_history_space_id ON display_history(space_id);
CREATE INDEX IF NOT EXISTS idx_display_history_artwork_id ON display_history(artwork_id);
CREATE INDEX IF NOT EXISTS idx_display_history_dates ON display_history(display_start_date, display_end_date);
CREATE INDEX IF NOT EXISTS idx_display_history_status ON display_history(status);

-- Trigger to auto-update updated_at
CREATE TRIGGER update_display_history_updated_at
    BEFORE UPDATE ON display_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
