-- Migration: Create customer_favorites table
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Customer Favorites Table
-- ============================================
CREATE TABLE IF NOT EXISTS customer_favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    artwork_id UUID NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(customer_id, artwork_id)
);

-- Enable Row Level Security
ALTER TABLE customer_favorites ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Customer Favorites
-- Customers can view and manage their own favorites
CREATE POLICY "Customers can manage own favorites"
    ON customer_favorites FOR ALL
    USING (auth.uid() = customer_id)
    WITH CHECK (auth.uid() = customer_id);

-- Service role can do everything
CREATE POLICY "Service role can manage customer favorites"
    ON customer_favorites FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_customer_favorites_customer_id ON customer_favorites(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_favorites_artwork_id ON customer_favorites(artwork_id);

COMMIT;
