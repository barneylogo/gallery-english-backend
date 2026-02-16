"""
Artwork management endpoints

Complete CRUD operations for artworks with image upload, processing, and management.
"""

from fastapi import APIRouter, HTTPException, status, Query, Depends, UploadFile, File, Form, Security
from app.core.dependencies import security
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from decimal import Decimal
import json

from app.core.dependencies import require_artist, CurrentUser, get_current_user
from app.core.supabase import get_supabase_admin_client
from app.core.storage import get_storage_service
from app.core.image_processing import get_image_processing_service, ImageSize
from app.utils.id_generator import generate_custom_id

router = APIRouter()


# Request/Response Models
class ArtworkDimensions(BaseModel):
    """Artwork dimensions"""
    width: float = Field(..., description="Width in cm")
    height: float = Field(..., description="Height in cm")
    depth: Optional[float] = Field(None, description="Depth in cm (optional)")


class ArtworkCreateRequest(BaseModel):
    """Request model for creating artwork"""
    title: str = Field(..., min_length=1, description="Artwork title")
    description: Optional[str] = None
    story: Optional[str] = None
    price: Decimal = Field(..., gt=0, description="Purchase price in JPY")
    lease_price: Optional[Decimal] = Field(None, ge=0, description="Monthly lease price in JPY")
    dimensions: ArtworkDimensions
    size_class: Optional[str] = Field(None, description="Size class: XS, S, M, L, XL, XXL")
    year: Optional[int] = None
    medium: Optional[str] = None  # 油彩, アクリル, etc.
    support: Optional[str] = None  # キャンバス, 紙, etc.
    weight: Optional[Decimal] = None
    has_frame: bool = False
    coating: Optional[str] = None
    packaging_info: Optional[str] = None
    maintenance_info: Optional[str] = None


class ArtworkImageInfo(BaseModel):
    """Artwork image information"""
    id: str
    image_url: str
    image_order: int
    is_main: bool
    alt_text: Optional[str] = None


class ArtistInfo(BaseModel):
    """Artist information"""
    id: str
    name: str
    profile_image_url: Optional[str] = None


class ArtworkResponse(BaseModel):
    """Response model for artwork"""
    id: str
    custom_id: str
    artist_id: str
    artist: Optional[ArtistInfo] = None
    title: str
    description: Optional[str] = None
    story: Optional[str] = None
    price: Decimal
    lease_price: Optional[Decimal] = None
    dimensions: Dict[str, Any]
    size_class: Optional[str] = None
    year: Optional[int] = None
    medium: Optional[str] = None
    support: Optional[str] = None
    weight: Optional[Decimal] = None
    has_frame: bool = False
    coating: Optional[str] = None
    status: str
    main_image_url: str
    thumbnail_urls: Optional[List[str]] = None
    images: Optional[List[ArtworkImageInfo]] = None
    dominant_color: Optional[str] = None
    qr_code_url: Optional[str] = None
    qr_code_data: Optional[str] = None
    packaging_info: Optional[str] = None
    maintenance_info: Optional[str] = None
    view_count: int = 0
    favorite_count: int = 0
    inquiry_count: int = 0
    created_at: str
    updated_at: str
    published_at: Optional[str] = None


