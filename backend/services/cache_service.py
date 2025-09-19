import json
import hashlib
from typing import Any, Optional
from backend.config.redis_config import get_redis

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

CACHE_TTL = {
    "home": 300,
    "popular": 600,
    "recent": 180,
    "detail": 900,
    "user_articles": 240,
    "user_detail": 600,
    "statistics": 180,
    "categories": 300,
    "author": 240,
    "authors": 180
}

def build_cache_key(base_key: str, app_id: Optional[str] = None, **params) -> str:
    if app_id:
        key_with_app = f"{base_key}:app_{app_id}"
    else:
        key_with_app = base_key
    
    if params:
        return generate_cache_key(key_with_app, **params)
    return key_with_app

def build_cache_pattern(base_pattern: str, app_id: Optional[str] = None) -> str:
    if app_id:
        clean_pattern = base_pattern.rstrip('*')
        return f"{clean_pattern}:app_{app_id}*"
    return base_pattern

async def get_cache(base_key: str, app_id: Optional[str] = None, **params) -> Optional[Any]:
    try:
        cache_key = build_cache_key(base_key, app_id, **params)
        redis = await get_redis()
        cached_data = await redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        return None
    except Exception as e:
        return None

async def set_cache(base_key: str, data: Any, app_id: Optional[str] = None, ttl: int = 300, **params) -> bool:
    try:
        cache_key = build_cache_key(base_key, app_id, **params)
        redis = await get_redis()
        serialized_data = json.dumps(data, default=str)
        await redis.set(cache_key, serialized_data, ex=ttl)
        return True
    except Exception as e:
        return False

async def delete_cache(base_key: str, app_id: Optional[str] = None, **params) -> bool:
    try:
        cache_key = build_cache_key(base_key, app_id, **params)
        redis = await get_redis()
        await redis.delete(cache_key)
        return True
    except Exception as e:
        return False

async def delete_cache_pattern(base_pattern: str, app_id: Optional[str] = None) -> bool:
    try:
        pattern = build_cache_pattern(base_pattern, app_id)
        redis = await get_redis()
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)
        return True
    except Exception as e:
        return False

def generate_cache_key(base_key: str, **params) -> str:
    if not params:
        return base_key
    
    sorted_params = sorted(params.items())
    param_string = "&".join([f"{k}={v}" for k, v in sorted_params])
    
    if len(param_string) > 50:
        param_hash = hashlib.md5(param_string.encode()).hexdigest()
        return f"{base_key}:{param_hash}"
    
    return f"{base_key}:{param_string}"
