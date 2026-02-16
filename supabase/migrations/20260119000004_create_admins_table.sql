-- Migration: Create admins table with RLS policies
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Admins Table
-- ============================================
CREATE TABLE IF NOT EXISTS admins (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL DEFAULT 'moderator' 
        CHECK (role IN ('super_admin', 'admin', 'moderator', 'support')),
    permissions JSONB,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE admins ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Admins
-- Admins can view their own profile
CREATE POLICY "Admins can view own profile"
    ON admins FOR SELECT
    USING (auth.uid() = id);

-- Admins can update their own profile
CREATE POLICY "Admins can update own profile"
    ON admins FOR UPDATE
    USING (auth.uid() = id);

-- Service role can insert (for backend admin creation)
CREATE POLICY "Service role can insert admins"
    ON admins FOR INSERT
    WITH CHECK (true);

-- Super admins can view all admins
CREATE POLICY "Super admins can view all admins"
    ON admins FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM admins
            WHERE id = auth.uid() AND role = 'super_admin'
        )
    );

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email);
CREATE INDEX IF NOT EXISTS idx_admins_role ON admins(role);

-- Trigger to auto-update updated_at
CREATE TRIGGER update_admins_updated_at
    BEFORE UPDATE ON admins
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
