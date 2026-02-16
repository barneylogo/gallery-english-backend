-- Migration: Create bank_accounts table
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Bank Accounts Table
-- ============================================
CREATE TABLE IF NOT EXISTS bank_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    user_type TEXT NOT NULL CHECK (user_type IN ('artist', 'corporate')),
    bank_name TEXT NOT NULL,
    branch_name TEXT NOT NULL,
    account_type TEXT NOT NULL CHECK (account_type IN ('savings', 'checking')),
    account_number TEXT NOT NULL,
    account_holder_name TEXT NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, user_type, account_number)
);

-- Enable Row Level Security
ALTER TABLE bank_accounts ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Bank Accounts
-- Users can view their own bank accounts
CREATE POLICY "Users can view own bank accounts"
    ON bank_accounts FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own bank accounts
CREATE POLICY "Users can insert own bank accounts"
    ON bank_accounts FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own bank accounts
CREATE POLICY "Users can update own bank accounts"
    ON bank_accounts FOR UPDATE
    USING (auth.uid() = user_id);

-- Service role can do everything (for backend operations)
CREATE POLICY "Service role can manage bank accounts"
    ON bank_accounts FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_bank_accounts_user ON bank_accounts(user_id, user_type);
CREATE INDEX IF NOT EXISTS idx_bank_accounts_primary ON bank_accounts(user_id, user_type, is_primary) 
    WHERE is_primary = true;

-- Trigger to auto-update updated_at
CREATE TRIGGER update_bank_accounts_updated_at
    BEFORE UPDATE ON bank_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
