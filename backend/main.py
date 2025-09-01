"""Application entrypoint for the backend FastAPI app.

This module configures the application lifespan (connects/disconnects
to external services like Cosmos DB and Redis), CORS settings and
registers the API routers (articles, files, auth, users).

Requests come in to FastAPI -> matched to a router -> handler in
`backend.api.*` which calls service layer functions in
`backend.services.*` which in turn call repository functions in
`backend.repositories.*` that operate on the database containers.
"""

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

load_dotenv()
FRONTEND_URL = os.getenv("FRONTEND_URL", "*").split(",")


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_URL,  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


app.include_router(articles)
app.include_router(auth)
app.include_router(files)
app.include_router(users)
app.include_router(search)
app.include_router(cache)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    return {"status": "healthy", "message": "Backend is running"}
@app.get("/all-environment")
async def all_environment():
    """Get all environment variables."""
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
