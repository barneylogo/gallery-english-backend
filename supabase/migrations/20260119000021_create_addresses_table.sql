-- Migration: Create addresses table
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Addresses Table
-- ============================================
CREATE TABLE IF NOT EXISTS addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    user_type TEXT NOT NULL CHECK (user_type IN ('artist', 'corporate', 'customer')),
    address_type TEXT NOT NULL CHECK (address_type IN ('primary', 'shipping', 'billing', 'display')),
    name TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    prefecture TEXT NOT NULL,
    city TEXT NOT NULL,
    street_address TEXT NOT NULL,
    building_name TEXT,
    phone TEXT,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE addresses ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Addresses
-- Users can view and manage their own addresses
CREATE POLICY "Users can manage own addresses"
    ON addresses FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Service role can do everything
CREATE POLICY "Service role can manage addresses"
    ON addresses FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_addresses_user ON addresses(user_id, user_type);
CREATE INDEX IF NOT EXISTS idx_addresses_default ON addresses(user_id, user_type, is_default) 
    WHERE is_default = true;

-- Trigger to auto-update updated_at
CREATE TRIGGER update_addresses_updated_at
    BEFORE UPDATE ON addresses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
