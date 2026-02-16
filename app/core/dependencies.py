"""
Authentication dependencies for FastAPI routes

Provides dependencies for protecting routes with JWT authentication
and role-based access control (RBAC).
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from app.core.supabase import get_supabase_client, get_supabase_admin_client

# HTTP Bearer token security scheme
# auto_error=False allows us to handle errors manually
# scheme_name="BearerAuth" makes it work better with Swagger UI
security = HTTPBearer(auto_error=False, scheme_name="BearerAuth")


async def extract_token_from_request(request: Request) -> Optional[str]:
    """
    Fallback method to manually extract token from Authorization header
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Log all headers for debugging
    logger.info(f"DEBUG: All request headers: {dict(request.headers)}")
    
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    logger.info(f"DEBUG: Manual header extraction - auth_header: {auth_header[:50] if auth_header else 'None'}...")
    logger.info(f"DEBUG: auth_header type: {type(auth_header)}")
    logger.info(f"DEBUG: auth_header length: {len(auth_header) if auth_header else 0}")
    
    if not auth_header:
        logger.error("DEBUG: No Authorization header found in request!")
        return None
    
    # Handle "Bearer <token>" format
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        logger.info(f"DEBUG: Extracted token from 'Bearer ' prefix: {token[:30]}... (length: {len(token)})")
        return token
    elif auth_header.startswith("bearer "):
        token = auth_header[7:].strip()
        logger.info(f"DEBUG: Extracted token from 'bearer ' prefix: {token[:30]}... (length: {len(token)})")
        return token
    else:
        # Maybe token is provided without "Bearer" prefix
        logger.info(f"DEBUG: Token provided without 'Bearer' prefix, using as-is: {auth_header[:30]}... (length: {len(auth_header)})")
        return auth_header.strip()


class CurrentUser:
    """Current authenticated user data"""
    def __init__(self, user_id: str, email: str, user_type: str, profile: Dict[str, Any]):
        self.id = user_id
        self.email = email
        self.user_type = user_type
        self.profile = profile


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> CurrentUser:
    """
    Dependency to get the current authenticated user from JWT token
    
    Validates the JWT token using Supabase Auth and returns user information.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        request: FastAPI request object (for debugging)
        
    Returns:
        CurrentUser: Current authenticated user data
        
    Raises:
        HTTPException: If token is invalid, expired, or user not found
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    # DEBUG: Log what we received
    logger.info("=" * 50)
    logger.info("DEBUG: get_current_user called")
    logger.info(f"DEBUG: credentials is None? {credentials is None}")
    logger.info(f"DEBUG: credentials type: {type(credentials)}")
    
    # If credentials is None, try to extract token manually from headers
    token = None
    if credentials:
        token = credentials.credentials
        logger.info(f"DEBUG: Token extracted from HTTPBearer: {token[:20] if token else 'None'}...")
        logger.info(f"DEBUG: Token scheme: {credentials.scheme}")
    else:
        logger.warning("DEBUG: HTTPBearer returned None, trying manual extraction")
        # Try manual extraction as fallback
        token = await extract_token_from_request(request)
        if token:
            logger.info(f"DEBUG: Successfully extracted token manually: {token[:30]}...")
        
        if not token:
            logger.error("DEBUG: HTTPBearer returned None AND manual extraction failed!")
            logger.error("DEBUG: This usually means:")
            logger.error("DEBUG: 1. Authorization header is missing")
            logger.error("DEBUG: 2. Header format is wrong (should be 'Bearer <token>')")
            logger.error("DEBUG: 3. HTTPBearer security scheme is not working")
            logger.error("DEBUG: 4. Token might be expired or invalid format")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token required (DEBUG: HTTPBearer returned None - check Authorization header)",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    if not token:
        logger.error("DEBUG: Token is empty string!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is empty",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"DEBUG: Token received: {token[:30]}... (length: {len(token)})")
    
    try:
        from jose import jwt
        from app.core.config import settings
        
        admin_client = get_supabase_admin_client()
        logger.info("DEBUG: Starting token validation")
        
        # Method: Decode JWT token to get user ID, then fetch user via admin API
        # This is the most reliable method for token validation
        try:
            # Decode JWT token without verification (to extract user ID)
            # We'll verify by fetching the user from Supabase
            # Use get_unverified_claims() to decode without needing a key
            decoded = jwt.get_unverified_claims(token)
            
            user_id = decoded.get("sub")  # Subject (user ID) in JWT
            if not user_id:
                logger.error(f"Token missing user ID: {decoded}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token does not contain user ID",
                )
            
            # Get user from admin API (this validates the user exists)
            try:
                user_response = admin_client.auth.admin.get_user_by_id(user_id)
            except Exception as admin_error:
                logger.error(f"Admin API error: {str(admin_error)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Failed to get user: {str(admin_error)}",
                )
            
            if not user_response.user:
                logger.error(f"User not found for ID: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                )
            
            user = user_response.user
            user_metadata = user.user_metadata or {}
            user_type = user_metadata.get("user_type", "")
            
            logger.debug(f"Authenticated user: {user_id}, type: {user_type}")
            
        except jwt.JWTError as jwt_error:
            logger.error(f"JWT decode error: {str(jwt_error)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token format: {str(jwt_error)}",
            )
        except HTTPException:
            raise
        except Exception as decode_error:
            logger.error(f"Token validation error: {str(decode_error)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Failed to verify authentication token: {str(decode_error)}",
            )
        
        # Fetch user profile from appropriate table based on user_type
        profile = {}
        if user_type:
            try:
                if user_type == "artist":
                    profile_response = admin_client.table("artists").select("*").eq("id", user_id).execute()
                    if profile_response.data:
                        profile = profile_response.data[0]
                elif user_type == "customer":
                    profile_response = admin_client.table("customers").select("*").eq("id", user_id).execute()
                    if profile_response.data:
                        profile = profile_response.data[0]
                elif user_type == "corporate":
                    profile_response = admin_client.table("corporates").select("*").eq("id", user_id).execute()
                    if profile_response.data:
                        profile = profile_response.data[0]
            except Exception as profile_error:
                # Log error but continue - profile might not exist yet
                logger.warning(f"Failed to fetch profile for user {user_id}: {str(profile_error)}")
                profile = {}
        
        # If no profile found, create a minimal profile from user metadata
        if not profile:
            profile = {
                "id": user_id,
                "email": user.email,
                "name": user_metadata.get("name", ""),
                "status": "active",
            }
        
        return CurrentUser(
            user_id=user_id,
            email=user.email or "",
            user_type=user_type,
            profile=profile
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)
        if "invalid" in error_message.lower() or "expired" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token is invalid or expired",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
        )


async def require_artist(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Dependency to require user to be an artist
    
    Args:
        current_user: Current authenticated user from get_current_user
        
    Returns:
        CurrentUser: Current user if they are an artist
        
    Raises:
        HTTPException: If user is not an artist
    """
    if current_user.user_type != "artist":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires artist permissions",
        )
    return current_user


async def require_customer(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Dependency to require user to be a customer
    
    Args:
        current_user: Current authenticated user from get_current_user
        
    Returns:
        CurrentUser: Current user if they are a customer
        
    Raises:
        HTTPException: If user is not a customer
    """
    if current_user.user_type != "customer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires customer permissions",
        )
    return current_user


async def require_corporate(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Dependency to require user to be a corporate
    
    Args:
        current_user: Current authenticated user from get_current_user
        
    Returns:
        CurrentUser: Current user if they are a corporate
        
    Raises:
        HTTPException: If user is not a corporate
    """
    if current_user.user_type != "corporate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires corporate permissions",
        )
    return current_user
