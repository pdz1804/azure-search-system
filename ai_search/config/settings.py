"""
Configuration Settings Management

This module handles centralized configuration for the Azure AI Search integration.
It loads settings from environment variables with sensible defaults when possible.

Features:
- Type-safe settings with dataclass representation
- Automatic environment variable loading with dotenv support
- Grouped configuration (search, cosmos, embeddings, weights)
- Clear documentation of all expected environment variables
- Helper functions for parsing special types (bool, float, etc.)

Usage:
    from config.settings import SETTINGS
    
    # Access settings as typed properties
    endpoint = SETTINGS.search_endpoint
    weights = (SETTINGS.w_semantic, SETTINGS.w_bm25, SETTINGS.w_vector, SETTINGS.w_business)

Required Environment Variables:
    AZURE_SEARCH_ENDPOINT: URL for Azure AI Search service
    AZURE_SEARCH_KEY: API key for Azure AI Search
    COSMOS_ENDPOINT: URL for Cosmos DB account
    COSMOS_KEY: Key for Cosmos DB account
"""

from dataclasses import dataclass
import os
from dotenv import load_dotenv
load_dotenv()

def _get_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y"}

@dataclass(frozen=True)
class Settings:
    # Azure AI Search settings
    search_endpoint: str = os.environ["AZURE_SEARCH_ENDPOINT"]  # Required: Full URL to search service
    search_key: str = os.environ["AZURE_SEARCH_KEY"]  # Required: Admin API key

    # Cosmos DB settings
    cosmos_endpoint: str = os.environ["COSMOS_ENDPOINT"]  # Required: Full URL to Cosmos DB account
    cosmos_key: str = os.environ["COSMOS_KEY"]  # Required: Primary or secondary key
    cosmos_db: str = os.environ.get("COSMOS_DB", "blogs")  # Database name
    cosmos_articles: str = os.environ.get("COSMOS_ARTICLES", "articles")  # Articles container
    cosmos_users: str = os.environ.get("COSMOS_USERS", "users")  # Users container

    # Embeddings configuration
    embedding_provider: str = os.environ.get("EMBEDDING_PROVIDER", "openai").lower()  # "openai" or "hf"
    embedding_model: str = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")  # OpenAI model name
    hf_model_name: str = os.environ.get("HF_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")  # Hugging Face model
    embedding_dim_env: str | None = os.environ.get("EMBEDDING_DIM")  # Optional override for embedding dimension
    enable_embeddings: bool = _get_bool("ENABLE_EMBEDDINGS", True)  # Toggle vector search

    # OpenAI API configuration
    openai_key: str = os.environ.get("OPENAI_API_KEY", "")  # OpenAI API key or Azure OpenAI key
    openai_base_url: str | None = os.environ.get("OPENAI_BASE_URL")  # For Azure OpenAI endpoints
    openai_api_version: str | None = os.environ.get("OPENAI_API_VERSION")  # For Azure OpenAI API version
    
    # Azure OpenAI specific settings for indexer skills
    azure_openai_endpoint: str = os.environ.get("AZURE_OPENAI_ENDPOINT", "")  # Azure OpenAI resource endpoint
    azure_openai_key: str = os.environ.get("AZURE_OPENAI_API_KEY", "")  # Azure OpenAI API key
    azure_openai_deployment: str = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "2024-12-01-preview")  # Deployment name
    azure_openai_model_name: str = os.environ.get("AZURE_OPENAI_MODELNAME", "text-embedding-3-small")  # Model name for skillsets
    azure_openai_api_version: str = os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")  # API version for skillsets
    
    # Score weights for articles search (must sum to 1.0)
    w_semantic: float = float(os.environ.get("WEIGHT_SEMANTIC", 0.5))  # Semantic search weight
    w_bm25: float = float(os.environ.get("WEIGHT_BM25", 0.3))  # Keyword matching weight
    w_vector: float = float(os.environ.get("WEIGHT_VECTOR", 0.1))  # Vector similarity weight
    w_business: float = float(os.environ.get("WEIGHT_BUSINESS", 0.1))  # Business logic weight

    # Score weights for authors search (must sum to 1.0)
    aw_semantic: float = float(os.environ.get("AUTHORS_WEIGHT_SEMANTIC", 0.6))  # Semantic search weight
    aw_bm25: float = float(os.environ.get("AUTHORS_WEIGHT_BM25", 0.4))  # Keyword matching weight
    aw_vector: float = float(os.environ.get("AUTHORS_WEIGHT_VECTOR", 0.0))  # Vector similarity weight (default off)
    aw_business: float = float(os.environ.get("AUTHORS_WEIGHT_BUSINESS", 0.0))  # Business logic weight (default off)

    # Content freshness parameters for business scoring
    freshness_halflife_days: float = float(os.environ.get("FRESHNESS_HALFLIFE_DAYS", 250))  # Decay rate for content
    freshness_window_days: int = int(os.environ.get("FRESHNESS_WINDOW_DAYS", 365))  # Max time window for scoring

    # Score threshold filtering
    score_threshold: float = float(os.environ.get("SCORE_THRESHOLD", 0.0))  # Minimum score for results
    enable_score_filtering: bool = _get_bool("ENABLE_SCORE_FILTERING", True)  # Enable/disable score threshold filtering

    # Cache functionality removed for simplicity

SETTINGS = Settings()

# Print configuration on module load (only once)
print("⚙️ Configuration loaded:")
print(f"   🔍 Search: {SETTINGS.search_endpoint}")
print(f"   🌌 Cosmos: {SETTINGS.cosmos_db}/{SETTINGS.cosmos_articles}, {SETTINGS.cosmos_db}/{SETTINGS.cosmos_users}")
print(f"   🧮 Embeddings: {SETTINGS.embedding_provider} ({SETTINGS.embedding_model if SETTINGS.embedding_provider == 'openai' else SETTINGS.hf_model_name})")
print(f"   📊 Article weights: sem={SETTINGS.w_semantic}, bm25={SETTINGS.w_bm25}, vec={SETTINGS.w_vector}, biz={SETTINGS.w_business}")
print(f"   👤 Author weights: sem={SETTINGS.aw_semantic}, bm25={SETTINGS.aw_bm25}, vec={SETTINGS.aw_vector}, biz={SETTINGS.aw_business}")
print(f"   📅 Freshness: half-life={SETTINGS.freshness_halflife_days} days, window={SETTINGS.freshness_window_days} days")
print(f"   🎯 Score filtering: threshold={SETTINGS.score_threshold}, enabled={SETTINGS.enable_score_filtering}")
print(f"   🗂️ Cache: disabled for simplicity")