class ArtworkListResponse(BaseModel):
    """Response model for artwork list"""
    items: List[ArtworkResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ArtworkUpdateRequest(BaseModel):
    """Request model for updating artwork"""
    title: Optional[str] = None
    description: Optional[str] = None
    story: Optional[str] = None
    price: Optional[Decimal] = None
    lease_price: Optional[Decimal] = None
    dimensions: Optional[ArtworkDimensions] = None
    size_class: Optional[str] = None
    year: Optional[int] = None
    medium: Optional[str] = None
    support: Optional[str] = None
    weight: Optional[Decimal] = None
    has_frame: Optional[bool] = None
    coating: Optional[str] = None
    packaging_info: Optional[str] = None
    maintenance_info: Optional[str] = None


# Helper Functions
def artwork_to_response(artwork_data: dict, include_artist: bool = False, include_images: bool = False) -> ArtworkResponse:
    """Convert database artwork to response model"""
    admin_client = get_supabase_admin_client()
    
    # Get artist info if requested
    artist_info = None
    if include_artist:
        artist_response = admin_client.table("artists").select("id, name, profile_image_url").eq("id", artwork_data["artist_id"]).execute()
        if artist_response.data:
            artist_data = artist_response.data[0]
            artist_info = ArtistInfo(
                id=artist_data["id"],
                name=artist_data["name"],
                profile_image_url=artist_data.get("profile_image_url"),
            )
    
    # Get images if requested
    images = None
    if include_images:
        images_response = admin_client.table("artwork_images").select("*").eq("artwork_id", artwork_data["id"]).order("image_order").execute()
        if images_response.data:
            images = [
                ArtworkImageInfo(
                    id=img["id"],
                    image_url=img["image_url"],
                    image_order=img["image_order"],
                    is_main=img["is_main"],
                    alt_text=img.get("alt_text"),
                )
                for img in images_response.data
            ]
    
    # Parse dimensions JSONB
    dimensions = artwork_data.get("dimensions", {})
    if isinstance(dimensions, str):
        dimensions = json.loads(dimensions)
    
    # Parse thumbnail_urls JSONB
    thumbnail_urls = artwork_data.get("thumbnail_urls")
    if isinstance(thumbnail_urls, str):
        thumbnail_urls = json.loads(thumbnail_urls)
    if isinstance(thumbnail_urls, list):
        thumbnail_urls = thumbnail_urls
    
    return ArtworkResponse(
        id=artwork_data["id"],
        custom_id=artwork_data["custom_id"],
        artist_id=artwork_data["artist_id"],
        artist=artist_info,
        title=artwork_data["title"],
        description=artwork_data.get("description"),
        story=artwork_data.get("story"),
        price=Decimal(str(artwork_data["price"])),
        lease_price=Decimal(str(artwork_data["lease_price"])) if artwork_data.get("lease_price") else None,
        dimensions=dimensions,
        size_class=artwork_data.get("size_class"),
        year=artwork_data.get("year"),
        medium=artwork_data.get("medium"),
        support=artwork_data.get("support"),
        weight=Decimal(str(artwork_data["weight"])) if artwork_data.get("weight") else None,
        has_frame=artwork_data.get("has_frame", False),
        coating=artwork_data.get("coating"),
        status=artwork_data["status"],
        main_image_url=artwork_data["main_image_url"],
        thumbnail_urls=thumbnail_urls,
        images=images,
        dominant_color=artwork_data.get("dominant_color"),
        qr_code_url=artwork_data.get("qr_code_url"),
        qr_code_data=artwork_data.get("qr_code_data"),
        packaging_info=artwork_data.get("packaging_info"),
        maintenance_info=artwork_data.get("maintenance_info"),
        view_count=artwork_data.get("view_count", 0),
        favorite_count=artwork_data.get("favorite_count", 0),
        inquiry_count=artwork_data.get("inquiry_count", 0),
        created_at=artwork_data["created_at"],
        updated_at=artwork_data["updated_at"],
        published_at=artwork_data.get("published_at"),
    )


# 4.1 Artwork Creation API
@router.post("/", response_model=ArtworkResponse, status_code=status.HTTP_201_CREATED)
async def create_artwork(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    story: Optional[str] = Form(None),
    price: Decimal = Form(...),
    lease_price: Optional[Decimal] = Form(None),
    width: float = Form(...),
    height: float = Form(...),
    depth: Optional[float] = Form(None),
    size_class: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    medium: Optional[str] = Form(None),
    support: Optional[str] = Form(None),
    weight: Optional[Decimal] = Form(None),
    has_frame: bool = Form(False),
    coating: Optional[str] = Form(None),
    packaging_info: Optional[str] = Form(None),
    maintenance_info: Optional[str] = Form(None),
    images: List[UploadFile] = File(..., description="Artwork images (at least 1 required)"),
    credentials = Security(security),
    current_user: CurrentUser = Depends(require_artist),
):
    """
    Create new artwork with image upload
    
    Requires: Artist authentication
    - Uploads and processes images (resize, optimize, convert HEIC)
    - Generates custom_id (WRK-001, WRK-002, etc.)
    - Stores artwork in database
    - Stores image URLs in artwork_images table
    - Extracts and stores dominant color
    """
    admin_client = get_supabase_admin_client()
    storage_service = get_storage_service()
    image_service = get_image_processing_service()
    
    if not images or len(images) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one image is required",
        )
    
    try:
        # Generate custom_id
        custom_id = generate_custom_id("WRK", "artworks")
        
        # Process and upload images
        processed_images = []
        main_image_url = None
        thumbnail_urls = []
        dominant_color = None
        
        for idx, image_file in enumerate(images):
            # Process image
            processed = await image_service.process_and_save_image(
                file=image_file,
                output_format="JPEG",
                sizes=[ImageSize.THUMBNAIL, ImageSize.MEDIUM, ImageSize.LARGE],
                convert_heic=True,
            )
            
            # Get dominant color from first image
            if idx == 0:
                dominant_color = processed["dominant_color"]
            
            # Upload all sizes
            uploaded_sizes = {}
            for size_name, size_data in processed["images"].items():
                size_data["data"].seek(0)
                
                # Create UploadFile-like object
                class BytesIOUploadFile:
                    def __init__(self, bytes_io, filename, content_type="image/jpeg"):
                        self.bytes_io = bytes_io
                        self.filename = filename
                        self.content_type = content_type
                        self.file = bytes_io
                    
                    async def read(self):
                        return self.bytes_io.read()
                    
                    def seek(self, position):
                        return self.bytes_io.seek(position)
                
                original_filename = image_file.filename or "image.jpg"
                name, ext = original_filename.rsplit(".", 1) if "." in original_filename else (original_filename, "jpg")
                size_filename = f"{name}_{size_name}.{ext}"
                
                temp_file = BytesIOUploadFile(
                    size_data["data"],
                    size_filename,
                    content_type="image/jpeg",
                )
                
                # Upload to storage
                upload_result = await storage_service.upload_file(
                    file=temp_file,
                    bucket="artworks",
                    user_id=current_user.id,
                    subfolder=custom_id,
                )
                
                uploaded_sizes[size_name] = upload_result["url"]
                
                # Set main image URL from first image's large size
                if idx == 0 and size_name == "large":
                    main_image_url = upload_result["url"]
                
                # Collect thumbnail URLs
                if size_name == "thumbnail":
                    thumbnail_urls.append(upload_result["url"])
            
            # Store image URLs in artwork_images table (after artwork is created)
            processed_images.append({
                "urls": uploaded_sizes,
                "order": idx,
                "is_main": idx == 0,
            })
        
        # Calculate size_class if not provided
        calculated_size_class = size_class
        if not calculated_size_class:
            # Auto-calculate based on dimensions
            area = width * height
            if area < 1000:  # < 1000 cm²
                calculated_size_class = "XS"
            elif area < 5000:
                calculated_size_class = "S"
            elif area < 15000:
                calculated_size_class = "M"
            elif area < 30000:
                calculated_size_class = "L"
            elif area < 50000:
                calculated_size_class = "XL"
            else:
                calculated_size_class = "XXL"
        
        # Create artwork in database
        artwork_data = {
            "custom_id": custom_id,
            "artist_id": current_user.id,
            "title": title,
            "description": description,
            "story": story,
            "price": str(price),
            "lease_price": str(lease_price) if lease_price else None,
            "dimensions": json.dumps({
                "width": width,
                "height": height,
                "depth": depth,
            }),
            "size_class": calculated_size_class,
            "year": year,
            "medium": medium,
            "support": support,
            "weight": str(weight) if weight else None,
            "has_frame": has_frame,
            "coating": coating,
            "status": "draft",
            "main_image_url": main_image_url,
            "thumbnail_urls": json.dumps(thumbnail_urls),
            "dominant_color": dominant_color,
            "packaging_info": packaging_info,
            "maintenance_info": maintenance_info,
            "created_at": "now()",
            "updated_at": "now()",
        }
        
        artwork_response = admin_client.table("artworks").insert(artwork_data).execute()
        
        if not artwork_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create artwork",
            )
        
        artwork = artwork_response.data[0]
        artwork_id = artwork["id"]
        
        # Store images in artwork_images table
        for img_data in processed_images:
            # Use large size as main image URL
            image_url = img_data["urls"].get("large") or img_data["urls"].get("medium") or list(img_data["urls"].values())[0]
            
            admin_client.table("artwork_images").insert({
                "artwork_id": artwork_id,
                "image_url": image_url,
                "image_order": img_data["order"],
                "is_main": img_data["is_main"],
            }).execute()
        
        # Return created artwork
        return artwork_to_response(artwork, include_artist=True, include_images=True)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create artwork: {str(e)}",
        )


