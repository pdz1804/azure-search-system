"""
Score fusion: combine semantic, BM25, vector, and business (freshness) scores with configurable weights.
"""

from __future__ import annotations
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
import math

from config.settings import SETTINGS

def _minmax(vs: List[float]) -> Tuple[float, float]:
    """Get min and max values from a list, handling edge cases."""
    if not vs:
        return (0.0, 1.0)
    vmin, vmax = min(vs), max(vs)
    if math.isclose(vmin, vmax):
        return (0.0, 1.0)
    return (vmin, vmax)

def _norm(v: float, bounds: Tuple[float, float]) -> float:
    """Normalize a value to [0,1] using min-max normalization."""
    vmin, vmax = bounds
    if math.isclose(vmin, vmax):
        return 1.0
    return (v - vmin) / (vmax - vmin)

def business_freshness(business_date: datetime | str | None) -> float:
    """
    Calculate business freshness score using exponential decay:
    score = exp(-ln(2) * age_days / half_life)
    - ~1.0 for brand new content
    - ~0.5 at half-life point
    """
    if not business_date:
        print("⚠️ No business date provided, returning freshness score of 0.0")
        return 0.0
    
    try:
        # Debug: show incoming value and type
        # (kept short to avoid huge logs in production)
        print(f"🔎 business_freshness input type={type(business_date).__name__} repr={str(business_date)[:40]}")

        bd = business_date
        # If a dict was passed (e.g., document object), try common timestamp keys
        if isinstance(bd, dict):
            for k in ("business_date", "updated_at", "created_at", "date"):
                if k in bd:
                    bd = bd[k]
                    break

        # If epoch provided as int/float
        if isinstance(bd, (int, float)):
            # Heuristic: if large (>1e12) it's ms
            ts = float(bd)
            if ts > 1e12:
                ts = ts / 1000.0
            bd = datetime.fromtimestamp(ts, tz=timezone.utc)

        # Accept strings (e.g. "2022-04-04 18:36:24") or datetime objects.
        if isinstance(bd, str):
            s = bd.strip()
            # Try several common formats
            parsed = None
            # Normalize ' ' -> 'T' for fromisoformat if needed
            try:
                parsed = datetime.fromisoformat(s.replace(" ", "T"))
            except Exception:
                pass
            if parsed is None:
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                    try:
                        parsed = datetime.strptime(s, fmt)
                        break
                    except Exception:
                        continue
            if parsed is None:
                # Try to strip a trailing Z (UTC) and parse
                if s.endswith("Z"):
                    try:
                        parsed = datetime.fromisoformat(s[:-1])
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    except Exception:
                        parsed = None
            if parsed is None:
                print(f"⚠️ Could not parse business_date string: {s}")
                return 0.0
            bd = parsed

        # If datetime is naive, assume UTC for freshness calculations
        if isinstance(bd, datetime) and bd.tzinfo is None:
            bd = bd.replace(tzinfo=timezone.utc)

        if not isinstance(bd, datetime):
            print(f"⚠️ Unsupported business_date type after parsing: {type(bd).__name__}")
            return 0.0

        age_days = (datetime.now(timezone.utc) - bd).days
        lam = math.log(2.0) / SETTINGS.freshness_halflife_days
        score = float(math.exp(-lam * max(age_days, 0)))
        print(f"📅 Freshness score: {score:.3f} (age: {age_days} days, half-life: {SETTINGS.freshness_halflife_days} days)")
        return score
    except Exception as e:
        print(f"❌ Error calculating freshness score: {e}")
        return 0.0

