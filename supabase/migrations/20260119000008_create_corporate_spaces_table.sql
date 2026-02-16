-- Migration: Create corporate_spaces table with RLS policies
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Corporate Spaces Table
-- ============================================
CREATE TABLE IF NOT EXISTS corporate_spaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    custom_id TEXT UNIQUE NOT NULL,
    corporate_id UUID NOT NULL REFERENCES corporates(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    facility_type TEXT NOT NULL,
    description TEXT,
    dimensions JSONB,
    lighting_info TEXT,
    wall_color TEXT,
    style_preference JSONB,
    photo_urls JSONB,
    address TEXT,
    postal_code TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE corporate_spaces ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Corporate Spaces
-- Corporates can view their own spaces
CREATE POLICY "Corporates can view own spaces"
    ON corporate_spaces FOR SELECT
    USING (auth.uid() = corporate_id);

-- Corporates can insert their own spaces
CREATE POLICY "Corporates can insert own spaces"
    ON corporate_spaces FOR INSERT
    WITH CHECK (auth.uid() = corporate_id);

-- Corporates can update their own spaces
CREATE POLICY "Corporates can update own spaces"
    ON corporate_spaces FOR UPDATE
    USING (auth.uid() = corporate_id);

-- Service role can do everything
CREATE POLICY "Service role can manage corporate spaces"
    ON corporate_spaces FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_corporate_spaces_custom_id ON corporate_spaces(custom_id);
CREATE INDEX IF NOT EXISTS idx_corporate_spaces_corporate_id ON corporate_spaces(corporate_id);
CREATE INDEX IF NOT EXISTS idx_corporate_spaces_active ON corporate_spaces(corporate_id, is_active) 
    WHERE is_active = true;

-- Trigger to auto-update updated_at
CREATE TRIGGER update_corporate_spaces_updated_at
    BEFORE UPDATE ON corporate_spaces
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
