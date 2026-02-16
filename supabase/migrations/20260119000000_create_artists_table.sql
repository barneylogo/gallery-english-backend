-- Migration: Create artists table with RLS policies and indexes
-- Created: 2026-01-19

-- ============================================
-- Artists Table
-- ============================================
CREATE TABLE IF NOT EXISTS artists (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    birth_date DATE,
    phone TEXT,
    agreement_copyright BOOLEAN NOT NULL DEFAULT false,
    agreement_ai BOOLEAN NOT NULL DEFAULT false,
    agreement_commercial BOOLEAN NOT NULL DEFAULT false,
    agreement_report BOOLEAN NOT NULL DEFAULT false,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'suspended')),
    bio TEXT,
    portfolio_url TEXT,
    profile_image_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE artists ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Artists
-- Artists can read their own profile
CREATE POLICY "Artists can view own profile"
    ON artists FOR SELECT
    USING (auth.uid() = id);

-- Artists can update their own profile
CREATE POLICY "Artists can update own profile"
    ON artists FOR UPDATE
    USING (auth.uid() = id);

-- Service role can insert (for backend signup)
CREATE POLICY "Service role can insert artists"
    ON artists FOR INSERT
    WITH CHECK (true);

-- Public can view approved artists (for public artist listings)
CREATE POLICY "Public can view approved artists"
    ON artists FOR SELECT
    USING (status = 'approved');

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_artists_email ON artists(email);
CREATE INDEX IF NOT EXISTS idx_artists_status ON artists(status);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER update_artists_updated_at
    BEFORE UPDATE ON artists
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
