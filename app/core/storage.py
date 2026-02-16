"""
Supabase Storage Service

This module provides file upload, download, and management functionality
using Supabase Storage.

Features:
- File upload with validation
- File download
- File deletion
- File path generation
- Error handling
"""

import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime
import mimetypes

from fastapi import UploadFile, HTTPException, status
from supabase import Client

from app.core.config import settings
from app.core.supabase import get_supabase_admin_client


# Allowed file types by bucket
ALLOWED_MIME_TYPES = {
    "artworks": ["image/jpeg", "image/png", "image/webp", "image/heic"],
    "profiles": ["image/jpeg", "image/png", "image/webp"],
    "spaces": ["image/jpeg", "image/png", "image/webp"],
    "documents": ["application/pdf", "image/jpeg", "image/png"],
}

# File size limits by bucket (in bytes)
FILE_SIZE_LIMITS = {
    "artworks": 10485760,  # 10MB
    "profiles": 5242880,   # 5MB
    "spaces": 10485760,    # 10MB
    "documents": 10485760, # 10MB
}

# Default bucket
DEFAULT_BUCKET = "artworks"


class StorageService:
    """Service for managing file storage in Supabase Storage"""

    def __init__(self, client: Optional[Client] = None):
        """
        Initialize storage service
        
        Args:
            client: Optional Supabase client (uses admin client if not provided)
        """
        self.client = client or get_supabase_admin_client()

    def validate_file(
        self,
        file: UploadFile,
        bucket: str = DEFAULT_BUCKET,
        max_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Validate uploaded file
        
        Args:
            file: FastAPI UploadFile object
            bucket: Target bucket name
            max_size: Optional custom max file size (overrides bucket default)
            
        Returns:
            Dict with validation results
            
        Raises:
            HTTPException: If validation fails
        """
        # Check bucket exists
        if bucket not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid bucket: {bucket}",
            )

        # Get file size
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        # Check file size
        max_file_size = max_size or FILE_SIZE_LIMITS.get(bucket, settings.MAX_FILE_SIZE)
        if file_size > max_file_size:
            size_mb = max_file_size / 1024 / 1024
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds limit of {size_mb:.1f}MB",
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty",
            )

        # Check MIME type
        content_type = file.content_type
        if not content_type:
            # Try to guess from filename
            content_type, _ = mimetypes.guess_type(file.filename or "")
            if not content_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not determine file type",
                )

        allowed_types = ALLOWED_MIME_TYPES.get(bucket, [])
        if content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{content_type}' not allowed. Allowed types: {', '.join(allowed_types)}",
            )

        # Validate file extension
        if file.filename:
            ext = Path(file.filename).suffix.lower()
            valid_extensions = {
                "artworks": [".jpg", ".jpeg", ".png", ".webp", ".heic"],
                "profiles": [".jpg", ".jpeg", ".png", ".webp"],
                "spaces": [".jpg", ".jpeg", ".png", ".webp"],
                "documents": [".pdf", ".jpg", ".jpeg", ".png"],
            }
            if ext not in valid_extensions.get(bucket, []):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File extension '{ext}' not allowed for bucket '{bucket}'",
                )

        return {
            "valid": True,
            "size": file_size,
            "content_type": content_type,
            "filename": file.filename,
        }

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent security issues
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = Path(filename).name

        # Remove or replace dangerous characters
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')

        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext

        return filename

    def generate_file_path(
        self,
        bucket: str,
        user_id: str,
        filename: str,
        subfolder: Optional[str] = None,
    ) -> str:
        """
        Generate file path for storage
        
        Args:
            bucket: Bucket name
            user_id: User ID (artist_id, corporate_id, etc.)
            filename: Original filename
            subfolder: Optional subfolder (e.g., artwork_id, space_id)
            
        Returns:
            Full file path in bucket
        """
        # Sanitize filename
        safe_filename = self.sanitize_filename(filename)

        # Generate unique filename to prevent collisions
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = str(uuid.uuid4())[:8]
        name, ext = os.path.splitext(safe_filename)
        unique_filename = f"{name}_{timestamp}_{file_id}{ext}"

        # Build path based on bucket type
        if subfolder:
            path = f"{user_id}/{subfolder}/{unique_filename}"
        else:
            path = f"{user_id}/{unique_filename}"

        return path

    async def upload_file(
        self,
        file: UploadFile,
        bucket: str,
        user_id: str,
        subfolder: Optional[str] = None,
        custom_filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload file to Supabase Storage
        
        Args:
            file: FastAPI UploadFile object
            bucket: Target bucket name
            user_id: User ID (for path organization)
            subfolder: Optional subfolder (e.g., artwork_id, space_id)
            custom_filename: Optional custom filename (will be sanitized)
            
        Returns:
            Dict with upload results (path, url, size, etc.)
            
        Raises:
            HTTPException: If upload fails
        """
        # Validate file
        validation = self.validate_file(file, bucket)
        
        # Generate file path
        filename = custom_filename or file.filename or "upload"
        file_path = self.generate_file_path(bucket, user_id, filename, subfolder)

        try:
            # Read file content
            file_content = await file.read()

            # Upload to Supabase Storage
            # Supabase Storage API: upload(path, file, file_options)
            response = self.client.storage.from_(bucket).upload(
                file_path,
                file_content,
                file_options={
                    "content-type": validation["content_type"],
                    "upsert": False,  # Don't overwrite existing files
                },
            )

            # Get public URL
            if bucket in ["artworks", "profiles", "spaces"]:
                # Public buckets
                url = self.client.storage.from_(bucket).get_public_url(file_path)
            else:
                # Private buckets - return signed URL (valid for 1 hour)
                url_data = self.client.storage.from_(bucket).create_signed_url(
                    file_path,
                    expires_in=3600,
                )
                url = url_data.get("signedURL", "")

            return {
                "success": True,
                "path": file_path,
                "url": url,
                "bucket": bucket,
                "size": validation["size"],
                "content_type": validation["content_type"],
                "filename": Path(file_path).name,
            }

        except Exception as e:
            error_msg = str(e)
            # Check for specific Supabase errors
            if "already exists" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"File already exists at path: {file_path}",
                )
            elif "permission" in error_msg.lower() or "unauthorized" in error_msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permission denied. Check storage policies.",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload file: {error_msg}",
                )

    async def delete_file(
        self,
        bucket: str,
        file_path: str,
    ) -> bool:
        """
        Delete file from Supabase Storage
        
        Args:
            bucket: Bucket name
            file_path: Path to file in bucket
            
        Returns:
            True if deleted successfully
            
        Raises:
            HTTPException: If deletion fails
        """
        try:
            response = self.client.storage.from_(bucket).remove([file_path])
            return True
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                # File doesn't exist, consider it deleted
                return True
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {error_msg}",
            )

    def get_file_url(
        self,
        bucket: str,
        file_path: str,
        signed: bool = False,
        expires_in: int = 3600,
    ) -> str:
        """
        Get file URL (public or signed)
        
        Args:
            bucket: Bucket name
            file_path: Path to file in bucket
            signed: Whether to generate signed URL (for private buckets)
            expires_in: Expiration time in seconds for signed URLs
            
        Returns:
            File URL
        """
        if signed or bucket == "documents":
            # Generate signed URL for private files
            url_data = self.client.storage.from_(bucket).create_signed_url(
                file_path,
                expires_in=expires_in,
            )
            return url_data.get("signedURL", "")
        else:
            # Public URL
            return self.client.storage.from_(bucket).get_public_url(file_path)

    def list_files(
        self,
        bucket: str,
        folder_path: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """
        List files in a bucket folder
        
        Args:
            bucket: Bucket name
            folder_path: Optional folder path to list
            limit: Maximum number of files to return
            
        Returns:
            List of file metadata
        """
        try:
            if folder_path:
                response = self.client.storage.from_(bucket).list(
                    path=folder_path,
                    limit=limit,
                )
            else:
                response = self.client.storage.from_(bucket).list(limit=limit)

            return response or []
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list files: {str(e)}",
            )


# Create singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """
    Get storage service instance (singleton)
    
    Returns:
        StorageService instance
    """
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
