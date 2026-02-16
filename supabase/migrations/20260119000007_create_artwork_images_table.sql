-- Migration: Create artwork_images table
-- Created: 2026-01-19
BEGIN;
-- ============================================
-- Artwork Images Table
-- ============================================
CREATE TABLE IF NOT EXISTS artwork_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artwork_id UUID NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    image_order INTEGER NOT NULL DEFAULT 0,
    is_main BOOLEAN DEFAULT false,
    alt_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Enable Row Level Security
ALTER TABLE artwork_images ENABLE ROW LEVEL SECURITY;
-- RLS Policies for Artwork Images
-- Users can view images of artworks they can view
CREATE POLICY "Users can view artwork images" ON artwork_images FOR
SELECT USING (
        EXISTS (
            SELECT 1
            FROM artworks
            WHERE artworks.id = artwork_images.artwork_id
                AND (
                    artworks.artist_id = auth.uid()
                    OR artworks.status = 'published'
                )
        )
    );
-- Artists can manage images of their own artworks
CREATE POLICY "Artists can manage own artwork images" ON artwork_images FOR ALL USING (
    EXISTS (
        SELECT 1
        FROM artworks
        WHERE artworks.id = artwork_images.artwork_id
            AND artworks.artist_id = auth.uid()
    )
);
-- Service role can do everything
CREATE POLICY "Service role can manage artwork images" ON artwork_images FOR ALL WITH CHECK (true);
-- Create indexes
CREATE INDEX IF NOT EXISTS idx_artwork_images_artwork_id ON artwork_images(artwork_id);
CREATE INDEX IF NOT EXISTS idx_artwork_images_order ON artwork_images(artwork_id, image_order);
COMMIT;