"""
Custom ID Generator

Generates human-readable IDs like WRK-001, WRK-002, etc.
"""

from typing import Optional
from app.core.supabase import get_supabase_admin_client


def generate_custom_id(prefix: str, table_name: str) -> str:
    """
    Generate custom ID with format: PREFIX-XXX (e.g., WRK-001)
    
    Args:
        prefix: ID prefix (e.g., "WRK" for artworks)
        table_name: Database table name to check for existing IDs
        
    Returns:
        Custom ID string (e.g., "WRK-001")
    """
    admin_client = get_supabase_admin_client()
    
    # Get the highest existing custom_id for this prefix
    # Query: SELECT custom_id FROM table WHERE custom_id LIKE 'PREFIX-%' ORDER BY custom_id DESC LIMIT 1
    try:
        response = admin_client.table(table_name).select("custom_id").like("custom_id", f"{prefix}-%").order("custom_id", desc=True).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            last_id = response.data[0]["custom_id"]
            # Extract number from last ID (e.g., "WRK-001" -> 1)
            try:
                last_number = int(last_id.split("-")[1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
    except Exception:
        # If query fails, start from 1
        next_number = 1
    
    # Format: PREFIX-XXX (3 digits, zero-padded)
    custom_id = f"{prefix}-{next_number:03d}"
    
    return custom_id
