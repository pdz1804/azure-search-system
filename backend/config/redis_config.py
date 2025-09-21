import os
import redis.asyncio as redis
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            REDIS_URL,
            password=REDIS_PASSWORD,
            db=REDIS_DB,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None


async def clear_cache_pattern(pattern: str):
    redis_conn = await get_redis()
    keys = await redis_conn.keys(pattern)
    if keys:
        await redis_conn.delete(*keys)
