"""
Supabase client configuration
"""

from supabase import create_client, Client
from app.core.config import settings
from typing import Optional

# Lazy-loaded singleton instances
_supabase_client: Optional[Client] = None
_supabase_admin: Optional[Client] = None


def get_supabase_client() -> Client:
    """
    Get Supabase client instance (lazy-loaded singleton)
    
    Returns:
        Client: Supabase client
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase_client


def get_supabase_admin_client() -> Client:
    """
    Get Supabase admin client with service role key (lazy-loaded singleton)
    
    Returns:
        Client: Supabase admin client
    """
    global _supabase_admin
    if _supabase_admin is None:
        _supabase_admin = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_admin


# For backward compatibility, you can also use:
# from app.core.supabase import get_supabase_client
# client = get_supabase_client()