# 4.2 Artwork Listing API
@router.get("/", response_model=ArtworkListResponse)
async def get_artworks(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (draft, published, recalled, sold, rented)"),
    artist_id: Optional[str] = Query(None, description="Filter by artist ID"),
    min_price: Optional[Decimal] = Query(None, description="Minimum price"),
    max_price: Optional[Decimal] = Query(None, description="Maximum price"),
    size_class: Optional[str] = Query(None, description="Filter by size class (XS, S, M, L, XL, XXL)"),
    medium: Optional[str] = Query(None, description="Filter by medium"),
    search: Optional[str] = Query(None, description="Search in title, description, artist name"),
    sort_by: Optional[str] = Query("created_at", description="Sort by: price, created_at, view_count"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc, desc"),
    credentials = Security(security),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
):
    """
    Get list of artworks with pagination, filters, and search
    
    - Pagination support
    - Filtering by status, artist, price range, size, medium
    - Search in title, description, artist name
    - Sorting by price, created_at, view_count
    - Returns total count for pagination
    - Includes artist information and image URLs
    """
    admin_client = get_supabase_admin_client()
    
    try:
        # Build query
        query = admin_client.table("artworks").select("*, artists(id, name, profile_image_url)")
        
        # Apply filters
        if status:
            query = query.eq("status", status)
        else:
            # Default: show published artworks, or user's own artworks if authenticated
            if current_user and current_user.user_type == "artist":
                # Artists can see their own artworks (any status) + published artworks
                # Use separate queries and combine results, or use a more complex filter
                # For now, we'll fetch all and filter in Python (not ideal for large datasets)
                # In production, you might want to use a database function or view
                pass  # Will filter after query
            else:
                # Others only see published artworks
                query = query.eq("status", "published")
        
        if artist_id:
            query = query.eq("artist_id", artist_id)
        
        if min_price is not None:
            query = query.gte("price", str(min_price))
        
        if max_price is not None:
            query = query.lte("price", str(max_price))
        
        if size_class:
            query = query.eq("size_class", size_class)
        
        if medium:
            query = query.ilike("medium", f"%{medium}%")
        
        if search:
            # Search in title, description
            query = query.or_(f"title.ilike.%{search}%,description.ilike.%{search}%")
        
        # Apply sorting
        sort_column = sort_by if sort_by in ["price", "created_at", "view_count"] else "created_at"
        sort_desc = sort_order.lower() == "desc"
        query = query.order(sort_column, desc=sort_desc)
        
        # Execute query to get all matching results (for filtering)
        response = query.execute()
        
        # Filter results if needed (for artist's own artworks + published)
        filtered_data = []
        if response.data:
            if current_user and current_user.user_type == "artist" and not status:
                # Filter: own artworks (any status) OR published artworks
                for artwork_data in response.data:
                    if artwork_data["artist_id"] == current_user.id or artwork_data["status"] == "published":
                        filtered_data.append(artwork_data)
            else:
                filtered_data = response.data
        
        # Calculate total
        total = len(filtered_data)
        
        # Apply pagination
        offset = (page - 1) * page_size
        paginated_data = filtered_data[offset:offset + page_size]
        
        artworks = []
        for artwork_data in paginated_data:
            artworks.append(artwork_to_response(artwork_data, include_artist=True, include_images=False))
        
        total_pages = (total + page_size - 1) // page_size
        
        return ArtworkListResponse(
            items=artworks,
            total=total,
        page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get artwork list: {str(e)}",
        )


# 4.3 Artwork Detail API
@router.get("/{artwork_id}", response_model=ArtworkResponse)
async def get_artwork(
    artwork_id: str,
    credentials = Security(security),
    current_user: Optional[CurrentUser] = Depends(get_current_user),
):
    """
    Get artwork by ID
    
    Returns full artwork details including:
    - All images
    - Artist profile
    - Increments view_count
    - Handles published vs draft visibility
    """
    admin_client = get_supabase_admin_client()
    
    try:
        # Get artwork
        response = admin_client.table("artworks").select("*").eq("id", artwork_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found",
            )
        
        artwork = response.data[0]
        
        # Check visibility
        is_owner = current_user and current_user.user_type == "artist" and current_user.id == artwork["artist_id"]
        is_published = artwork["status"] == "published"
        
        if not is_published and not is_owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found",
            )
        
        # Increment view_count (only for published artworks viewed by non-owners)
        if is_published and not is_owner:
            admin_client.table("artworks").update({
                "view_count": artwork.get("view_count", 0) + 1,
            }).eq("id", artwork_id).execute()
            artwork["view_count"] = artwork.get("view_count", 0) + 1
        
        return artwork_to_response(artwork, include_artist=True, include_images=True)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get artwork: {str(e)}",
        )


