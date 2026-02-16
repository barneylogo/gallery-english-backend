-- Migration: Enable RLS on schema_migrations table
-- Created: 2026-01-19
-- Description: Fixes RLS warning for schema_migrations table

BEGIN;

-- Enable Row Level Security
ALTER TABLE schema_migrations ENABLE ROW LEVEL SECURITY;

-- Drop existing policy if it exists (in case of re-running)
DROP POLICY IF EXISTS "Service role only for schema_migrations" ON schema_migrations;

-- RLS Policies for Schema Migrations
-- Only service role can access this system table
-- This prevents unauthorized access via Data API
CREATE POLICY "Service role only for schema_migrations"
    ON schema_migrations FOR ALL
    USING (false)  -- No user can access via client
    WITH CHECK (false);  -- No user can modify via client

-- Note: Service role (backend) can still access this table
-- because service role bypasses RLS by default

COMMIT;
