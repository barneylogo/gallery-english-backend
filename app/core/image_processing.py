"""
Image Processing Service

This module provides comprehensive image processing functionality including:
- Image validation
- Resize to multiple sizes (thumbnail, medium, large)
- Image compression and optimization
- HEIC to JPEG conversion
- EXIF data extraction
- Dominant color extraction
"""

import io
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from enum import Enum

from PIL import Image, ImageOps, ExifTags
from PIL.ExifTags import TAGS
import numpy as np
from colorthief import ColorThief
from fastapi import UploadFile, HTTPException, status

from app.core.config import settings


class ImageSize(Enum):
    """Image size presets"""
    THUMBNAIL = "thumbnail"
    MEDIUM = "medium"
    LARGE = "large"
    ORIGINAL = "original"


class ImageProcessingService:
    """Service for processing images"""

    # Size presets (max width or height)
    SIZE_PRESETS = {
        ImageSize.THUMBNAIL: settings.IMAGE_THUMBNAIL_SIZE,
        ImageSize.MEDIUM: settings.IMAGE_MEDIUM_SIZE,
        ImageSize.LARGE: settings.IMAGE_LARGE_SIZE,
    }

    # Supported image formats
    SUPPORTED_FORMATS = ["JPEG", "PNG", "WEBP", "HEIC", "HEIF"]
    
    # MIME type to format mapping
    MIME_TO_FORMAT = {
        "image/jpeg": "JPEG",
        "image/jpg": "JPEG",
        "image/png": "PNG",
        "image/webp": "WEBP",
        "image/heic": "HEIC",
        "image/heif": "HEIF",
    }

    def __init__(self):
        """Initialize image processing service"""
        # Register HEIF opener if pillow-heif is available
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
            self.heic_supported = True
        except ImportError:
            self.heic_supported = False

    def validate_image(self, file: UploadFile) -> Dict[str, Any]:
        """
        Validate uploaded image file
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Dict with validation results (valid, format, dimensions, etc.)
            
        Raises:
            HTTPException: If validation fails
        """
        try:
            # Read file content
            file_content = file.file.read()
            file.file.seek(0)  # Reset to beginning
            
            if len(file_content) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image file is empty",
                )
            
            # Try to open image
            try:
                image = Image.open(io.BytesIO(file_content))
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid image file: {str(e)}",
                )
            
            # Check format
            image_format = image.format
            if image_format not in self.SUPPORTED_FORMATS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported image format: {image_format}. Supported: {', '.join(self.SUPPORTED_FORMATS)}",
                )
            
            # Get dimensions
            width, height = image.size
            
            # Validate dimensions (minimum size)
            if width < 10 or height < 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Image dimensions too small (minimum 10x10 pixels)",
                )
            
            # Validate dimensions (maximum size)
            max_dimension = 10000  # 10K pixels max
            if width > max_dimension or height > max_dimension:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Image dimensions too large (maximum {max_dimension}x{max_dimension} pixels)",
                )
            
            return {
                "valid": True,
                "format": image_format,
                "width": width,
                "height": height,
                "mode": image.mode,
                "size_bytes": len(file_content),
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image validation failed: {str(e)}",
            )

    def is_heic_file(self, file: UploadFile) -> bool:
        """
        Check if file is HEIC/HEIF format
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            True if file is HEIC/HEIF
        """
        # Check MIME type
        mime_type = file.content_type or ""
        if mime_type.lower() in ["image/heic", "image/heif"]:
            return True
        
        # Check file extension
        if file.filename:
            ext = Path(file.filename).suffix.lower()
            if ext in [".heic", ".heif"]:
                return True
        
        # Check file content (magic bytes)
        try:
            file.file.seek(0)
            header = file.file.read(12)
            file.file.seek(0)
            
            # HEIC files start with specific bytes
            if header[:4] == b"ftyp" and b"heic" in header.lower():
                return True
        except Exception:
            pass
        
        return False

    async def convert_heic_to_jpeg(
        self,
        file: UploadFile,
        quality: int = settings.IMAGE_QUALITY_JPEG,
    ) -> io.BytesIO:
        """
        Convert HEIC/HEIF file to JPEG
        
        Args:
            file: FastAPI UploadFile object (HEIC file)
            quality: JPEG quality (1-100)
            
        Returns:
            BytesIO object containing JPEG image
            
        Raises:
            HTTPException: If conversion fails
        """
        if not self.heic_supported:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="HEIC conversion not supported. Please install pillow-heif.",
            )
        
        try:
            # Read file content
            file_content = await file.read()
            file.file.seek(0)
            
            # Open HEIC image
            image = Image.open(io.BytesIO(file_content))
            
            # Convert to RGB if necessary (HEIC might be in different color space)
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Save as JPEG
            output = io.BytesIO()
            image.save(
                output,
                format="JPEG",
                quality=quality,
                optimize=settings.IMAGE_OPTIMIZE,
            )
            output.seek(0)
            
            return output
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"HEIC to JPEG conversion failed: {str(e)}",
            )

    def resize_image(
        self,
        image: Image.Image,
        max_dimension: int,
        maintain_aspect_ratio: bool = True,
    ) -> Image.Image:
        """
        Resize image to fit within max dimension while maintaining aspect ratio
        
        Args:
            image: PIL Image object
            max_dimension: Maximum width or height
            maintain_aspect_ratio: Whether to maintain aspect ratio
            
        Returns:
            Resized PIL Image object
        """
        if not maintain_aspect_ratio:
            return image.resize((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        
        width, height = image.size
        
        # If image is already smaller, return as-is
        if width <= max_dimension and height <= max_dimension:
            return image
        
        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    async def process_image(
        self,
        file: UploadFile,
        sizes: Optional[List[ImageSize]] = None,
        convert_heic: bool = True,
        extract_metadata: bool = True,
        extract_color: bool = True,
    ) -> Dict[str, Any]:
        """
        Process image: validate, convert HEIC if needed, resize, optimize
        
        Args:
            file: FastAPI UploadFile object
            sizes: List of sizes to generate (default: [THUMBNAIL, MEDIUM, LARGE])
            convert_heic: Whether to convert HEIC to JPEG
            extract_metadata: Whether to extract EXIF metadata
            extract_color: Whether to extract dominant color
            
        Returns:
            Dict with processed images and metadata
        """
        if sizes is None:
            sizes = [ImageSize.THUMBNAIL, ImageSize.MEDIUM, ImageSize.LARGE]
        
        # Validate image
        validation = self.validate_image(file)
        
        # Read file content
        file_content = await file.read()
        file.file.seek(0)
        
        # Convert HEIC to JPEG if needed
        is_heic = self.is_heic_file(file)
        if is_heic and convert_heic:
            if not self.heic_supported:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="HEIC conversion not supported. Please install pillow-heif.",
                )
            jpeg_content = await self.convert_heic_to_jpeg(file)
            file_content = jpeg_content.read()
            validation["format"] = "JPEG"
            validation["converted_from"] = "HEIC"
        
        # Open image
        image = Image.open(io.BytesIO(file_content))
        
        # Auto-rotate based on EXIF orientation
        image = ImageOps.exif_transpose(image)
        
        # Process each size
        processed_images = {}
        for size in sizes:
            if size == ImageSize.ORIGINAL:
                processed_images[size.value] = {
                    "image": image,
                    "width": image.width,
                    "height": image.height,
                }
            else:
                max_dim = self.SIZE_PRESETS[size]
                resized = self.resize_image(image, max_dim)
                processed_images[size.value] = {
                    "image": resized,
                    "width": resized.width,
                    "height": resized.height,
                }
        
        # Extract metadata
        metadata = {}
        if extract_metadata:
            metadata = self.extract_exif_metadata(image)
        
        # Extract dominant color
        dominant_color = None
        if extract_color:
            dominant_color = self.extract_dominant_color(image)
        
        return {
            "original": {
                "format": validation["format"],
                "width": validation["width"],
                "height": validation["height"],
                "mode": validation["mode"],
                "size_bytes": validation["size_bytes"],
            },
            "processed": processed_images,
            "metadata": metadata,
            "dominant_color": dominant_color,
            "converted_from_heic": is_heic and convert_heic,
        }

    def optimize_image(
        self,
        image: Image.Image,
        format: str = "JPEG",
        quality: Optional[int] = None,
    ) -> io.BytesIO:
        """
        Optimize image: compress and save to BytesIO
        
        Args:
            image: PIL Image object
            format: Output format (JPEG, PNG, WEBP)
            quality: Quality setting (1-100, None for default)
            
        Returns:
            BytesIO object containing optimized image
        """
        output = io.BytesIO()
        
        # Set quality based on format
        if quality is None:
            if format == "JPEG":
                quality = settings.IMAGE_QUALITY_JPEG
            elif format == "WEBP":
                quality = settings.IMAGE_QUALITY_WEBP
            else:
                quality = 85
        
        # Convert to RGB if saving as JPEG
        if format == "JPEG" and image.mode != "RGB":
            image = image.convert("RGB")
        
        # Save with optimization
        save_kwargs = {
            "format": format,
            "optimize": settings.IMAGE_OPTIMIZE,
        }
        
        if format in ["JPEG", "WEBP"]:
            save_kwargs["quality"] = quality
        elif format == "PNG":
            # PNG uses compress_level (0-9, 9 is best compression)
            save_kwargs["compress_level"] = 9
        
        image.save(output, **save_kwargs)
        output.seek(0)
        
        return output

    def extract_exif_metadata(self, image: Image.Image) -> Dict[str, Any]:
        """
        Extract EXIF metadata from image
        
        Args:
            image: PIL Image object
            
        Returns:
            Dict with EXIF metadata
        """
        metadata = {}
        
        try:
            exifdata = image.getexif()
            
            if not exifdata:
                return metadata
            
            # Extract standard EXIF tags
            for tag_id, value in exifdata.items():
                tag = TAGS.get(tag_id, tag_id)
                
                # Convert bytes to string if needed
                if isinstance(value, bytes):
                    try:
                        value = value.decode("utf-8", errors="ignore")
                    except Exception:
                        value = str(value)
                
                metadata[tag] = value
            
            # Extract specific useful fields
            useful_fields = {
                "DateTime": exifdata.get(306),  # DateTime
                "DateTimeOriginal": exifdata.get(36867),  # DateTimeOriginal
                "Make": exifdata.get(271),  # Make (camera manufacturer)
                "Model": exifdata.get(272),  # Model (camera model)
                "Orientation": exifdata.get(274),  # Orientation
                "XResolution": exifdata.get(282),  # XResolution
                "YResolution": exifdata.get(283),  # YResolution
                "Software": exifdata.get(305),  # Software
            }
            
            # Add useful fields to metadata
            for key, value in useful_fields.items():
                if value is not None:
                    metadata[key] = value
            
        except Exception as e:
            # If EXIF extraction fails, return empty dict
            metadata["error"] = str(e)
        
        return metadata

    def extract_dominant_color(self, image: Image.Image) -> Optional[str]:
        """
        Extract dominant color from image (hex format)
        
        Args:
            image: PIL Image object
            
        Returns:
            Hex color code (e.g., "#FF5733") or None if extraction fails
        """
        try:
            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # Save image to BytesIO for ColorThief
            img_bytes = io.BytesIO()
            image.save(img_bytes, format="JPEG")
            img_bytes.seek(0)
            
            # Extract dominant color using ColorThief
            color_thief = ColorThief(img_bytes)
            dominant_color = color_thief.get_color(quality=1)
            
            # Convert RGB tuple to hex
            hex_color = "#{:02x}{:02x}{:02x}".format(
                dominant_color[0],
                dominant_color[1],
                dominant_color[2],
            )
            
            return hex_color.upper()
            
        except Exception as e:
            # If color extraction fails, return None
            return None

    async def process_and_save_image(
        self,
        file: UploadFile,
        output_format: str = "JPEG",
        sizes: Optional[List[ImageSize]] = None,
        convert_heic: bool = True,
    ) -> Dict[str, Any]:
        """
        Process image and return optimized versions ready for storage
        
        Args:
            file: FastAPI UploadFile object
            output_format: Output format (JPEG, PNG, WEBP)
            sizes: List of sizes to generate
            convert_heic: Whether to convert HEIC to JPEG
            
        Returns:
            Dict with processed image data ready for upload
        """
        # Process image
        processed = await self.process_image(
            file=file,
            sizes=sizes,
            convert_heic=convert_heic,
            extract_metadata=True,
            extract_color=True,
        )
        
        # Optimize each size
        optimized_images = {}
        for size_name, size_data in processed["processed"].items():
            img = size_data["image"]
            
            # Determine format
            if output_format == "AUTO":
                # Use original format if available, otherwise JPEG
                original_format = processed["original"]["format"]
                if original_format in ["JPEG", "PNG", "WEBP"]:
                    format_to_use = original_format
                else:
                    format_to_use = "JPEG"
            else:
                format_to_use = output_format
            
            # Optimize
            optimized = self.optimize_image(img, format=format_to_use)
            
            optimized_images[size_name] = {
                "data": optimized,
                "width": size_data["width"],
                "height": size_data["height"],
                "format": format_to_use,
                "size_bytes": len(optimized.getvalue()),
            }
        
        return {
            "images": optimized_images,
            "metadata": processed["metadata"],
            "dominant_color": processed["dominant_color"],
            "original_info": processed["original"],
        }


# Create singleton instance
_image_processing_service: Optional[ImageProcessingService] = None


def get_image_processing_service() -> ImageProcessingService:
    """
    Get image processing service instance (singleton)
    
    Returns:
        ImageProcessingService instance
    """
    global _image_processing_service
    if _image_processing_service is None:
        _image_processing_service = ImageProcessingService()
    return _image_processing_service
