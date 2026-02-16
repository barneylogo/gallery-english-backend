# Supabase Storage Setup Guide

This guide explains how to set up Supabase Storage buckets for the Micro Gallery Japan platform.

## Quick Start

### Option 1: Supabase CLI (Recommended for Automation)

If you have Supabase CLI installed:

```bash
# Create each bucket
supabase storage create artworks --public
supabase storage create profiles --public
supabase storage create spaces --public
supabase storage create documents
```

### Option 2: Python Setup Script

Run the Python setup script:

```bash
# From backend directory
python supabase/setup_storage_buckets.py

# Or from project root
python backend/supabase/setup_storage_buckets.py
```

**Note:** This script uses the Supabase REST API. If it fails, use Option 1 or Option 3.

This script will:
- ✅ Create all required storage buckets
- ✅ Configure bucket settings (public/private, file size limits)
- ✅ Set allowed MIME types
- ✅ Verify bucket creation

### Option 3: Manual Setup via Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to **Storage**
3. Click **New bucket** for each bucket:
   - `artworks` (Public, 10MB limit)
   - `profiles` (Public, 5MB limit)
   - `spaces` (Public, 10MB limit)
   - `documents` (Private, 10MB limit)

## Storage Buckets

### 1. `artworks` Bucket
- **Purpose**: Artwork images (main images, thumbnails)
- **Access**: Public (read), Authenticated (write)
- **File Size Limit**: 10MB
- **Allowed Types**: JPEG, PNG, WebP, HEIC
- **Path Structure**: `{artist_id}/{artwork_id}/{filename}`

### 2. `profiles` Bucket
- **Purpose**: User profile images
- **Access**: Public (read), Authenticated (write)
- **File Size Limit**: 5MB
- **Allowed Types**: JPEG, PNG, WebP
- **Path Structure**: `{user_id}/{filename}`

### 3. `spaces` Bucket
- **Purpose**: Corporate space photos
- **Access**: Public (read), Corporate users (write)
- **File Size Limit**: 10MB
- **Allowed Types**: JPEG, PNG, WebP
- **Path Structure**: `{corporate_id}/{space_id}/{filename}`

### 4. `documents` Bucket
- **Purpose**: Private documents (contracts, bank info, etc.)
- **Access**: Private (authenticated users only)
- **File Size Limit**: 10MB
- **Allowed Types**: PDF, JPEG, PNG
- **Path Structure**: `{user_id}/{document_type}/{filename}`

## Storage Policies Setup

After creating buckets, set up Row Level Security (RLS) policies:

### Option 1: Run SQL Script

1. Go to Supabase Dashboard > SQL Editor
2. Copy and paste contents of `storage_policies.sql`
3. Execute the script

### Option 2: Manual Policy Setup

For each bucket, create policies via Dashboard:

1. Go to **Storage** > Select bucket > **Policies**
2. Create policies for:
   - **SELECT**: Who can view files
   - **INSERT**: Who can upload files
   - **UPDATE**: Who can update files
   - **DELETE**: Who can delete files

## File Path Structure

### Recommended Path Patterns

```
artworks/
  └── {artist_id}/
      └── {artwork_id}/
          ├── main.jpg
          ├── thumbnail.jpg
          └── image-1.jpg

profiles/
  └── {user_id}/
      └── profile.jpg

spaces/
  └── {corporate_id}/
      └── {space_id}/
          ├── photo-1.jpg
          └── photo-2.jpg

documents/
  └── {user_id}/
      ├── contracts/
      │   └── contract-2026.pdf
      └── bank-accounts/
          └── statement.pdf
```

## Testing

### Test Bucket Creation

```bash
python supabase/setup_storage_buckets.py
```

Expected output:
```
✅ Created bucket 'artworks' (public: True)
✅ Created bucket 'profiles' (public: True)
✅ Created bucket 'spaces' (public: True)
✅ Created bucket 'documents' (public: False)
```

### Test File Upload

Use Supabase Dashboard > Storage to manually upload a test file and verify:
- File uploads successfully
- File is accessible via public URL (for public buckets)
- File permissions are correct

## Troubleshooting

### Error: "Bucket already exists"
- ✅ This is normal if buckets were created previously
- The script will skip existing buckets

### Error: "Permission denied"
- Check that `SUPABASE_SERVICE_ROLE_KEY` is set in `.env`
- Service role key is required for bucket creation

### Error: "Invalid bucket configuration"
- Verify bucket name follows Supabase naming rules (lowercase, no spaces)
- Check file size limits are within Supabase limits

### Policies Not Working
- Ensure RLS is enabled on `storage.objects` table
- Verify policies are created correctly
- Test with authenticated user tokens

## Environment Variables

Required in `.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## Next Steps

After setting up storage buckets:

1. ✅ Verify all buckets are created
2. ✅ Set up storage policies (run `storage_policies.sql`)
3. ✅ Test file upload functionality
4. ✅ Implement file upload service (Phase 1, Step 1.2)
5. ✅ Implement image processing (Phase 2)

## References

- [Supabase Storage Documentation](https://supabase.com/docs/guides/storage)
- [Storage Policies Guide](https://supabase.com/docs/guides/storage/security/access-control)
- [Storage API Reference](https://supabase.com/docs/reference/python/storage-api)
