import json
import hashlib
from typing import Any, Optional
from backend.config.redis_config import get_redis

# Cache keys
CACHE_KEYS = {
    "articles_home": "articles:home",
    "articles_popular": "articles:popular", 
    "articles_recent": "articles:recent",
    "article_detail": "article:detail:{article_id}",
    "user_articles": "user:articles:{user_id}"
}

# Cache TTL (Time To Live) in seconds
CACHE_TTL = {
    "home": 300,  # 5 minutes
    "popular": 600,  # 10 minutes
    "recent": 180,  # 3 minutes
    "detail": 900,  # 15 minutes
    "user_articles": 240  # 4 minutes
}

async def get_cache(key: str) -> Optional[Any]:
    """Get data from cache"""
    try:
        redis = await get_redis()
        cached_data = await redis.get(key)
        if cached_data:
            return json.loads(cached_data)
        return None
    except Exception as e:
        print(f"Cache get error: {e}")
        return None

async def set_cache(key: str, data: Any, ttl: int = 300) -> bool:
    """Set data to cache with TTL"""
    try:
        redis = await get_redis()
        serialized_data = json.dumps(data, default=str)
        await redis.set(key, serialized_data, ex=ttl)
        return True
    except Exception as e:
        print(f"Cache set error: {e}")
        return False

async def delete_cache(key: str) -> bool:
    """Delete cache by key"""
    try:
        redis = await get_redis()
        await redis.delete(key)
        return True
    except Exception as e:
        print(f"Cache delete error: {e}")
        return False

async def delete_cache_pattern(pattern: str) -> bool:
    """Delete cache by pattern"""
    try:
        redis = await get_redis()
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)
        return True
    except Exception as e:
        print(f"Cache pattern delete error: {e}")
        return False

def generate_cache_key(base_key: str, **params) -> str:
    """Generate cache key with parameters"""
    if not params:
        return base_key
    
    # Sort parameters for consistent key generation
    sorted_params = sorted(params.items())
    param_string = "&".join([f"{k}={v}" for k, v in sorted_params])
    
    # Create hash for long parameter strings
    if len(param_string) > 50:
        param_hash = hashlib.md5(param_string.encode()).hexdigest()
        return f"{base_key}:{param_hash}"
    
    return f"{base_key}:{param_string}"