# 4.4 Artwork Update API
@router.put("/{artwork_id}", response_model=ArtworkResponse)
async def update_artwork(
    artwork_id: str,
    request: ArtworkUpdateRequest,
    credentials = Security(security),
    current_user: CurrentUser = Depends(require_artist),
):
    """
    Update artwork
    
    Requires: Artist authentication (can only update own artworks)
    - Updates artwork fields
    - Handles status changes (draft → published requires validation)
    """
    admin_client = get_supabase_admin_client()
    
    try:
        # Get artwork and verify ownership
        artwork_response = admin_client.table("artworks").select("*").eq("id", artwork_id).execute()
        
        if not artwork_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found",
            )
        
        artwork = artwork_response.data[0]
        
        # Verify ownership
        if artwork["artist_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own artworks",
            )
        
        # Build update data
        updates = {}
        
        if request.title is not None:
            updates["title"] = request.title
        if request.description is not None:
            updates["description"] = request.description
        if request.story is not None:
            updates["story"] = request.story
        if request.price is not None:
            updates["price"] = str(request.price)
        if request.lease_price is not None:
            updates["lease_price"] = str(request.lease_price)
        if request.dimensions is not None:
            updates["dimensions"] = json.dumps({
                "width": request.dimensions.width,
                "height": request.dimensions.height,
                "depth": request.dimensions.depth,
            })
        if request.size_class is not None:
            updates["size_class"] = request.size_class
        if request.year is not None:
            updates["year"] = request.year
        if request.medium is not None:
            updates["medium"] = request.medium
        if request.support is not None:
            updates["support"] = request.support
        if request.weight is not None:
            updates["weight"] = str(request.weight)
        if request.has_frame is not None:
            updates["has_frame"] = request.has_frame
        if request.coating is not None:
            updates["coating"] = request.coating
        if request.packaging_info is not None:
            updates["packaging_info"] = request.packaging_info
        if request.maintenance_info is not None:
            updates["maintenance_info"] = request.maintenance_info
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields specified for update",
            )
        
        updates["updated_at"] = "now()"
        
        # Update artwork
        update_response = admin_client.table("artworks").update(updates).eq("id", artwork_id).execute()
        
        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update artwork",
            )
        
        updated_artwork = update_response.data[0]
        
        return artwork_to_response(updated_artwork, include_artist=True, include_images=True)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update artwork: {str(e)}",
        )