def fuse_articles(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fuse article scores: final = 0.5*semantic + 0.3*bm25 + 0.1*vector + 0.1*business
    If semantic scores are all zero (semantic search unavailable), redistribute weight to BM25.
    """
    if not rows:
        print("⚠️ No articles to fuse")
        return []
    
    print(f"⚖️ Fusing {len(rows)} article results...")
    print(f"📋 Article weights: semantic={SETTINGS.w_semantic}, bm25={SETTINGS.w_bm25}, vector={SETTINGS.w_vector}, business={SETTINGS.w_business}")
    
    try:
        bm25s  = [r.get("_bm25", 0.0) for r in rows]
        sems   = [r.get("_semantic", 0.0) for r in rows]
        vecs   = [r.get("_vector", 0.0) for r in rows]

        # Check if semantic scores are all zero (semantic search not available)
        semantic_available = any(sem > 0.0 for sem in sems)
        
        if not semantic_available:
            print("⚠️ No semantic scores available - redistributing semantic weight to BM25")
            # Redistribute semantic weight to BM25
            w_semantic_adj = 0.0
            w_bm25_adj = SETTINGS.w_bm25 
            w_vector_adj = SETTINGS.w_vector + SETTINGS.w_semantic
            w_business_adj = SETTINGS.w_business
        else:
            w_semantic_adj = SETTINGS.w_semantic
            w_bm25_adj = SETTINGS.w_bm25
            w_vector_adj = SETTINGS.w_vector
            w_business_adj = SETTINGS.w_business

        bm_rng  = _minmax(bm25s)
        sem_rng = _minmax(sems)
        vec_rng = _minmax(vecs)
        
        print(f"📊 Score ranges - BM25: {bm_rng[0]:.3f}-{bm_rng[1]:.3f}, Semantic: {sem_rng[0]:.3f}-{sem_rng[1]:.3f}, Vector: {vec_rng[0]:.3f}-{vec_rng[1]:.3f}")
        print(f"📋 Adjusted weights: semantic={w_semantic_adj}, bm25={w_bm25_adj}, vector={w_vector_adj}, business={w_business_adj}")

        for r in rows:
            nbm  = _norm(r.get("_bm25", 0.0), bm_rng)
            nsem = _norm(r.get("_semantic", 0.0), sem_rng)
            nvec = _norm(r.get("_vector", 0.0), vec_rng)
            b    = r.get("_business", 0.0)

            r["_final"] = (
                w_semantic_adj * nsem +
                w_bm25_adj     * nbm +
                w_vector_adj   * nvec +
                w_business_adj * b
            )

        sorted_results = sorted(rows, key=lambda x: x["_final"], reverse=True)
        if sorted_results:
            top_score = sorted_results[0]["_final"]
            print(f"✅ Article fusion complete, top score: {top_score:.3f}")
        
        return sorted_results
        
    except Exception as e:
        print(f"❌ Article fusion failed: {e}")
        raise

def fuse_authors(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fuse author scores: default final = 0.6*semantic + 0.4*bm25 (configurable)
    """
    if not rows:
        print("⚠️ No authors to fuse")
        return []
    
    print(f"⚖️ Fusing {len(rows)} author results...")
    print(f"📋 Author weights: semantic={SETTINGS.aw_semantic}, bm25={SETTINGS.aw_bm25}, vector={SETTINGS.aw_vector}, business={SETTINGS.aw_business}")
    
    try:
        bm25s  = [r.get("_bm25", 0.0) for r in rows]
        sems   = [r.get("_semantic", 0.0) for r in rows]
        vecs   = [r.get("_vector", 0.0) for r in rows]

        # Check if semantic scores are all zero (semantic search not available)
        semantic_available = any(sem > 0.0 for sem in sems)
        
        if not semantic_available:
            print("⚠️ No semantic scores available - redistributing semantic weight to BM25")
            # Redistribute semantic weight to BM25
            w_semantic_adj = 0.0
            w_bm25_adj = SETTINGS.aw_bm25 + SETTINGS.aw_semantic
            w_vector_adj = SETTINGS.aw_vector
            w_business_adj = SETTINGS.aw_business
        else:
            w_semantic_adj = SETTINGS.aw_semantic
            w_bm25_adj = SETTINGS.aw_bm25
            w_vector_adj = SETTINGS.aw_vector
            w_business_adj = SETTINGS.aw_business
        bm_rng  = _minmax(bm25s)
        sem_rng = _minmax(sems)
        vec_rng = _minmax(vecs)

        print(f"📊 Score ranges - BM25: {bm_rng[0]:.3f}-{bm_rng[1]:.3f}, Semantic: {sem_rng[0]:.3f}-{sem_rng[1]:.3f}, Vector: {vec_rng[0]:.3f}-{vec_rng[1]:.3f}")
        print(f"📋 Adjusted weights: semantic={w_semantic_adj}, bm25={w_bm25_adj}, vector={w_vector_adj}, business={w_business_adj}")

        # If semantic not available, prefer a direct scaling of BM25 by max value to preserve granularity
        bm25_max = max(bm25s) if bm25s else 0.0

        for r in rows:
            if not semantic_available and bm25_max > 0:
                # Scale BM25 by max to preserve relative magnitudes instead of min-max collapsing to zero
                nbm = r.get("_bm25", 0.0) / bm25_max
            else:
                nbm = _norm(r.get("_bm25", 0.0), bm_rng)

            nsem = _norm(r.get("_semantic", 0.0), sem_rng)
            nvec = _norm(r.get("_vector", 0.0), vec_rng)
            b    = r.get("_business", 0.0)

            r["_final"] = (
                w_semantic_adj * nsem +
                w_bm25_adj     * nbm +
                w_vector_adj   * nvec +
                w_business_adj * b
            )

        sorted_results = sorted(rows, key=lambda x: x["_final"], reverse=True)
        if sorted_results:
            top_score = sorted_results[0]["_final"]
            print(f"✅ Author fusion complete, top score: {top_score:.3f}")
            
        return sorted_results
        
    except Exception as e:
        print(f"❌ Author fusion failed: {e}")
        raise


