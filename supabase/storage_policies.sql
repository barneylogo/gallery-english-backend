-- Storage Bucket Policies for Micro Gallery Japan
-- Run this SQL in Supabase SQL Editor after creating buckets
-- Created: 2026-01-19

-- ============================================
-- Artworks Bucket Policies
-- ============================================
-- Public read access for published artworks
CREATE POLICY "Public can view artwork images"
ON storage.objects FOR SELECT
USING (bucket_id = 'artworks');

-- Artists can upload their own artwork images
CREATE POLICY "Artists can upload artwork images"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'artworks'
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Artists can update their own artwork images
CREATE POLICY "Artists can update own artwork images"
ON storage.objects FOR UPDATE
USING (
    bucket_id = 'artworks'
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Artists can delete their own artwork images
CREATE POLICY "Artists can delete own artwork images"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'artworks'
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- ============================================
-- Profiles Bucket Policies
-- ============================================
-- Public read access for profile images
CREATE POLICY "Public can view profile images"
ON storage.objects FOR SELECT
USING (bucket_id = 'profiles');

-- Users can upload their own profile images
CREATE POLICY "Users can upload own profile images"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'profiles'
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Users can update their own profile images
CREATE POLICY "Users can update own profile images"
ON storage.objects FOR UPDATE
USING (
    bucket_id = 'profiles'
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Users can delete their own profile images
CREATE POLICY "Users can delete own profile images"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'profiles'
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- ============================================
-- Spaces Bucket Policies
-- ============================================
-- Public read access for space photos
CREATE POLICY "Public can view space photos"
ON storage.objects FOR SELECT
USING (bucket_id = 'spaces');

-- Corporates can upload space photos
CREATE POLICY "Corporates can upload space photos"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'spaces'
    AND EXISTS (
        SELECT 1 FROM corporates
        WHERE corporates.id = auth.uid()
    )
);

-- Corporates can update their space photos
CREATE POLICY "Corporates can update own space photos"
ON storage.objects FOR UPDATE
USING (
    bucket_id = 'spaces'
    AND EXISTS (
        SELECT 1 FROM corporates
        WHERE corporates.id = auth.uid()
    )
);

-- Corporates can delete their space photos
CREATE POLICY "Corporates can delete own space photos"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'spaces'
    AND EXISTS (
        SELECT 1 FROM corporates
        WHERE corporates.id = auth.uid()
    )
);

-- ============================================
-- Documents Bucket Policies (Private)
-- ============================================
-- Users can view their own documents
CREATE POLICY "Users can view own documents"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'documents'
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Users can upload their own documents
CREATE POLICY "Users can upload own documents"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'documents'
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Users can update their own documents
CREATE POLICY "Users can update own documents"
ON storage.objects FOR UPDATE
USING (
    bucket_id = 'documents'
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- Users can delete their own documents
CREATE POLICY "Users can delete own documents"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'documents'
    AND auth.uid()::text = (storage.foldername(name))[1]
);

-- ============================================
-- Notes:
-- ============================================
-- 1. File paths should follow pattern: {user_id}/{filename}
--    Example: artworks/550e8400-e29b-41d4-a716-446655440000/artwork-1.jpg
--
-- 2. For service role operations (backend), use service role key
--    which bypasses RLS policies
--
-- 3. To test policies, use Supabase Dashboard > Storage > Policies
--    and verify each policy works as expected
