-- Migration: Create shipping_tracking table
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Shipping Tracking Table
-- ============================================
CREATE TABLE IF NOT EXISTS shipping_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id UUID NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    tracking_event TEXT NOT NULL,
    location TEXT,
    timestamp TIMESTAMPTZ NOT NULL,
    notes TEXT,
    yamato_api_response JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE shipping_tracking ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Shipping Tracking
-- Users can view tracking for shipments they can view
CREATE POLICY "Users can view shipment tracking"
    ON shipping_tracking FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM shipments
            WHERE shipments.id = shipping_tracking.shipment_id
            AND (
                -- Artist can view if artwork is theirs
                EXISTS (
                    SELECT 1 FROM artworks
                    WHERE artworks.id = shipments.artwork_id
                    AND artworks.artist_id = auth.uid()
                )
                -- Customer can view if order is theirs
                OR EXISTS (
                    SELECT 1 FROM orders
                    WHERE orders.id = shipments.order_id
                    AND orders.customer_id = auth.uid()
                )
                -- Corporate can view if space is theirs
                OR EXISTS (
                    SELECT 1 FROM space_artwork_assignments
                    JOIN corporate_spaces ON corporate_spaces.id = space_artwork_assignments.space_id
                    WHERE space_artwork_assignments.id = shipments.assignment_id
                    AND corporate_spaces.corporate_id = auth.uid()
                )
            )
        )
    );

-- Service role can do everything
CREATE POLICY "Service role can manage tracking"
    ON shipping_tracking FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_shipping_tracking_shipment_id ON shipping_tracking(shipment_id);
CREATE INDEX IF NOT EXISTS idx_shipping_tracking_timestamp ON shipping_tracking(timestamp);

COMMIT;
