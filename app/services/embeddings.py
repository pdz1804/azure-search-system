"""
Embedding abstraction supporting OpenAI and Hugging Face (SentenceTransformers).
- Resolve embedding dimension for index creation.
- Provide a simple .encode(text) -> List[float]
"""

from __future__ import annotations
from typing import List, Optional
import os

from config.settings import SETTINGS

# Conditional imports (lazy) to avoid heavy startup if not needed
_openai = None
_st_model = None

# Common known OpenAI dims for convenience (avoid API calls during index creation)
_OPENAI_DIMS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    # add more if you use them
}

def resolve_embedding_dim() -> int:
    """Return the embedding dimension (from env override, model metadata, or known defaults)."""
    print("🧮 Resolving embedding dimension...")
    
    if SETTINGS.embedding_dim_env and SETTINGS.embedding_dim_env.strip():
        dim = int(SETTINGS.embedding_dim_env)
        print(f"✅ Using dimension from environment: {dim}")
        return dim

    if SETTINGS.embedding_provider == "openai":
        dim = _OPENAI_DIMS.get(SETTINGS.embedding_model, 1536)
        print(f"✅ Using OpenAI model '{SETTINGS.embedding_model}' dimension: {dim}")
        return dim
    else:
        print(f"🤗 Loading HuggingFace model '{SETTINGS.hf_model_name}' to get dimension...")
        # HF: load model just to read dimension (only once)
        global _st_model
        if _st_model is None:
            from sentence_transformers import SentenceTransformer
            _st_model = SentenceTransformer(SETTINGS.hf_model_name)
            print(f"✅ HuggingFace model loaded successfully")
        
        dim = int(_st_model.get_sentence_embedding_dimension())
        print(f"✅ HuggingFace model dimension: {dim}")
        return dim

def _ensure_openai():
    global _openai
    if _openai is None:
        print("🔑 Initializing OpenAI client...")
        from openai import OpenAI
        kwargs = {"api_key": SETTINGS.openai_key}
        if SETTINGS.openai_base_url:
            kwargs["base_url"] = SETTINGS.openai_base_url
            print(f"🌐 Using custom OpenAI base URL: {SETTINGS.openai_base_url}")
        _openai = OpenAI(**kwargs)
        print("✅ OpenAI client initialized")
    return _openai

def _ensure_st():
    global _st_model
    if _st_model is None:
        print(f"🤗 Loading SentenceTransformer model: {SETTINGS.hf_model_name}")
        from sentence_transformers import SentenceTransformer
        _st_model = SentenceTransformer(SETTINGS.hf_model_name)
        print("✅ SentenceTransformer model loaded")
    return _st_model

def encode(text: str) -> List[float]:
    """
    Generate a single embedding vector for a text string using the configured provider.
    """
    if not text or not text.strip():
        print("⚠️ Empty text provided for encoding")
        text = " "  # Fallback to avoid API errors
    
    text_preview = text[:50] + "..." if len(text) > 50 else text
    print(f"🧮 Encoding text with {SETTINGS.embedding_provider}: '{text_preview}'")
    
    try:
        if SETTINGS.embedding_provider == "openai":
            cli = _ensure_openai()
            # Trim to be safe (if extremely long). Chunking is a future enhancement.
            truncated_text = text[:100_000]
            if len(text) > 100_000:
                print(f"⚠️ Text truncated from {len(text)} to 100,000 characters")
            
            resp = cli.embeddings.create(model=SETTINGS.embedding_model, input=truncated_text)
            embedding = resp.data[0].embedding
            print(f"✅ OpenAI embedding generated (dim={len(embedding)})")
            return embedding
        else:
            model = _ensure_st()
            # normalize_embeddings=True gives cosine-friendly vectors
            import numpy as np
            vec = model.encode(text or "", normalize_embeddings=True)
            embedding = vec.astype(float).tolist()
            print(f"✅ HuggingFace embedding generated (dim={len(embedding)})")
            return embedding
            
    except Exception as e:
        print(f"❌ Embedding generation failed: {e}")
        raise
