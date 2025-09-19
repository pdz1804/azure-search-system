import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import asynccontextmanager

from backend.database.cosmos import close_cosmos, connect_cosmos
from backend.config.redis_config import get_redis, close_redis
from backend.api.article import articles
from backend.api.file import files
from backend.api.cache import cache
from backend.authentication.routes import auth
from backend.api.user import users
from backend.api.search import search


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_cosmos()
    await get_redis()
    yield
    await close_cosmos()
    await close_redis()


app = FastAPI(title="Article CMS - modular", lifespan=lifespan)

load_dotenv()
FRONTEND_URL = os.getenv("FRONTEND_URL", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_URL,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(articles)
app.include_router(auth)
app.include_router(files)
app.include_router(users)
app.include_router(search)
app.include_router(cache)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Backend is running"}


@app.get("/all-environment")
async def all_environment():
    return {"success": True, "data": dict(os.environ)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        lifespan="on"
    )
