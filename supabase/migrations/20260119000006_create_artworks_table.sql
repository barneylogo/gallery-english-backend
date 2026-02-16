-- Migration: Create artworks table with RLS policies and indexes
-- Created: 2026-01-19

BEGIN;

-- ============================================
-- Artworks Table
-- ============================================
CREATE TABLE IF NOT EXISTS artworks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    custom_id TEXT UNIQUE NOT NULL,
    artist_id UUID NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    story TEXT,
    price DECIMAL(12, 2) NOT NULL,
    lease_price DECIMAL(12, 2),
    dimensions JSONB NOT NULL,
    size_class TEXT CHECK (size_class IN ('XS', 'S', 'M', 'L', 'XL', 'XXL')),
    year INTEGER,
    medium TEXT,
    support TEXT,
    weight DECIMAL(6, 2),
    has_frame BOOLEAN DEFAULT false,
    coating TEXT,
    status TEXT NOT NULL DEFAULT 'draft' 
        CHECK (status IN ('draft', 'published', 'recalled', 'sold', 'rented')),
    main_image_url TEXT NOT NULL,
    thumbnail_urls JSONB,
    dominant_color TEXT,
    qr_code_url TEXT,
    qr_code_data TEXT,
    packaging_info TEXT,
    maintenance_info TEXT,
    view_count INTEGER DEFAULT 0,
    favorite_count INTEGER DEFAULT 0,
    inquiry_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ
);

-- Enable Row Level Security
ALTER TABLE artworks ENABLE ROW LEVEL SECURITY;

-- RLS Policies for Artworks
-- Artists can view their own artworks
CREATE POLICY "Artists can view own artworks"
    ON artworks FOR SELECT
    USING (auth.uid() = artist_id);

-- Artists can insert their own artworks
CREATE POLICY "Artists can insert own artworks"
    ON artworks FOR INSERT
    WITH CHECK (auth.uid() = artist_id);

-- Artists can update their own artworks
CREATE POLICY "Artists can update own artworks"
    ON artworks FOR UPDATE
    USING (auth.uid() = artist_id);

-- Public can view published artworks
CREATE POLICY "Public can view published artworks"
    ON artworks FOR SELECT
    USING (status = 'published');

-- Service role can do everything (for backend operations)
CREATE POLICY "Service role can manage artworks"
    ON artworks FOR ALL
    WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_artworks_custom_id ON artworks(custom_id);
CREATE INDEX IF NOT EXISTS idx_artworks_artist_id ON artworks(artist_id);
CREATE INDEX IF NOT EXISTS idx_artworks_status ON artworks(status);
CREATE INDEX IF NOT EXISTS idx_artworks_price ON artworks(price);
CREATE INDEX IF NOT EXISTS idx_artworks_size_class ON artworks(size_class);
CREATE INDEX IF NOT EXISTS idx_artworks_created_at ON artworks(created_at);
CREATE INDEX IF NOT EXISTS idx_artworks_published_at ON artworks(published_at);
CREATE INDEX IF NOT EXISTS idx_artworks_status_published ON artworks(status, published_at) 
    WHERE status = 'published';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_artworks_updated_at
    BEFORE UPDATE ON artworks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
