-- Migration: Create return_requests table
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Return Requests Table
-- ============================================
CREATE TABLE IF NOT EXISTS return_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID NOT NULL REFERENCES space_artwork_assignments(id) ON DELETE CASCADE,
    requested_by UUID NOT NULL,
    reason TEXT NOT NULL,
    requested_date DATE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'approved', 'rejected', 'in_transit', 'completed')),
    approval_date DATE,
    shipment_id UUID REFERENCES shipments(id),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE return_requests ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Return Requests
-- Corporates can view and create return requests for their space assignments
CREATE POLICY "Corporates can manage own return requests"
    ON return_requests FOR ALL
    USING (
        auth.uid() = requested_by
        AND EXISTS (
            SELECT 1 FROM space_artwork_assignments
            JOIN corporate_spaces ON corporate_spaces.id = space_artwork_assignments.space_id
            WHERE space_artwork_assignments.id = return_requests.assignment_id
            AND corporate_spaces.corporate_id = auth.uid()
        )
    );

-- Artists can view return requests for their artworks
CREATE POLICY "Artists can view artwork return requests"
    ON return_requests FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM space_artwork_assignments
            JOIN artworks ON artworks.id = space_artwork_assignments.artwork_id
            WHERE space_artwork_assignments.id = return_requests.assignment_id
            AND artworks.artist_id = auth.uid()
        )
    );

-- Service role can do everything
CREATE POLICY "Service role can manage return requests"
    ON return_requests FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_return_requests_assignment_id ON return_requests(assignment_id);
CREATE INDEX IF NOT EXISTS idx_return_requests_status ON return_requests(status);

-- Trigger to auto-update updated_at
CREATE TRIGGER update_return_requests_updated_at
    BEFORE UPDATE ON return_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