# 4.5 Artwork Deletion/Recall API
@router.delete("/{artwork_id}")
async def delete_artwork(
    artwork_id: str,
    hard_delete: bool = Query(False, description="Permanently delete (default: soft delete/recall)"),
    credentials = Security(security),
    current_user: CurrentUser = Depends(require_artist),
):
    """
    Delete or recall artwork
    
    Requires: Artist authentication (can only delete own artworks)
    - Soft delete: Sets status to 'recalled' (default)
    - Hard delete: Permanently removes from database
    - Handles related data (favorites, assignments, orders via CASCADE)
    - Deletes associated images from storage (for hard delete)
    """
    admin_client = get_supabase_admin_client()
    storage_service = get_storage_service()
    
    try:
        # Get artwork and verify ownership
        artwork_response = admin_client.table("artworks").select("*").eq("id", artwork_id).execute()
        
        if not artwork_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found",
            )
        
        artwork = artwork_response.data[0]
        
        # Verify ownership
        if artwork["artist_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own artworks",
            )
        
        if hard_delete:
            # Hard delete: Get image URLs before deletion
            images_response = admin_client.table("artwork_images").select("image_url").eq("artwork_id", artwork_id).execute()
            
            # Delete artwork (CASCADE will handle artwork_images)
            admin_client.table("artworks").delete().eq("id", artwork_id).execute()
            
            # Delete images from storage
            if images_response.data:
                for img in images_response.data:
                    image_url = img["image_url"]
                    # Extract path from URL and delete
                    # Note: This is a simplified approach - you may need to parse the URL properly
                    try:
                        # Extract path from Supabase storage URL
                        # URL format: https://[project].supabase.co/storage/v1/object/public/artworks/[path]
                        if "/artworks/" in image_url:
                            path = image_url.split("/artworks/")[1].split("?")[0]
                            await storage_service.delete_file("artworks", path)
                    except Exception:
                        pass  # Ignore storage deletion errors
            
            return {
                "message": "Artwork permanently deleted",
                "detail": "Artwork and related data have been permanently deleted.",
            }
        else:
            # Soft delete: Set status to 'recalled'
            admin_client.table("artworks").update({
                "status": "recalled",
                "updated_at": "now()",
            }).eq("id", artwork_id).execute()
            
            return {
                "message": "Artwork recalled",
                "detail": "Artwork status has been changed to 'recalled'.",
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete artwork: {str(e)}",
        )


