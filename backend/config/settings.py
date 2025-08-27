"""
Backend configuration settings.
"""

import os
from typing import Optional

# AI Search Service Configuration
AI_SEARCH_BASE_URL: str = os.getenv("AI_SEARCH_BASE_URL", "http://localhost:8000")

# Database Configuration
COSMOS_DB_CONNECTION_STRING: Optional[str] = os.getenv("COSMOS_DB_CONNECTION_STRING")
COSMOS_DB_NAME: str = os.getenv("COSMOS_DB_NAME", "articlehub")

# Redis Configuration
REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))

# Application Configuration
APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT: int = int(os.getenv("APP_PORT", "8001"))
DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
