-- Migration: Create orders table with RLS policies
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Orders Table
-- ============================================
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number TEXT UNIQUE NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    artwork_id UUID NOT NULL REFERENCES artworks(id) ON DELETE RESTRICT,
    space_id UUID REFERENCES corporate_spaces(id),
    order_type TEXT NOT NULL CHECK (order_type IN ('purchase', 'lease')),
    total_amount DECIMAL(12, 2) NOT NULL,
    tax_amount DECIMAL(12, 2) NOT NULL DEFAULT 0,
    shipping_cost DECIMAL(12, 2) NOT NULL DEFAULT 0,
    commission_rate DECIMAL(5, 2) NOT NULL DEFAULT 10.00,
    artist_commission DECIMAL(12, 2) NOT NULL,
    corporate_commission DECIMAL(12, 2) NOT NULL,
    platform_commission DECIMAL(12, 2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'confirmed', 'paid', 'shipped', 'delivered', 'cancelled', 'refunded')),
    payment_method TEXT,
    payment_status TEXT NOT NULL DEFAULT 'pending' 
        CHECK (payment_status IN ('pending', 'processing', 'completed', 'failed', 'refunded')),
    delivery_address JSONB NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    paid_at TIMESTAMPTZ,
    shipped_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ
);

-- Enable Row Level Security
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Orders
-- Customers can view their own orders
CREATE POLICY "Customers can view own orders"
    ON orders FOR SELECT
    USING (auth.uid() = customer_id);

-- Artists can view orders for their artworks
CREATE POLICY "Artists can view orders for own artworks"
    ON orders FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM artworks
            WHERE artworks.id = orders.artwork_id
            AND artworks.artist_id = auth.uid()
        )
    );

-- Corporates can view orders from their spaces
CREATE POLICY "Corporates can view orders from own spaces"
    ON orders FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM corporate_spaces
            WHERE corporate_spaces.id = orders.space_id
            AND corporate_spaces.corporate_id = auth.uid()
        )
    );

-- Service role can do everything
CREATE POLICY "Service role can manage orders"
    ON orders FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_artwork_id ON orders(artwork_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_payment_status ON orders(payment_status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);

-- Trigger to auto-update updated_at
CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
