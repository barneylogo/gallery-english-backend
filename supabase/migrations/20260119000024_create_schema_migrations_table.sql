-- Migration: Create schema_migrations tracking table
-- Created: 2026-01-19
-- Description: Tracks applied migrations for version control

BEGIN;

-- ============================================
-- Schema Migrations Table
-- ============================================
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    description TEXT
);

-- Enable Row Level Security
ALTER TABLE schema_migrations ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Schema Migrations
-- Only service role can access this system table
-- This prevents unauthorized access via Data API
CREATE POLICY "Service role only for schema_migrations"
    ON schema_migrations FOR ALL
    USING (false)  -- No user can access via client
    WITH CHECK (false);  -- No user can modify via client

-- Note: Service role (backend) can still access this table
-- because service role bypasses RLS by default

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at ON schema_migrations(applied_at);

COMMIT;
