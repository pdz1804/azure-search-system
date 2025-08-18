from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import asynccontextmanager

from backend.database.cosmos import close_cosmos, connect_cosmos
from backend.config.redis_config import get_redis, close_redis
from backend.api.article import articles
from backend.api.file import files
from backend.authentication.routes import auth
from backend.api.user import users

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to databases
    await connect_cosmos()
    await get_redis()  # Initialize Redis connection
    print("✅ Connected to Redis")
    
    yield
    
    # Close connections
    await close_cosmos()
    await close_redis()
    print("🛑 Redis connection closed")

app = FastAPI(title="Article CMS - modular", lifespan=lifespan)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả HTTP methods
    allow_headers=["*"],  # Cho phép tất cả headers
)


app.include_router(articles)
app.include_router(auth)
app.include_router(files)
app.include_router(users)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        lifespan="on"
    )
