"""
Typed settings loader. Keeps configuration out of business logic.
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
    # Search
    search_endpoint: str = os.environ["AZURE_SEARCH_ENDPOINT"]
    search_key: str = os.environ["AZURE_SEARCH_KEY"]

    # Cosmos
    cosmos_endpoint: str = os.environ["COSMOS_ENDPOINT"]
    cosmos_key: str = os.environ["COSMOS_KEY"]
    cosmos_db: str = os.environ.get("COSMOS_DB", "blogs")
    cosmos_articles: str = os.environ.get("COSMOS_ARTICLES", "articles")
    cosmos_users: str = os.environ.get("COSMOS_USERS", "users")

    # Embeddings provider
    embedding_provider: str = os.environ.get("EMBEDDING_PROVIDER", "openai").lower()  # "openai" or "hf"
    embedding_model: str = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
    hf_model_name: str = os.environ.get("HF_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    embedding_dim_env: str | None = os.environ.get("EMBEDDING_DIM")
    enable_embeddings: bool = _get_bool("ENABLE_EMBEDDINGS", True)

    # OpenAI specifics
    openai_key: str = os.environ.get("OPENAI_API_KEY", "")
    openai_base_url: str | None = os.environ.get("OPENAI_BASE_URL")
    openai_api_version: str | None = os.environ.get("OPENAI_API_VERSION")

    # Weights - articles
    w_semantic: float = float(os.environ.get("WEIGHT_SEMANTIC", 0.5))
    w_bm25: float = float(os.environ.get("WEIGHT_BM25", 0.3))
    w_vector: float = float(os.environ.get("WEIGHT_VECTOR", 0.1))
    w_business: float = float(os.environ.get("WEIGHT_BUSINESS", 0.1))

    # Weights - authors
    aw_semantic: float = float(os.environ.get("AUTHORS_WEIGHT_SEMANTIC", 0.6))
    aw_bm25: float = float(os.environ.get("AUTHORS_WEIGHT_BM25", 0.4))
    aw_vector: float = float(os.environ.get("AUTHORS_WEIGHT_VECTOR", 0.0))
    aw_business: float = float(os.environ.get("AUTHORS_WEIGHT_BUSINESS", 0.0))

    # Freshness
    freshness_halflife_days: float = float(os.environ.get("FRESHNESS_HALFLIFE_DAYS", 250))
    freshness_window_days: int = int(os.environ.get("FRESHNESS_WINDOW_DAYS", 365))

SETTINGS = Settings()

# Print configuration on module load (only once)
print("⚙️ Configuration loaded:")
print(f"   🔍 Search: {SETTINGS.search_endpoint}")
print(f"   🌌 Cosmos: {SETTINGS.cosmos_db}/{SETTINGS.cosmos_articles}, {SETTINGS.cosmos_db}/{SETTINGS.cosmos_users}")
print(f"   🧮 Embeddings: {SETTINGS.embedding_provider} ({SETTINGS.embedding_model if SETTINGS.embedding_provider == 'openai' else SETTINGS.hf_model_name})")
print(f"   📊 Article weights: sem={SETTINGS.w_semantic}, bm25={SETTINGS.w_bm25}, vec={SETTINGS.w_vector}, biz={SETTINGS.w_business}")
print(f"   👤 Author weights: sem={SETTINGS.aw_semantic}, bm25={SETTINGS.aw_bm25}, vec={SETTINGS.aw_vector}, biz={SETTINGS.aw_business}")
print(f"   📅 Freshness: half-life={SETTINGS.freshness_halflife_days} days, window={SETTINGS.freshness_window_days} days")

