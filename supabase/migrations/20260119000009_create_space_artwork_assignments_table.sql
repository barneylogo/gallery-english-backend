-- Migration: Create space_artwork_assignments table
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Space Artwork Assignments Table
-- ============================================
CREATE TABLE IF NOT EXISTS space_artwork_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    space_id UUID NOT NULL REFERENCES corporate_spaces(id) ON DELETE CASCADE,
    artwork_id UUID NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'approved', 'displaying', 'returned', 'cancelled')),
    display_start_date DATE,
    display_end_date DATE,
    request_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approval_date TIMESTAMPTZ,
    return_request_date TIMESTAMPTZ,
    return_approval_date TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add unique constraint for active assignments
CREATE UNIQUE INDEX IF NOT EXISTS idx_space_artwork_unique_active 
    ON space_artwork_assignments(space_id, artwork_id, status) 
    WHERE status IN ('pending', 'approved', 'displaying');

-- Enable Row Level Security
ALTER TABLE space_artwork_assignments ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Space Artwork Assignments
-- Corporates can view assignments for their spaces
CREATE POLICY "Corporates can view own space assignments"
    ON space_artwork_assignments FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM corporate_spaces
            WHERE corporate_spaces.id = space_artwork_assignments.space_id
            AND corporate_spaces.corporate_id = auth.uid()
        )
    );

-- Artists can view assignments for their artworks
CREATE POLICY "Artists can view own artwork assignments"
    ON space_artwork_assignments FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM artworks
            WHERE artworks.id = space_artwork_assignments.artwork_id
            AND artworks.artist_id = auth.uid()
        )
    );

-- Corporates can insert assignments for their spaces
CREATE POLICY "Corporates can insert own space assignments"
    ON space_artwork_assignments FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM corporate_spaces
            WHERE corporate_spaces.id = space_artwork_assignments.space_id
            AND corporate_spaces.corporate_id = auth.uid()
        )
    );

-- Service role can do everything
CREATE POLICY "Service role can manage assignments"
    ON space_artwork_assignments FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_space_artwork_space_id ON space_artwork_assignments(space_id);
CREATE INDEX IF NOT EXISTS idx_space_artwork_artwork_id ON space_artwork_assignments(artwork_id);
CREATE INDEX IF NOT EXISTS idx_space_artwork_status ON space_artwork_assignments(status);
CREATE INDEX IF NOT EXISTS idx_space_artwork_displaying ON space_artwork_assignments(space_id, status) 
    WHERE status = 'displaying';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_space_artwork_assignments_updated_at
    BEFORE UPDATE ON space_artwork_assignments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
