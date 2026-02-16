"""
Redis client configuration
"""

import redis.asyncio as redis
from app.core.config import settings


async def get_redis_client():
    """
    Get Redis client instance
    
    Returns:
        Redis: Redis client
    """
    return await redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


# Create Redis client (will be initialized on startup)
redis_client = None
