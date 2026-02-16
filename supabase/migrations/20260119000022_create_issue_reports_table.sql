-- Migration: Create issue_reports table
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Issue Reports Table
-- ============================================
CREATE TABLE IF NOT EXISTS issue_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID NOT NULL REFERENCES space_artwork_assignments(id) ON DELETE CASCADE,
    reported_by UUID NOT NULL,
    issue_type TEXT NOT NULL 
        CHECK (issue_type IN ('damage', 'missing', 'quality', 'other')),
    description TEXT NOT NULL,
    photo_urls JSONB,
    status TEXT NOT NULL DEFAULT 'open' 
        CHECK (status IN ('open', 'investigating', 'resolved', 'rejected')),
    resolution_notes TEXT,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE issue_reports ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Issue Reports
-- Corporates can view and create reports for their space assignments
CREATE POLICY "Corporates can manage own space issue reports"
    ON issue_reports FOR ALL
    USING (
        auth.uid() = reported_by
        AND EXISTS (
            SELECT 1 FROM space_artwork_assignments
            JOIN corporate_spaces ON corporate_spaces.id = space_artwork_assignments.space_id
            WHERE space_artwork_assignments.id = issue_reports.assignment_id
            AND corporate_spaces.corporate_id = auth.uid()
        )
    );

-- Artists can view reports for their artworks
CREATE POLICY "Artists can view artwork issue reports"
    ON issue_reports FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM space_artwork_assignments
            JOIN artworks ON artworks.id = space_artwork_assignments.artwork_id
            WHERE space_artwork_assignments.id = issue_reports.assignment_id
            AND artworks.artist_id = auth.uid()
        )
    );

-- Service role can do everything
CREATE POLICY "Service role can manage issue reports"
    ON issue_reports FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_issue_reports_assignment_id ON issue_reports(assignment_id);
CREATE INDEX IF NOT EXISTS idx_issue_reports_status ON issue_reports(status);

-- Trigger to auto-update updated_at
CREATE TRIGGER update_issue_reports_updated_at
    BEFORE UPDATE ON issue_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
