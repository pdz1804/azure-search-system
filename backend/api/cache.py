from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.cache_service import delete_cache_pattern

cache = APIRouter(prefix="/api/cache", tags=["cache"])


class InvalidateRequest(BaseModel):
    pattern: str


@cache.post("/invalidate")
async def invalidate_cache(req: InvalidateRequest):
    if not req.pattern:
        raise HTTPException(status_code=400, detail="pattern required")
    try:
        await delete_cache_pattern(req.pattern)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
