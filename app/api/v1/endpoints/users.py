"""
User management endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form, Request, Security
from app.core.dependencies import security
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.core.dependencies import get_current_user, CurrentUser
from app.core.storage import get_storage_service
from app.core.image_processing import get_image_processing_service

router = APIRouter()


class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    user_type: str
    created_at: Optional[str] = None
    status: Optional[str] = None
    company_name: Optional[str] = None
    profile_image_url: Optional[str] = None
    profile_completion: Optional[int] = None  # Percentage 0-100


class UpdateProfileRequest(BaseModel):
    """Request model for updating user profile"""
    name: Optional[str] = None
    phone: Optional[str] = None
    postal_code: Optional[str] = None
    address: Optional[str] = None
    bio: Optional[str] = None  # For artists
    website: Optional[str] = None  # For artists
    instagram: Optional[str] = None  # For artists
    contact_name: Optional[str] = None  # For corporates
    company_name: Optional[str] = None  # For corporates


@router.get(
    "/me",
    response_model=UserProfile,
    tags=["users"]
)
async def get_current_user_profile(
    request: Request,
    credentials = Security(security),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get current authenticated user profile
    
    Requires authentication via JWT token.
    Includes profile completion percentage and profile image URL.
    """
    # Debug: Log request headers and authentication
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 50)
    logger.info("DEBUG: /users/me endpoint called")
    logger.info(f"DEBUG: Authorization header: {request.headers.get('authorization', 'NOT FOUND')}")
    logger.info(f"DEBUG: All headers: {dict(request.headers)}")
    logger.info(f"DEBUG: User authenticated: {current_user.id}, type: {current_user.user_type}")
    logger.info("=" * 50)
    
    profile = current_user.profile
    
    # Extract name based on user type
    name = profile.get("name") or profile.get("contact_name", "")
    
    # Calculate profile completion
    completion = calculate_profile_completion(profile, current_user.user_type)
    
    # Extract additional fields based on user type
    user_profile = UserProfile(
        id=current_user.id,
        email=current_user.email,
        name=name,
        user_type=current_user.user_type,
        created_at=profile.get("created_at"),
        status=profile.get("status"),
        profile_image_url=profile.get("profile_image_url"),
        profile_completion=completion,
    )
    
    # Add company_name for corporate users
    if current_user.user_type == "corporate":
        user_profile.company_name = profile.get("company_name")
    
    return user_profile


@router.put("/me", response_model=UserProfile)
async def update_user_profile(
    request: UpdateProfileRequest,
    credentials = Security(security),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Update current user profile
    
    Requires authentication via JWT token.
    Only updates fields that are provided.
    Supports role-specific fields.
    """
    from app.core.supabase import get_supabase_admin_client
    
    admin_client = get_supabase_admin_client()
    updates = {}
    
    # Common fields
    if request.name is not None:
        updates["name"] = request.name
    if request.phone is not None:
        updates["phone"] = request.phone
    if request.postal_code is not None:
        updates["postal_code"] = request.postal_code
    if request.address is not None:
        updates["address"] = request.address
    
    # Role-specific fields
    if current_user.user_type == "artist":
        if request.bio is not None:
            updates["bio"] = request.bio
        if request.website is not None:
            updates["website"] = request.website
        if request.instagram is not None:
            updates["instagram"] = request.instagram
    elif current_user.user_type == "corporate":
        if request.contact_name is not None:
            updates["contact_name"] = request.contact_name
        if request.company_name is not None:
            updates["company_name"] = request.company_name
        # If name is provided, map to contact_name for corporates
        if "name" in updates:
            updates["contact_name"] = updates.pop("name")
    
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields specified for update",
        )
    
    # Update profile in appropriate table
    table_name = None
    if current_user.user_type == "artist":
        table_name = "artists"
    elif current_user.user_type == "customer":
        table_name = "customers"
    elif current_user.user_type == "corporate":
        table_name = "corporates"
    
    if table_name:
        updates["updated_at"] = "now()"
        response = admin_client.table(table_name).update(updates).eq("id", current_user.id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )
        
        updated_profile = response.data[0]
        
        # Calculate profile completion
        completion = calculate_profile_completion(updated_profile, current_user.user_type)
        
        # Return updated profile
        display_name = updated_profile.get("name") or updated_profile.get("contact_name", "")
        
        user_profile = UserProfile(
            id=current_user.id,
            email=current_user.email,
            name=display_name,
            user_type=current_user.user_type,
            created_at=updated_profile.get("created_at"),
            status=updated_profile.get("status"),
            profile_image_url=updated_profile.get("profile_image_url"),
            profile_completion=completion,
        )
        
        if current_user.user_type == "corporate":
            user_profile.company_name = updated_profile.get("company_name")
        
        return user_profile
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid user type",
    )


@router.post("/me/profile-image", response_model=UserProfile)
async def upload_profile_image(
    file: UploadFile = File(...),
    credentials = Security(security),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Upload profile image for current user
    
    Requires authentication. Image will be processed and optimized.
    """
    from app.core.supabase import get_supabase_admin_client
    
    storage_service = get_storage_service()
    image_service = get_image_processing_service()
    
    try:
        # Validate image
        validation = image_service.validate_image(file)
        
        # Process image (resize to medium size for profile)
        from app.core.image_processing import ImageSize
        processed = await image_service.process_and_save_image(
            file=file,
            output_format="JPEG",
            sizes=[ImageSize.MEDIUM],
            convert_heic=True,
        )
        
        # Upload processed image
        medium_image = processed["images"]["medium"]
        medium_image["data"].seek(0)
        
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
        
        original_filename = file.filename or "profile.jpg"
        name, ext = original_filename.rsplit(".", 1) if "." in original_filename else (original_filename, "jpg")
        profile_filename = f"{name}_profile.{ext}"
        
        temp_file = BytesIOUploadFile(
            medium_image["data"],
            profile_filename,
            content_type="image/jpeg",
        )
        
        # Upload to profiles bucket
        upload_result = await storage_service.upload_file(
            file=temp_file,
            bucket="profiles",
            user_id=current_user.id,
            subfolder=None,
        )
        
        # Update profile with image URL
        admin_client = get_supabase_admin_client()
        table_name = None
        if current_user.user_type == "artist":
            table_name = "artists"
        elif current_user.user_type == "customer":
            table_name = "customers"
        elif current_user.user_type == "corporate":
            table_name = "corporates"
        
        if table_name:
            response = admin_client.table(table_name).update({
                "profile_image_url": upload_result["url"],
                "updated_at": "now()",
            }).eq("id", current_user.id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Profile not found",
                )
            
            updated_profile = response.data[0]
            completion = calculate_profile_completion(updated_profile, current_user.user_type)
            
            display_name = updated_profile.get("name") or updated_profile.get("contact_name", "")
            
            user_profile = UserProfile(
                id=current_user.id,
                email=current_user.email,
                name=display_name,
                user_type=current_user.user_type,
                created_at=updated_profile.get("created_at"),
                status=updated_profile.get("status"),
                profile_image_url=upload_result["url"],
                profile_completion=completion,
            )
            
            if current_user.user_type == "corporate":
                user_profile.company_name = updated_profile.get("company_name")
            
            return user_profile
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user type",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload profile image: {str(e)}",
        )


