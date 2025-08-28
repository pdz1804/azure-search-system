import json
import hashlib
from typing import Any, Optional, Dict, List
from backend.config.redis_config import get_redis

# Cache keys - Base patterns without app_id
CACHE_KEYS = {
    "articles_home": "articles:home",
    "articles_popular": "articles:popular",
    "article_detail": "article:detail:{article_id}",
    "user_articles": "user:articles:{user_id}",
    "user_detail": "user:detail:{user_id}",
    "homepage_statistics": "homepage:statistics",
    "homepage_categories": "homepage:categories",
    "articles_author": "articles:author:{author_id}",
    "authors": "authors"
}

# Cache TTL (Time To Live) in seconds
CACHE_TTL = {
    "home": 300,  # 5 minutes
    "popular": 600,  # 10 minutes
    "recent": 180,  # 3 minutes
    "detail": 900,  # 15 minutes
    "user_articles": 240,  # 4 minutes
    "user_detail": 600,  # 10 minutes
    "statistics": 180,  # 3 minutes
    "categories": 300,  # 5 minutes
    "author": 240,  # 4 minutes
    "authors": 180  # 3 minutes
}

def build_cache_key(base_key: str, app_id: Optional[str] = None, **params) -> str:
    """Build cache key with app_id and parameters"""
    # Add app_id to the key if provided
    if app_id:
        key_with_app = f"{base_key}:app_{app_id}"
    else:
        key_with_app = base_key
    
    # Add other parameters
    if params:
        return generate_cache_key(key_with_app, **params)
    return key_with_app

def build_cache_pattern(base_pattern: str, app_id: Optional[str] = None) -> str:
    """Build cache pattern with app_id"""
    if app_id:
        # Remove existing * if present, add app_id, then add * back
        clean_pattern = base_pattern.rstrip('*')
        return f"{clean_pattern}:app_{app_id}*"
    return base_pattern

async def get_cache(base_key: str, app_id: Optional[str] = None, **params) -> Optional[Any]:
    """Get data from cache with app_id support"""
    try:
        cache_key = build_cache_key(base_key, app_id, **params)
        redis = await get_redis()
        cached_data = await redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        return None
    except Exception as e:
        print(f"Cache get error: {e}")
        return None

async def set_cache(base_key: str, data: Any, app_id: Optional[str] = None, ttl: int = 300, **params) -> bool:
    """Set data to cache with app_id support"""
    try:
        cache_key = build_cache_key(base_key, app_id, **params)
        redis = await get_redis()
        serialized_data = json.dumps(data, default=str)
        await redis.set(cache_key, serialized_data, ex=ttl)
        return True
    except Exception as e:
        print(f"Cache set error: {e}")
        return False

async def delete_cache(base_key: str, app_id: Optional[str] = None, **params) -> bool:
    """Delete cache by key with app_id support"""
    try:
        cache_key = build_cache_key(base_key, app_id, **params)
        redis = await get_redis()
        await redis.delete(cache_key)
        return True
    except Exception as e:
        print(f"Cache delete error: {e}")
        return False

async def delete_cache_pattern(base_pattern: str, app_id: Optional[str] = None) -> bool:
    """Delete cache by pattern with app_id support"""
    try:
        pattern = build_cache_pattern(base_pattern, app_id)
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
