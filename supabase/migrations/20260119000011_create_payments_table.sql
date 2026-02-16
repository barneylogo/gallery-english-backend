-- Migration: Create payments table with RLS policies
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Payments Table
-- ============================================
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    payment_gateway TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    transaction_id TEXT,
    amount DECIMAL(12, 2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'JPY',
    status TEXT NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'refunded', 'cancelled')),
    gateway_response JSONB,
    failure_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Enable Row Level Security
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Payments
-- Users can view payments for their orders (via order ownership)
CREATE POLICY "Users can view own order payments"
    ON payments FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM orders
            WHERE orders.id = payments.order_id
            AND (
                orders.customer_id = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM artworks
                    WHERE artworks.id = orders.artwork_id
                    AND artworks.artist_id = auth.uid()
                )
                OR EXISTS (
                    SELECT 1 FROM corporate_spaces
                    WHERE corporate_spaces.id = orders.space_id
                    AND corporate_spaces.corporate_id = auth.uid()
                )
            )
        )
    );

-- Service role can do everything
CREATE POLICY "Service role can manage payments"
    ON payments FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_transaction_id ON payments(transaction_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at);

-- Trigger to auto-update updated_at
CREATE TRIGGER update_payments_updated_at
    BEFORE UPDATE ON payments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
