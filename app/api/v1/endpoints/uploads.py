"""
File upload endpoints

Handles file uploads for artworks, profiles, spaces, and documents.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Form, Security
from app.core.dependencies import security
from pydantic import BaseModel
from typing import Optional, List

from app.core.storage import get_storage_service, StorageService
from app.core.dependencies import get_current_user, CurrentUser
from app.core.image_processing import (
    get_image_processing_service,
    ImageProcessingService,
    ImageSize,
)

router = APIRouter()


class UploadResponse(BaseModel):
    """Response model for file upload"""
    success: bool
    path: str
    url: str
    bucket: str
    size: int
    content_type: str
    filename: str


class DeleteFileResponse(BaseModel):
    """Response model for file deletion"""
    success: bool
    message: str


class ProcessedImageUploadResponse(BaseModel):
    """Response model for processed image upload"""
    success: bool
    images: dict  # Dict with size names as keys
    metadata: dict
    dominant_color: Optional[str]
    original_info: dict


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    bucket: str = Form(default="artworks", description="Target bucket (artworks, profiles, spaces, documents)"),
    subfolder: Optional[str] = Form(default=None, description="Optional subfolder (e.g., artwork_id, space_id)"),
    credentials = Security(security),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Upload a file to Supabase Storage
    
    Requires authentication. Files are organized by user_id.
    
    Buckets:
    - artworks: Artwork images (10MB max, JPEG/PNG/WebP/HEIC)
    - profiles: Profile images (5MB max, JPEG/PNG/WebP)
    - spaces: Space photos (10MB max, JPEG/PNG/WebP)
    - documents: Private documents (10MB max, PDF/JPEG/PNG)
    """
    storage_service = get_storage_service()
    
    try:
        result = await storage_service.upload_file(
            file=file,
            bucket=bucket,
            user_id=current_user.id,
            subfolder=subfolder,
        )
        
        return UploadResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}",
        )


@router.post("/upload/multiple", response_model=List[UploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    bucket: str = Form(default="artworks", description="Target bucket"),
    subfolder: Optional[str] = Form(default=None, description="Optional subfolder"),
    credentials = Security(security),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Upload multiple files to Supabase Storage
    
    Requires authentication. All files are uploaded to the same bucket and subfolder.
    """
    storage_service = get_storage_service()
    results = []
    errors = []
    
    for file in files:
        try:
            result = await storage_service.upload_file(
                file=file,
                bucket=bucket,
                user_id=current_user.id,
                subfolder=subfolder,
            )
            results.append(UploadResponse(**result))
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    if errors and not results:
        # All uploads failed
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"All uploads failed: {'; '.join(errors)}",
        )
    
    if errors:
        # Some uploads failed, but return successful ones
        # In production, you might want to handle this differently
        pass
    
    return results


@router.delete("/delete/{bucket}/{file_path:path}", response_model=DeleteFileResponse)
async def delete_file(
    bucket: str,
    file_path: str,
    credentials = Security(security),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Delete a file from Supabase Storage
    
    Requires authentication. Users can only delete their own files.
    File path should be URL-encoded if it contains special characters.
    """
    storage_service = get_storage_service()
    
    # Security check: ensure user can only delete their own files
    if not file_path.startswith(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own files",
        )
    
    try:
        success = await storage_service.delete_file(bucket, file_path)
        
        return DeleteFileResponse(
            success=success,
            message=f"File deleted successfully" if success else "File not found",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}",
        )


@router.get("/url/{bucket}/{file_path:path}")
async def get_file_url(
    bucket: str,
    file_path: str,
    signed: bool = False,
    expires_in: int = 3600,
    credentials = Security(security),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get file URL (public or signed)
    
    For private buckets (documents), signed URLs are required.
    """
    storage_service = get_storage_service()
    
    try:
        url = storage_service.get_file_url(
            bucket=bucket,
            file_path=file_path,
            signed=signed or bucket == "documents",
            expires_in=expires_in,
        )
        
        return {"url": url, "bucket": bucket, "path": file_path}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file URL: {str(e)}",
        )


@router.post(
    "/upload/processed",
    response_model=ProcessedImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_processed_image(
    file: UploadFile = File(...),
    bucket: str = Form(default="artworks", description="Target bucket"),
    subfolder: Optional[str] = Form(default=None, description="Optional subfolder"),
    generate_sizes: Optional[str] = Form(
        default="thumbnail,medium,large",
        description="Comma-separated list of sizes to generate (thumbnail,medium,large)",
    ),
    convert_heic: bool = Form(default=True, description="Convert HEIC to JPEG"),
    credentials = Security(security),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Upload and process image: resize, optimize, convert HEIC, extract metadata
    
    This endpoint:
    - Validates the image
    - Converts HEIC to JPEG if needed
    - Generates multiple sizes (thumbnail, medium, large)
    - Optimizes images for web
    - Extracts EXIF metadata
    - Extracts dominant color
    - Uploads all sizes to storage
    
    Requires authentication.
    """
    storage_service = get_storage_service()
    image_service = get_image_processing_service()
    
    try:
        # Parse sizes
        size_names = [s.strip().lower() for s in generate_sizes.split(",")]
        sizes = []
        for name in size_names:
            if name == "thumbnail":
                sizes.append(ImageSize.THUMBNAIL)
            elif name == "medium":
                sizes.append(ImageSize.MEDIUM)
            elif name == "large":
                sizes.append(ImageSize.LARGE)
            elif name == "original":
                sizes.append(ImageSize.ORIGINAL)
        
        if not sizes:
            sizes = [ImageSize.THUMBNAIL, ImageSize.MEDIUM, ImageSize.LARGE]
        
        # Process image
        processed = await image_service.process_and_save_image(
            file=file,
            output_format="JPEG",
            sizes=sizes,
            convert_heic=convert_heic,
        )
        
        # Upload each size to storage
        uploaded_images = {}
        for size_name, size_data in processed["images"].items():
            # Reset BytesIO to beginning
            size_data["data"].seek(0)
            
            # Create filename with size suffix
            original_filename = file.filename or "image.jpg"
            name, ext = original_filename.rsplit(".", 1) if "." in original_filename else (original_filename, "jpg")
            size_filename = f"{name}_{size_name}.{ext}"
            
            # Create temporary UploadFile-like object for storage service
            class BytesIOUploadFile:
                """Wrapper to make BytesIO work like UploadFile"""
                def __init__(self, bytes_io, filename, content_type="image/jpeg"):
                    self.bytes_io = bytes_io
                    self.filename = filename
                    self.content_type = content_type
                    self.file = bytes_io  # Storage service may access .file attribute
                
                async def read(self):
                    return self.bytes_io.read()
                
                def seek(self, position):
                    return self.bytes_io.seek(position)
            
            temp_file = BytesIOUploadFile(
                size_data["data"],
                size_filename,
                content_type=f"image/{size_data['format'].lower()}",
            )
            
            # Upload to storage
            upload_result = await storage_service.upload_file(
                file=temp_file,
                bucket=bucket,
                user_id=current_user.id,
                subfolder=subfolder,
            )
            
            uploaded_images[size_name] = {
                "path": upload_result["path"],
                "url": upload_result["url"],
                "width": size_data["width"],
                "height": size_data["height"],
                "format": size_data["format"],
                "size_bytes": size_data["size_bytes"],
            }
        
        return ProcessedImageUploadResponse(
            success=True,
            images=uploaded_images,
            metadata=processed["metadata"],
            dominant_color=processed["dominant_color"],
            original_info=processed["original_info"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image processing and upload failed: {str(e)}",
        )
