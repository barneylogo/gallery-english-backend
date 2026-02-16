-- Migration: Create customers table with RLS policies
-- Created: 2026-01-19
-- ============================================
-- Customers Table
-- ============================================
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deleted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Enable Row Level Security
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
-- RLS Policies for Customers
-- Customers can view their own profile
CREATE POLICY "Customers can view own profile" ON customers FOR
SELECT USING (auth.uid() = id);
-- Customers can update their own profile
CREATE POLICY "Customers can update own profile" ON customers FOR
UPDATE USING (auth.uid() = id);
-- Service role can insert (for backend signup)
CREATE POLICY "Service role can insert customers" ON customers FOR
INSERT WITH CHECK (true);
-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);
-- Trigger to auto-update updated_at
CREATE TRIGGER update_customers_updated_at BEFORE
UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();