# 4.6 Artwork Publishing Status API
@router.post("/{artwork_id}/publish", response_model=ArtworkResponse)
async def publish_artwork(
    artwork_id: str,
    credentials = Security(security),
    current_user: CurrentUser = Depends(require_artist),
):
    """
    Publish artwork
    
    Changes status from 'draft' to 'published'
    Sets published_at timestamp
    Validates artwork completeness before publishing
    """
    admin_client = get_supabase_admin_client()
    
    try:
        # Get artwork and verify ownership
        artwork_response = admin_client.table("artworks").select("*").eq("id", artwork_id).execute()
        
        if not artwork_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found",
            )
        
        artwork = artwork_response.data[0]
        
        # Verify ownership
        if artwork["artist_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only publish your own artworks",
            )
        
        # Validate artwork completeness
        required_fields = ["title", "price", "main_image_url"]
        missing_fields = [field for field in required_fields if not artwork.get(field)]
        
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The following fields are required for publishing: {', '.join(missing_fields)}",
            )
        
        # Check if already published
        if artwork["status"] == "published":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This artwork is already published",
            )
        
        # Publish artwork
        update_response = admin_client.table("artworks").update({
            "status": "published",
            "published_at": "now()",
            "updated_at": "now()",
        }).eq("id", artwork_id).execute()
        
        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to publish artwork",
            )
        
        updated_artwork = update_response.data[0]
        
        return artwork_to_response(updated_artwork, include_artist=True, include_images=True)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish artwork: {str(e)}",
        )


@router.post("/{artwork_id}/unpublish", response_model=ArtworkResponse)
async def unpublish_artwork(
    artwork_id: str,
    credentials = Security(security),
    current_user: CurrentUser = Depends(require_artist),
):
    """
    Unpublish artwork
    
    Changes status from 'published' back to 'draft'
    """
    admin_client = get_supabase_admin_client()
    
    try:
        # Get artwork and verify ownership
        artwork_response = admin_client.table("artworks").select("*").eq("id", artwork_id).execute()
        
        if not artwork_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artwork not found",
            )
        
        artwork = artwork_response.data[0]
        
        # Verify ownership
        if artwork["artist_id"] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only unpublish your own artworks",
            )
        
        # Check if already draft
        if artwork["status"] == "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This artwork is already a draft",
            )
        
        # Unpublish artwork
        update_response = admin_client.table("artworks").update({
            "status": "draft",
            "updated_at": "now()",
        }).eq("id", artwork_id).execute()
        
        if not update_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to unpublish artwork",
            )
        
        updated_artwork = update_response.data[0]
        
        return artwork_to_response(updated_artwork, include_artist=True, include_images=True)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unpublish artwork: {str(e)}",
        )
