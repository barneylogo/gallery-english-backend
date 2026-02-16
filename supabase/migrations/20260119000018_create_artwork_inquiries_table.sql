-- Migration: Create artwork_inquiries table
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Artwork Inquiries Table
-- ============================================
CREATE TABLE IF NOT EXISTS artwork_inquiries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artwork_id UUID NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id),
    corporate_id UUID REFERENCES corporates(id),
    inquiry_type TEXT NOT NULL CHECK (inquiry_type IN ('question', 'purchase_interest', 'lease_interest')),
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' 
        CHECK (status IN ('open', 'responded', 'closed')),
    response TEXT,
    responded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE artwork_inquiries ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Artwork Inquiries
-- Customers can view and create their own inquiries
CREATE POLICY "Customers can manage own inquiries"
    ON artwork_inquiries FOR ALL
    USING (auth.uid() = customer_id OR customer_id IS NULL)
    WITH CHECK (auth.uid() = customer_id OR customer_id IS NULL);

-- Corporates can view inquiries for their artworks (if they have artworks)
-- Note: This is a simplified policy - in practice, corporates don't create artworks
CREATE POLICY "Corporates can view inquiries"
    ON artwork_inquiries FOR SELECT
    USING (auth.uid() = corporate_id);

-- Artists can view and respond to inquiries for their artworks
CREATE POLICY "Artists can manage inquiries for own artworks"
    ON artwork_inquiries FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM artworks
            WHERE artworks.id = artwork_inquiries.artwork_id
            AND artworks.artist_id = auth.uid()
        )
    );

-- Service role can do everything
CREATE POLICY "Service role can manage inquiries"
    ON artwork_inquiries FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_artwork_inquiries_artwork_id ON artwork_inquiries(artwork_id);
CREATE INDEX IF NOT EXISTS idx_artwork_inquiries_customer_id ON artwork_inquiries(customer_id);
CREATE INDEX IF NOT EXISTS idx_artwork_inquiries_status ON artwork_inquiries(status);

-- Trigger to auto-update updated_at
CREATE TRIGGER update_artwork_inquiries_updated_at
    BEFORE UPDATE ON artwork_inquiries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