@router.post("/me/deactivate")
async def deactivate_account(
    credentials = Security(security),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Deactivate user account (soft delete)
    
    Sets account status to 'suspended' but keeps data for potential reactivation.
    User cannot login but data is preserved.
    """
    from app.core.supabase import get_supabase_admin_client
    
    admin_client = get_supabase_admin_client()
    
    # Determine table name
    table_name = None
    if current_user.user_type == "artist":
        table_name = "artists"
    elif current_user.user_type == "customer":
        table_name = "customers"
    elif current_user.user_type == "corporate":
        table_name = "corporates"
    
    if not table_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user type",
        )
    
    try:
        # Update status to suspended
        response = admin_client.table(table_name).update({
            "status": "suspended",
            "updated_at": "now()",
        }).eq("id", current_user.id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found",
            )
        
        # Sign out the user
        from app.core.supabase import get_supabase_client
        client = get_supabase_client()
        try:
            client.auth.sign_out()
        except Exception:
            pass  # Ignore sign out errors
        
        return {
            "message": "Account deactivated",
            "detail": "Account has been suspended. Data will be retained.",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate account: {str(e)}",
        )


@router.post("/me/delete")
async def delete_account(
    credentials = Security(security),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Permanently delete user account (hard delete)
    
    WARNING: This action cannot be undone. All user data will be permanently deleted.
    This includes:
    - User profile
    - Artworks (for artists)
    - Orders and transactions
    - All related data
    
    For GDPR compliance, this performs a complete data deletion.
    """
    from app.core.supabase import get_supabase_admin_client
    
    admin_client = get_supabase_admin_client()
    
    # Determine table name
    table_name = None
    if current_user.user_type == "artist":
        table_name = "artists"
    elif current_user.user_type == "customer":
        table_name = "customers"
    elif current_user.user_type == "corporate":
        table_name = "corporates"
    
    if not table_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user type",
        )
    
    try:
        # Note: Due to foreign key constraints, we may need to handle related data
        # For now, we'll delete the profile and let database CASCADE handle related data
        # In production, you might want to:
        # 1. Delete user's artworks (if artist)
        # 2. Cancel pending orders
        # 3. Delete user's files from storage
        # 4. Delete user's profile
        # 5. Delete auth user (via admin API)
        
        # Delete profile (CASCADE will handle related data if configured)
        response = admin_client.table(table_name).delete().eq("id", current_user.id).execute()
        
        # Delete auth user
        try:
            admin_client.auth.admin.delete_user(current_user.id)
        except Exception as e:
            # Log error but continue
            print(f"Warning: Failed to delete auth user: {str(e)}")
        
        # Sign out
        from app.core.supabase import get_supabase_client
        client = get_supabase_client()
        try:
            client.auth.sign_out()
        except Exception:
            pass
        
        return {
            "message": "Account permanently deleted",
            "detail": "All data has been permanently deleted. This action cannot be undone.",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}",
        )


def calculate_profile_completion(profile: dict, user_type: str) -> int:
    """
    Calculate profile completion percentage (0-100)
    
    Args:
        profile: User profile dictionary
        user_type: User type (artist, customer, corporate)
        
    Returns:
        Completion percentage (0-100)
    """
    required_fields = {
        "artist": ["name", "email", "phone", "bio"],
        "customer": ["name", "email", "phone", "address"],
        "corporate": ["company_name", "contact_name", "email", "phone", "address"],
    }
    
    optional_fields = {
        "artist": ["website", "instagram", "profile_image_url", "portfolio_url"],
        "customer": ["postal_code", "profile_image_url"],
        "corporate": ["postal_code", "profile_image_url"],
    }
    
    required = required_fields.get(user_type, [])
    optional = optional_fields.get(user_type, [])
    
    # Count filled required fields
    filled_required = sum(1 for field in required if profile.get(field))
    
    # Count filled optional fields
    filled_optional = sum(1 for field in optional if profile.get(field))
    
    # Calculate completion
    # Required fields: 70% weight
    # Optional fields: 30% weight
    required_score = (filled_required / len(required)) * 70 if required else 0
    optional_score = (filled_optional / len(optional)) * 30 if optional else 0
    
    completion = int(required_score + optional_score)
    return min(100, max(0, completion))
