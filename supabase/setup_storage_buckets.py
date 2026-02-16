"""
Supabase Storage Buckets Setup Script

This script creates the required storage buckets for the Micro Gallery Japan platform.
Run this script after setting up your Supabase project.

Usage:
    python backend/supabase/setup_storage_buckets.py

Or from the backend directory:
    python supabase/setup_storage_buckets.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

try:
    import httpx
except ImportError:
    print("⚠️  'httpx' library not found. Installing...")
    print("   Run: pip install httpx")
    sys.exit(1)

from app.core.config import settings
from app.core.supabase import get_supabase_admin_client
from supabase import Client


# Bucket configurations
BUCKETS_CONFIG = [
    {
        "name": "artworks",
        "public": True,  # Public access for artwork images
        "file_size_limit": 10485760,  # 10MB
        "allowed_mime_types": ["image/jpeg", "image/png", "image/webp", "image/heic"],
        "description": "Artwork images (main images, thumbnails)",
    },
    {
        "name": "profiles",
        "public": True,  # Public access for profile images
        "file_size_limit": 5242880,  # 5MB
        "allowed_mime_types": ["image/jpeg", "image/png", "image/webp"],
        "description": "User profile images (artists, corporates, customers)",
    },
    {
        "name": "spaces",
        "public": True,  # Public access for space photos
        "file_size_limit": 10485760,  # 10MB
        "allowed_mime_types": ["image/jpeg", "image/png", "image/webp"],
        "description": "Corporate space photos",
    },
    {
        "name": "documents",
        "public": False,  # Private access for documents
        "file_size_limit": 10485760,  # 10MB
        "allowed_mime_types": ["application/pdf", "image/jpeg", "image/png"],
        "description": "Private documents (contracts, bank account info, etc.)",
    },
]


def create_bucket(client: Client, bucket_config: dict) -> bool:
    """
    Create a storage bucket with the given configuration

    Args:
        client: Supabase admin client
        bucket_config: Bucket configuration dictionary

    Returns:
        bool: True if bucket was created or already exists, False on error
    """
    bucket_name = bucket_config["name"]

    try:
        # Check if bucket already exists
        try:
            buckets = client.storage.list_buckets()
            existing_bucket = next((b for b in buckets if b.name == bucket_name), None)
            if existing_bucket:
                print(f"✅ Bucket '{bucket_name}' already exists")
                return True
        except Exception as check_error:
            # If list_buckets fails, try to create anyway
            print(f"⚠️  Could not check existing buckets: {check_error}")

        # Create bucket using Storage API
        # Note: Supabase Python client may have different API, so we'll try multiple approaches
        try:
            # Method 1: Direct API call (if available)
            response = client.storage.create_bucket(
                bucket_name,
                options={
                    "public": bucket_config["public"],
                    "file_size_limit": bucket_config["file_size_limit"],
                    "allowed_mime_types": bucket_config.get("allowed_mime_types", []),
                },
            )

            if response:
                print(
                    f"✅ Created bucket '{bucket_name}' (public: {bucket_config['public']})"
                )
                return True
        except AttributeError:
            # Method 2: Use REST API directly if client method doesn't exist
            url = f"{settings.SUPABASE_URL}/storage/v1/bucket"
            headers = {
                "apikey": settings.SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json",
            }
            data = {
                "name": bucket_name,
                "public": bucket_config["public"],
                "file_size_limit": bucket_config["file_size_limit"],
                "allowed_mime_types": bucket_config.get("allowed_mime_types", []),
            }

            response = httpx.post(url, json=data, headers=headers, timeout=30.0)

            if response.status_code == 200 or response.status_code == 201:
                print(
                    f"✅ Created bucket '{bucket_name}' (public: {bucket_config['public']})"
                )
                return True
            elif response.status_code == 409:
                # Bucket already exists
                print(f"✅ Bucket '{bucket_name}' already exists")
                return True
            else:
                print(f"❌ Failed to create bucket '{bucket_name}': {response.text}")
                return False

        return False

    except Exception as e:
        # Check if error is because bucket already exists
        error_msg = str(e).lower()
        if (
            "already exists" in error_msg
            or "duplicate" in error_msg
            or "409" in error_msg
        ):
            print(f"✅ Bucket '{bucket_name}' already exists")
            return True
        else:
            print(f"❌ Error creating bucket '{bucket_name}': {e}")
            print(
                f"   💡 You may need to create buckets manually via Supabase Dashboard"
            )
            return False


def setup_storage_policies(client: Client):
    """
    Set up storage bucket policies via SQL

    Note: Storage policies are managed via SQL in Supabase
    """
    print("\n📋 Storage policies should be configured via Supabase Dashboard:")
    print("   1. Go to Storage > Policies")
    print("   2. Select each bucket")
    print("   3. Create policies for:")
    print("      - Public buckets: Allow SELECT for authenticated users")
    print(
        "      - Private buckets: Allow SELECT/INSERT/UPDATE/DELETE for authenticated users"
    )
    print(
        "\n   Or use the Supabase SQL Editor to run policy SQL (see storage_policies.sql)"
    )


def main():
    """Main function to set up all storage buckets"""
    print("🚀 Setting up Supabase Storage Buckets...")
    print(f"📍 Supabase URL: {settings.SUPABASE_URL}")
    print(f"🔧 Environment: {settings.ENVIRONMENT}\n")

    # Get admin client (required for bucket creation)
    try:
        client = get_supabase_admin_client()
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        print("\n💡 Make sure your .env file has:")
        print("   - SUPABASE_URL")
        print("   - SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)

    # Create all buckets
    print("📦 Creating storage buckets...\n")
    results = []

    for bucket_config in BUCKETS_CONFIG:
        success = create_bucket(client, bucket_config)
        results.append((bucket_config["name"], success))
        if success:
            print(f"   Description: {bucket_config['description']}")
            print(
                f"   File size limit: {bucket_config['file_size_limit'] / 1024 / 1024:.1f}MB"
            )
            print(
                f"   Allowed types: {', '.join(bucket_config.get('allowed_mime_types', []))}\n"
            )

    # Summary
    print("\n" + "=" * 60)
    print("📊 Setup Summary:")
    print("=" * 60)

    success_count = sum(1 for _, success in results if success)
    total_count = len(results)

    for bucket_name, success in results:
        status = "✅ Created/Exists" if success else "❌ Failed"
        print(f"   {bucket_name:20} {status}")

    print(f"\n   Total: {success_count}/{total_count} buckets ready")

    if success_count == total_count:
        print("\n✅ All storage buckets are ready!")
        print("\n📋 Next steps:")
        print("   1. Configure storage policies (see setup_storage_policies function)")
        print("   2. Test file upload functionality")
        print("   3. Verify bucket access permissions")
    else:
        print("\n⚠️  Some buckets failed to create. Check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
