-- Migration: Create shipments table
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Shipments Table
-- ============================================
CREATE TABLE IF NOT EXISTS shipments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_number TEXT UNIQUE NOT NULL,
    shipment_pattern TEXT NOT NULL 
        CHECK (shipment_pattern IN ('box_to_artist', 'artwork_to_corporate', 'return_to_artist', 'artwork_to_customer')),
    order_id UUID REFERENCES orders(id),
    assignment_id UUID REFERENCES space_artwork_assignments(id),
    artwork_id UUID NOT NULL REFERENCES artworks(id) ON DELETE RESTRICT,
    from_address JSONB NOT NULL,
    to_address JSONB NOT NULL,
    yamato_tracking_number TEXT,
    yamato_shipment_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'label_created', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'failed', 'returned')),
    shipping_cost DECIMAL(10, 2),
    estimated_delivery_date DATE,
    actual_delivery_date DATE,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMPTZ
);

-- Enable Row Level Security
ALTER TABLE shipments ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Shipments
-- Artists can view shipments for their artworks
CREATE POLICY "Artists can view own artwork shipments"
    ON shipments FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM artworks
            WHERE artworks.id = shipments.artwork_id
            AND artworks.artist_id = auth.uid()
        )
    );

-- Customers can view shipments for their orders
CREATE POLICY "Customers can view own order shipments"
    ON shipments FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM orders
            WHERE orders.id = shipments.order_id
            AND orders.customer_id = auth.uid()
        )
    );

-- Corporates can view shipments for their spaces
CREATE POLICY "Corporates can view own space shipments"
    ON shipments FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM corporate_spaces
            WHERE corporate_spaces.id = (
                SELECT space_id FROM space_artwork_assignments
                WHERE space_artwork_assignments.id = shipments.assignment_id
            )
            AND corporate_spaces.corporate_id = auth.uid()
        )
    );

-- Service role can do everything
CREATE POLICY "Service role can manage shipments"
    ON shipments FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_shipments_shipment_number ON shipments(shipment_number);
CREATE INDEX IF NOT EXISTS idx_shipments_artwork_id ON shipments(artwork_id);
CREATE INDEX IF NOT EXISTS idx_shipments_order_id ON shipments(order_id);
CREATE INDEX IF NOT EXISTS idx_shipments_yamato_tracking ON shipments(yamato_tracking_number);
CREATE INDEX IF NOT EXISTS idx_shipments_status ON shipments(status);
CREATE INDEX IF NOT EXISTS idx_shipments_pattern ON shipments(shipment_pattern);

-- Trigger to auto-update updated_at
CREATE TRIGGER update_shipments_updated_at
    BEFORE UPDATE ON shipments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
