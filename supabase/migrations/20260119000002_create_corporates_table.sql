-- Migration: Create corporates table with RLS policies
-- Created: 2026-01-19

-- ============================================
-- Corporates Table
-- ============================================
CREATE TABLE IF NOT EXISTS corporates (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    company_name TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    postal_code TEXT,
    address TEXT,
    phone TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'suspended')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE corporates ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Corporates
-- Corporates can view their own profile
CREATE POLICY "Corporates can view own profile"
    ON corporates FOR SELECT
    USING (auth.uid() = id);

-- Corporates can update their own profile
CREATE POLICY "Corporates can update own profile"
    ON corporates FOR UPDATE
    USING (auth.uid() = id);

-- Service role can insert (for backend signup)
CREATE POLICY "Service role can insert corporates"
    ON corporates FOR INSERT
    WITH CHECK (true);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_corporates_email ON corporates(email);
CREATE INDEX IF NOT EXISTS idx_corporates_status ON corporates(status);
CREATE INDEX IF NOT EXISTS idx_corporates_company_name ON corporates(company_name);

-- Trigger to auto-update updated_at
CREATE TRIGGER update_corporates_updated_at
    BEFORE UPDATE ON corporates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
