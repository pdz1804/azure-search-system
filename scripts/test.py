"""
Blog App Seed Data Generator (Kaggle-friendly)

What it does
------------
1) Creates Users and Articles in memory (two dicts) with UUID v4 IDs.
2) Enforces constraints:
   - following <-> followers are consistent (A follows B => B has A in followers)
   - users never like and dislike the same article
   - article like/dislike counters match user actions
   - article views > (likes + dislikes)
   - user lists (liked_articles/disliked_articles/bookmarked_articles) reference real article IDs
   - article author exists; author_id is a single user ID; author_name derived
3) Optionally calls OpenAI to generate realistic title/abstract/content/tags.
   Fallback: synthetic content if no API key / request fails.
4) Tries to assign working avatar URLs from i.pravatar.cc; falls back safely.
5) Saves final JSON to ./blog_seed.json and prints stats.

Updated JSON Schema
-------------------
- IDs are UUID v4 strings.
- Article.author_id is a single User.id (UUID string).
- Added 'author_name' (single string).
- Uses 'abstract' instead of 'summary'.
- Date range: 2020-2024 with updated_at > created_at.

Usage on Kaggle
---------------
- (Recommended) Add a secret named OPENAI_API_KEY in "Add-ons → Secrets".
- Or set env var OPENAI_API_KEY in the notebook/session.
- Then run this cell. Output file: ./blog_seed.json
"""

import os, json, random, uuid, math, time
import string
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import itertools

# Network utilities (avatar check + optional OpenAI usage)
import sys
import traceback
import textwrap

# Kaggle can lack some packages by default; requests is usually present.
try:
    import requests
except Exception:
    requests = None

# -----------------------
# CONFIG (edit as needed)
# -----------------------
RANDOM_SEED = 42
NUM_USERS = 5
NUM_ARTICLES = 5
CONTENT_WORDS_RANGE = (700, 800)  # target word count for article content
MAX_FOLLOWS_PER_USER = 6          # max number of other users a user follows
LIKES_RANGE = (1, 8)              # per-user liked_articles count (sampled)
DISLIKES_RANGE = (0, 3)           # per-user disliked_articles count (sampled)
BOOKMARKS_RANGE = (0, 6)          # per-user bookmarked_articles count (sampled)

USE_OPENAI_IF_AVAILABLE = True    # calls OpenAI if OPENAI_API_KEY is present
OPENAI_MODEL = "gpt-4o-mini"      # cost-effective, good quality
OPENAI_TIMEOUT = 60               # seconds

AVATAR_MIN_ID = 1                 # i.pravatar.cc has 1..70 common images
AVATAR_MAX_ID = 70

# Datetime window for 'created_at' (and updated_at >= created_at)
START_DATE = datetime(2020, 1, 1, 0, 0, 0)
END_DATE = datetime(2024, 12, 31, 23, 59, 59)

# Output path
OUTPUT_JSON = "blog_seed.json"

# -----------------------
# Topics (30 items)
# -----------------------
TOPICS = [
    "Transformers for NLP",
    "Self-Supervised Learning",
    "Contrastive Learning (CLIP/SimCLR)",
    "Retrieval-Augmented Generation (RAG)",
    "Prompt Engineering & Structured Output",
    "LoRA/Adapter Fine-Tuning",
    "Vision Transformers (ViT/DeiT)",
    "Diffusion Models & Image Generation",
    "Reinforcement Learning from Human Feedback (RLHF)",
    "Multimodal LLMs (VLMs)",
    "Graph Neural Networks (GNNs)",
    "Efficient Serving (vLLM/AWQ/FlashAttention)",
    "Quantization (INT4/INT8/AWQ)",
    "Mixture-of-Experts (MoE)",
    "Knowledge Distillation",
    "Active Learning & Data Curation",
    "Evaluation of LLMs (G-Eval/DeepEval)",
    "Vector Databases (FAISS, Milvus, Chroma)",
    "Hybrid Search (BM25 + Vectors)",
    "Sparse + Dense Retrieval Fusion",
    "Model Monitoring & Guardrails",
    "Agentic Workflows & Tool Use",
    "Open-Source LLMs (Qwen/Mistral/Llama)",
    "Federated Learning",
    "Time-Series Forecasting with DL",
    "Edge AI & On-device Inference",
    "Computer Vision in Industry",
    "Speech Recognition & TTS",
    "Machine Translation",
    "Ethics, Safety, and Alignment"
]

# -----------------------------------------------------
# Helpers: time, UUID, names, email, avatar existence
# -----------------------------------------------------
random.seed(RANDOM_SEED)

def ts(dt: datetime) -> str:
    """Format datetime as 'YYYY-MM-DD HH:mm:ss'."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def rand_dt(start: datetime, end: datetime) -> datetime:
    """Uniform random datetime between start and end."""
    delta = end - start
    seconds = int(delta.total_seconds())
    return start + timedelta(seconds=random.randint(0, max(1, seconds)))

FIRST_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy",
    "Kevin", "Linda", "Michael", "Nancy", "Oscar", "Patricia", "Quincy", "Rachel", "Steve", "Tina",
    "Ursula", "Victor", "Wendy", "Xavier", "Yvonne", "Zachary", "Amanda", "Brian", "Catherine", "David",
    "Elizabeth", "Frederick", "Gabrielle", "Henry", "Isabella", "Jonathan", "Katherine", "Lawrence", "Margaret", "Nicholas",
    "Olivia", "Peter", "Quinn", "Rebecca", "Samuel", "Teresa", "Uma", "Vincent", "Whitney", "Xander",
    "Yasmin", "Zoe", "Adrian", "Bethany", "Christopher", "Deborah", "Edward", "Fiona", "Gregory", "Hannah",
    "Ian", "Jennifer", "Kenneth", "Lauren", "Matthew", "Natalie", "Owen", "Priscilla", "Robert", "Sophia",
    "Thomas", "Vanessa", "William", "Alexandra", "Benjamin", "Caroline", "Daniel", "Emily", "Felix", "Gloria"
]
LAST_NAMES = [
    "Anderson", "Brown", "Clark", "Davis", "Evans", "Fisher", "Garcia", "Harris", "Jackson", "Johnson",
    "King", "Lopez", "Miller", "Nelson", "O'Connor", "Parker", "Quinn", "Robinson", "Smith", "Taylor",
    "Underwood", "Valdez", "Wilson", "Young", "Adams", "Baker", "Campbell", "Douglas", "Edwards", "Foster",
    "Green", "Hall", "Irving", "Jones", "Kelly", "Lewis", "Martinez", "Moore", "O'Brien", "Phillips",
    "Reed", "Stewart", "Thompson", "Turner", "Walker", "White", "Allen", "Bell", "Carter", "Cooper",
    "Cruz", "Diaz", "Ellis", "Flores", "Graham", "Hayes", "Hill", "Hughes", "James", "Kennedy",
    "Lee", "Long", "Martin", "Mitchell", "Morgan", "Murphy", "Perry", "Powell", "Price", "Ross"
]

def gen_full_name(i: int) -> str:
    """Pick a name deterministically for reproducibility."""
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def gen_email(full_name: str, i: int) -> str:
    """Create a simple unique email from the name."""
    base = (
        full_name.lower()
        .replace(" ", ".")
        .replace("đ", "d")
        .replace("ă", "a")
        .replace("â", "a")
        .replace("ê", "e")
        .replace("ô", "o")
        .replace("ơ", "o")
        .replace("ư", "u")
        .replace("á", "a").replace("à", "a").replace("ả", "a").replace("ã", "a").replace("ạ", "a")
        .replace("é", "e").replace("è", "e").replace("ẻ", "e").replace("ẽ", "e").replace("ẹ", "e")
        .replace("í", "i").replace("ì", "i").replace("ỉ", "i").replace("ĩ", "i").replace("ị", "i")
        .replace("ó", "o").replace("ò", "o").replace("ỏ", "o").replace("õ", "o").replace("ọ", "o")
        .replace("ú", "u").replace("ù", "u").replace("ủ", "u").replace("ũ", "u").replace("ụ", "u")
        .replace("ý", "y").replace("ỳ", "y").replace("ỷ", "y").replace("ỹ", "y").replace("ỵ", "y")
    )
    base = "".join(ch for ch in base if ch in (string.ascii_lowercase + "._"))
    return f"{base}.{i+1}@example.com"

_last_good_avatar = f"https://i.pravatar.cc/150?img=50"

def pick_avatar_url() -> str:
    """
    Try to return a working i.pravatar.cc image.
    If network blocked or image doesn't exist, reuse last known good.
    """
    global _last_good_avatar
    if requests is None:
        return _last_good_avatar
    n = random.randint(AVATAR_MIN_ID, AVATAR_MAX_ID)
    url = f"https://i.pravatar.cc/150?img={n}"
    try:
        # HEAD is usually cheaper; fall back to GET on services that don't allow HEAD
        resp = requests.head(url, timeout=5)
        if resp.status_code != 200:
            resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            _last_good_avatar = url
            return url
        return _last_good_avatar
    except Exception:
        return _last_good_avatar

# -----------------------------------
# OpenAI bootstrap + content generator
# -----------------------------------
def bootstrap_openai_client():
    """
    Resolve OpenAI credentials in this order:
      1) Env var OPENAI_API_KEY
      2) Kaggle Secrets
      3) .env via python-dotenv
    Returns (client or None).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Kaggle secrets
        try:
            from kaggle_secrets import UserSecretsClient
            user_secrets = UserSecretsClient()
            api_key = user_secrets.get_secret("OPENAI_API_KEY")
            if api_key:
                os.environ["OPENAI_API_KEY"] = api_key
        except Exception:
            pass

    if not os.getenv("OPENAI_API_KEY"):
        # optional .env
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except Exception:
            pass

    if not os.getenv("OPENAI_API_KEY"):
        return None

    try:
        from openai import OpenAI
        client = OpenAI(timeout=OPENAI_TIMEOUT)
        return client
    except Exception:
        return None

OPENAI_CLIENT = bootstrap_openai_client() if USE_OPENAI_IF_AVAILABLE else None

def target_word_count(text: str, lo: int, hi: int) -> str:
    """Clamp content to the target range by trimming or gently extending with summary."""
    words = text.split()
    if len(words) < lo:
        # Pad with a short reflective coda to reach ~lo words
        pad = " ".join(["(More details continue with practical tips, examples, caveats, and references.)"] * 3)
        words = (words + pad.split())[:lo]
    elif len(words) > hi:
        words = words[:hi]
    return " ".join(words)

# ---- CoT-safe + Few-shot prompt for JSON-only article generation ----

SYSTEM_PROMPT = """You are a concise technical writer that returns STRICT JSON only.

Think through the task privately before answering (do NOT reveal your reasoning).
Follow these rules exactly for the FINAL output:
- Output a single JSON object with keys exactly: "title", "abstract", "content", "tags".
- No preface, no explanations, no markdown, no extra keys, no trailing commas.
- "title": catchy but accurate; ~6-12 words; no emojis; no quotes.
- "abstract": 2-3 sentences, ≤ 60 words total; plain text; no lists.
- "content": 700-800 words; short paragraphs (2-4 sentences each); no headings/markdown.
  Cover: definition, why it matters, core ideas, examples, applications, trade-offs/limits, brief takeaway.
  Prefer clear, concrete language; avoid fluff and repeated phrases.
- "tags": 3-6 short lowercase tags (1-3 words each); deduplicate; no punctuation beyond hyphens.

Validation checklist (apply before you answer; do not print this checklist):
1) Keys are exactly: title, abstract, content, tags.
2) Word count of content is within 700-800 (approx ±5% acceptable).
3) Abstract length ≤ 60 words and has 2-3 sentences.
4) Tags count in [3..6]; tags are lowercase; no duplicates; each ≤ 3 words.
5) No markdown, code fences, backticks, or headings.
6) JSON parses successfully (UTF-8, proper quoting, no trailing commas).

Even if examples below are shorter, ALWAYS follow the word/count rules above for the final output.
"""

# --- FEW-SHOT EXEMPLARS (shortened content just to show structure/style) ---
FEW_SHOTS = [
    # EXAMPLE 1
    {
        "role": "user",
        "content": """Generate a JSON object for a blog article about the topic below.

Requirements:
- "title": catchy but accurate
- "abstract": 2-3 sentences
- "content": 700-800 words, clear structure, short paragraphs, no markdown headers
- "tags": 3-6 short tags (strings)

Topic: Graph Neural Networks (GNNs)
Return JSON with keys exactly: title, abstract, content, tags."""
    },
    {
        "role": "assistant",
        # Shortened content in example; REAL generations must produce 700-800 words per the system rules.
        "content": """{
  "title": "Understanding Graph Neural Networks for Relational Data",
  "abstract": "Graph Neural Networks model entities and their relationships directly on graphs. They excel when structure matters, enabling tasks like node classification, link prediction, and recommendation.",
  "content": "Graph Neural Networks (GNNs) are neural models designed to learn from graph-structured data ... (example shortened).",
  "tags": ["gnn", "graph-learning", "deep-learning"]
}"""
    },

    # EXAMPLE 2
    {
        "role": "user",
        "content": """Generate a JSON object for a blog article about the topic below.

Requirements:
- "title": catchy but accurate
- "abstract": 2-3 sentences
- "content": 700-800 words, clear structure, short paragraphs, no markdown headers
- "tags": 3-6 short tags (strings)

Topic: Quantization for Efficient Inference (INT8/INT4)
Return JSON with keys exactly: title, abstract, content, tags."""
    },
    {
        "role": "assistant",
        "content": """{
  "title": "Practical Model Quantization for Faster Inference",
  "abstract": "Quantization compresses neural networks by representing weights and activations with fewer bits. Done correctly, it reduces latency and memory with minimal accuracy loss.",
  "content": "Quantization replaces high-precision arithmetic (e.g., FP32) with lower-bit formats like INT8 or INT4 ... (example shortened).",
  "tags": ["quantization", "inference", "optimization"]
}"""
    }
]

# --- USER PROMPT TEMPLATE (f-string ready) ---
def build_user_prompt(topic: str) -> str:
    return f"""Generate a JSON object for a blog article about the topic below.

Requirements:
- "title": catchy but accurate
- "abstract": 2-3 sentences
- "content": 700-800 words, clear structure, short paragraphs, no markdown headers
- "tags": 3-6 short tags (strings)

Topic: {topic}
Return JSON with keys exactly: title, abstract, content, tags.
"""

def generate_article_fields_with_llm(topic: str) -> Dict:
    """
    Ask OpenAI for title, summary, content (~700-800 words), and tags (3-6).
    Falls back to synthetic content on error.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += FEW_SHOTS
    messages.append({"role": "user", "content": build_user_prompt(topic)})
    
    if OPENAI_CLIENT is None:
        return generate_article_fields_synthetic(topic)

    try:
        start_time = time.time()
        print(f"    🤖 Generating content for '{topic}' with LLM...")
        
        resp = OPENAI_CLIENT.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        end_time = time.time()
        generation_time = end_time - start_time
        print(f"    ✨ LLM generation completed in {generation_time:.2f} seconds")
        
        obj = json.loads(resp.choices[0].message.content)
        
        # Normalize + clamp content length
        obj["title"] = obj.get("title", f"{topic}: An Overview").strip()
        # Use abstract field directly, or fall back to summary if present
        obj["abstract"] = obj.get("abstract", obj.get("summary", f"This article introduces {topic}.")).strip()
        content = obj.get("content", f"{topic} fundamentals, applications, and trade-offs.")
        obj["content"] = target_word_count(content, CONTENT_WORDS_RANGE[0], CONTENT_WORDS_RANGE[1])
        tags = obj.get("tags", [])
        
        if not isinstance(tags, list): tags = [str(tags)]
        tags = [str(t).strip()[:40] for t in tags if str(t).strip()]
        tags = tags[:6] if len(tags) > 6 else tags
        if len(tags) < 3:
            tags = list({topic.lower().split()[0], "machine-learning", "deep-learning"})  # quick pad
        obj["tags"] = tags
        
        # Remove summary field since we only want abstract - keep only the required fields
        final_obj = {
            "title": obj["title"],
            "abstract": obj["abstract"], 
            "content": obj["content"],
            "tags": obj["tags"]
        }
        return final_obj
    except Exception:
        # On error, fallback
        print(f"    ⚠️  LLM generation failed, using synthetic content")
        return generate_article_fields_synthetic(topic)

def generate_article_fields_synthetic(topic: str) -> Dict:
    """Deterministic synthetic content if no OpenAI key or request fails."""
    base = f"{topic} is an essential area in modern AI. "
    para = (
        f"{topic} continues to evolve, influencing research and production systems alike. "
        "This article covers fundamentals, practical patterns, failure modes, and deployment tips. "
        "We discuss trade-offs, evaluation, and how to align choices with constraints such as latency, accuracy, and cost. "
    )
    content = base + " ".join([para]*60)  # long text, will be trimmed to range
    content = target_word_count(content, CONTENT_WORDS_RANGE[0], CONTENT_WORDS_RANGE[1])
    # Note: We only keep 'abstract' field, no 'summary'
    abstract = f"This article offers a pragmatic introduction to {topic}, including core ideas, pros/cons, and real-world usage patterns."
    title = f"{topic}: A Practical Guide"
    tags = list({topic.lower().split()[0], "ml", "dl", "ai"})[:4]
    return {"title": title, "abstract": abstract, "content": content, "tags": tags}

# -----------------------
# Core generation steps
# -----------------------
PASSWORD_CONST = "$2a$10$AbCdEfGhIjKlMnOpQrStUvWxYz1234567890"

def make_users(n: int) -> List[Dict]:
    """Create user objects with UUID v4, avatar, role, created_at."""
    roles = ["admin", "writer", "user"]
    users = []
    errors = []
    
    for i in range(n):
        try:
            # Progress indicator
            if i > 0 and (i % 5 == 0 or i == n - 1):
                print(f"  Creating users... {i+1}/{n}")
            
            uid = str(uuid.uuid4())
            full_name = gen_full_name(i)
            users.append({
                "id": uid,
                "full_name": full_name,
                "email": gen_email(full_name, i),
                "password": PASSWORD_CONST,
                "avatar_url": pick_avatar_url(),
                "role": random.choices(roles, weights=[1, 3, 8], k=1)[0],
                "created_at": ts(rand_dt(START_DATE, END_DATE)),
                # will fill after articles are known
                "liked_articles": [],
                "disliked_articles": [],
                "bookmarked_articles": [],
                "following": [],
                "followers": [],
            })
        except Exception as ex:
            error_msg = f"Error creating user {i+1}: {str(ex)}"
            errors.append(error_msg)
            print(f"WARNING: {error_msg}")
            
            # Create minimal fallback user to prevent cascade failures
            users.append({
                "id": str(uuid.uuid4()),
                "full_name": f"User {i+1}",
                "email": f"user{i+1}@example.com",
                "password": PASSWORD_CONST,
                "avatar_url": _last_good_avatar,
                "role": "user",
                "created_at": ts(datetime.now()),
                "liked_articles": [],
                "disliked_articles": [],
                "bookmarked_articles": [],
                "following": [],
                "followers": [],
            })
    
    if errors:
        print(f"  Encountered {len(errors)} errors while creating users")
    
    return users

def wire_follows(users: List[Dict]) -> None:
    """
    Create following links. For each user pick up to MAX_FOLLOWS_PER_USER other users to follow.
    Ensure consistency: A.following contains B => B.followers contains A (vice-versa relation).
    """
    errors = []
    ids = [u["id"] for u in users]
    
    # Phase 1: Assign following relationships
    for i, u in enumerate(users):
        try:
            # Progress indicator
            if i > 0 and (i % 5 == 0 or i == len(users) - 1):
                print(f"  Wiring follows (phase 1)... {i+1}/{len(users)} users")
            
            k = random.randint(0, min(MAX_FOLLOWS_PER_USER, max(0, len(users)-1)))
            candidates = [x for x in ids if x != u["id"]]
            sample = random.sample(candidates, k) if k > 0 and candidates else []
            u["following"] = sorted(set(sample))
        except Exception as ex:
            error_msg = f"Error setting following for user {i+1}: {str(ex)}"
            errors.append(error_msg)
            print(f"WARNING: {error_msg}")
            u["following"] = []
    
    # Phase 2: Build followers from following
    try:
        print("  Wiring follows (phase 2)... building followers relationships")
        followers_map = {u["id"]: set() for u in users}
        for u in users:
            for v in u["following"]:
                if v in followers_map:  # ensure target user exists
                    followers_map[v].add(u["id"])
        for u in users:
            u["followers"] = sorted(followers_map.get(u["id"], set()))
    except Exception as ex:
        error_msg = f"Error building followers map: {str(ex)}"
        errors.append(error_msg)
        print(f"WARNING: {error_msg}")
        # Set empty followers for all users as fallback
        for u in users:
            u["followers"] = []
    
    if errors:
        print(f"  Encountered {len(errors)} errors while wiring follows")

def make_articles(m: int, users: List[Dict], topics: List[str]) -> List[Dict]:
    """
    Create articles with UUID v4, single author, content via OpenAI or fallback.
    """
    articles = []
    errors = []
    
    for i in range(m):
        try:
            # Progress indicator
            if i > 0 and (i % 2 == 0 or i == m - 1):
                print(f"  Creating articles... {i+1}/{m}")
            
            aid = str(uuid.uuid4())
            topic = topics[i % len(topics)]
            # choose 1 author (single author)
            author = random.choice(users)
            author_id = author["id"]
            author_name = author["full_name"]

            # created / updated times
            created_at = rand_dt(START_DATE, END_DATE)
            # Ensure updated_at > created_at by adding at least 1 minute, up to 30 days
            min_update_delay = timedelta(minutes=1)
            max_update_delay = timedelta(days=30)
            # Make sure we don't exceed END_DATE
            max_possible_update = min(END_DATE, created_at + max_update_delay)
            updated_at = rand_dt(created_at + min_update_delay, max_possible_update)

            # content fields
            try:
                fields = generate_article_fields_with_llm(topic)
            except Exception as content_ex:
                error_msg = f"Error generating content for article {i+1}: {str(content_ex)}"
                errors.append(error_msg)
                print(f"WARNING: {error_msg} - Using fallback content")
                fields = generate_article_fields_synthetic(topic)

            articles.append({
                "id": aid,
                "title": fields["title"],
                "content": fields["content"],
                "abstract": fields["abstract"],  # Only abstract, no summary
                "status": random.choices(["published", "draft"], weights=[85, 15], k=1)[0],
                "tags": sorted(set(fields["tags"])),
                # No image field
                "author_id": author_id,
                "author_name": author_name,
                # counters filled after user actions are assigned
                "likes": 0,
                "dislikes": 0,
                "views": 0,
                "created_at": ts(created_at),
                "updated_at": ts(updated_at),
            })
        except Exception as ex:
            error_msg = f"Error creating article {i+1}: {str(ex)}"
            errors.append(error_msg)
            print(f"WARNING: {error_msg}")
            
            # Create minimal fallback article to prevent cascade failures
            try:
                fallback_created = rand_dt(START_DATE, END_DATE)
                fallback_updated = fallback_created + timedelta(minutes=random.randint(1, 60))
                
                articles.append({
                    "id": str(uuid.uuid4()),
                    "title": f"Article {i+1}: {topics[i % len(topics)]}",
                    "content": f"This is fallback content for article {i+1}.",
                    "abstract": f"Abstract for article {i+1}.",  # Only abstract
                    "status": "draft",
                    "tags": ["fallback"],
                    # No image field
                    "author_id": users[0]["id"] if users else str(uuid.uuid4()),
                    "author_name": users[0]["full_name"] if users else "Fallback Author",
                    "likes": 0,
                    "dislikes": 0,
                    "views": 1,
                    "created_at": ts(fallback_created),
                    "updated_at": ts(fallback_updated),
                })
            except Exception:
                print(f"CRITICAL: Failed to create fallback article {i+1}")
    
    if errors:
        print(f"  Encountered {len(errors)} errors while creating articles")
    
    return articles

def assign_user_engagements(users: List[Dict], articles: List[Dict]) -> None:
    """
    For each user, sample disjoint sets of liked_articles and disliked_articles; bookmarked_articles can overlap liked_articles.
    Ensure references exist.
    """
    article_ids = [a["id"] for a in articles]
    errors = []

    for i, u in enumerate(users):
        try:
            # Progress indicator
            if i > 0 and (i % 5 == 0 or i == len(users) - 1):
                print(f"  Assigning engagements... {i+1}/{len(users)} users")
            
            # how many liked_articles/disliked_articles/bookmarked_articles for this user
            n_like = random.randint(LIKES_RANGE[0], min(LIKES_RANGE[1], len(article_ids)))
            n_dislike = random.randint(DISLIKES_RANGE[0], min(DISLIKES_RANGE[1], len(article_ids)))

            likes = set(random.sample(article_ids, n_like) if n_like > 0 else [])
            # ensure disliked_articles disjoint
            remaining = [x for x in article_ids if x not in likes]
            dislikes = set(random.sample(remaining, min(n_dislike, len(remaining))) if n_dislike > 0 and remaining else [])

            # bookmarked_articles: from liked_articles or from remaining pool
            pool_for_bm = list(likes) + random.sample(article_ids, min(len(article_ids), 5))
            n_bm = random.randint(BOOKMARKS_RANGE[0], min(BOOKMARKS_RANGE[1], len(pool_for_bm)))
            bookmarks = set(random.sample(pool_for_bm, min(n_bm, len(pool_for_bm))) if n_bm > 0 and pool_for_bm else [])

            u["liked_articles"] = sorted(likes)
            u["disliked_articles"] = sorted(dislikes)
            u["bookmarked_articles"] = sorted(bookmarks)
        except Exception as ex:
            error_msg = f"Error assigning engagements for user {i+1}: {str(ex)}"
            errors.append(error_msg)
            print(f"WARNING: {error_msg}")
            
            # Set empty lists as fallback
            u["liked_articles"] = []
            u["disliked_articles"] = []
            u["bookmarked_articles"] = []
    
    if errors:
        print(f"  Encountered {len(errors)} errors while assigning engagements")

def rollup_article_counters(users: List[Dict], articles: List[Dict]) -> None:
    """Compute article likes/dislikes from user actions and set views > likes+dislikes."""
    errors = []
    
    try:
        print("  Counting likes and dislikes...")
        like_count = {a["id"]: 0 for a in articles}
        dislike_count = {a["id"]: 0 for a in articles}
        
        for i, u in enumerate(users):
            try:
                # Progress indicator
                if i > 0 and (i % 10 == 0 or i == len(users) - 1):
                    print(f"    Processing user engagements... {i+1}/{len(users)}")
                
                for aid in u.get("liked_articles", []):
                    if aid in like_count:
                        like_count[aid] += 1
                for aid in u.get("disliked_articles", []):
                    if aid in dislike_count:
                        dislike_count[aid] += 1
            except Exception as ex:
                error_msg = f"Error processing engagements for user {i+1}: {str(ex)}"
                errors.append(error_msg)
                print(f"WARNING: {error_msg}")
        
        print("  Setting article counters and views...")
        for i, a in enumerate(articles):
            try:
                # Progress indicator
                if i > 0 and (i % 3 == 0 or i == len(articles) - 1):
                    print(f"    Setting counters... {i+1}/{len(articles)} articles")
                
                L = like_count.get(a["id"], 0)
                D = dislike_count.get(a["id"], 0)
                a["likes"] = int(L)
                a["dislikes"] = int(D)
                # views greater than total engagements
                base = L + D
                # add a random extra margin (at least 5)
                margin = random.randint(5, 200)
                a["views"] = int(base + margin)
            except Exception as ex:
                error_msg = f"Error setting counters for article {i+1}: {str(ex)}"
                errors.append(error_msg)
                print(f"WARNING: {error_msg}")
                # Set minimal fallback values
                a["likes"] = 0
                a["dislikes"] = 0
                a["views"] = 10
    except Exception as ex:
        error_msg = f"Critical error in rollup_article_counters: {str(ex)}"
        errors.append(error_msg)
        print(f"CRITICAL WARNING: {error_msg}")
        # Set all articles to minimal values
        for a in articles:
            a["likes"] = 0
            a["dislikes"] = 0
            a["views"] = 10
    
    if errors:
        print(f"  Encountered {len(errors)} errors while rolling up counters")

# -----------------------
# Validation & stats
# -----------------------
def validate_dataset(users: List[Dict], articles: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Validate all constraints. Return (ok, errors).
    """
    print("  🔍 Running dataset validations...")
    errors = []
    user_by_id = {u["id"]: u for u in users}
    article_ids = {a["id"] for a in articles}

    # 1) Follow consistency
    print("    📋 Validating follow relationships consistency...")
    follow_errors = 0
    for u in users:
        for v in u["following"]:
            if v not in user_by_id:
                errors.append(f"User {u['id']} follows non-existent user {v}")
                follow_errors += 1
            else:
                if u["id"] not in user_by_id[v]["followers"]:
                    errors.append(f"Inconsistent followers: {v} missing follower {u['id']}")
                    follow_errors += 1
    
    if follow_errors == 0:
        print("    ✅ Follow relationships: All consistent")
    else:
        print(f"    ⚠️  Follow relationships: {follow_errors} errors found")

    # 2) liked_articles/disliked_articles sets (disjoint + exist)
    print("    📋 Validating user engagement data...")
    engagement_errors = 0
    for u in users:
        if set(u["liked_articles"]) & set(u["disliked_articles"]):
            errors.append(f"User {u['id']} liked_articles & disliked_articles overlap.")
            engagement_errors += 1
        for aid in itertools.chain(u["liked_articles"], u["disliked_articles"], u["bookmarked_articles"]):
            if aid not in article_ids:
                errors.append(f"User {u['id']} references non-existent article {aid}")
                engagement_errors += 1
    
    if engagement_errors == 0:
        print("    ✅ User engagements: All valid (no overlaps, all articles exist)")
    else:
        print(f"    ⚠️  User engagements: {engagement_errors} errors found")

    # 3) Authors exist + non-empty
    print("    📋 Validating article authors...")
    author_errors = 0
    for a in articles:
        if not a.get("author_id"):
            errors.append(f"Article {a['id']} has empty author_id.")
            author_errors += 1
        elif a["author_id"] not in user_by_id:
            errors.append(f"Article {a['id']} author {a['author_id']} does not exist.")
            author_errors += 1
    
    if author_errors == 0:
        print("    ✅ Article authors: All exist and are valid")
    else:
        print(f"    ⚠️  Article authors: {author_errors} errors found")

    # 4) Counters consistent
    print("    📋 Validating like/dislike counters...")
    # Recompute expected counts and compare
    exp_like = {a["id"]: 0 for a in articles}
    exp_dislike = {a["id"]: 0 for a in articles}
    for u in users:
        for aid in u["liked_articles"]:
            exp_like[aid] += 1
        for aid in u["disliked_articles"]:
            exp_dislike[aid] += 1
    
    counter_errors = 0
    view_errors = 0
    for a in articles:
        if a["likes"] != exp_like[a["id"]]:
            errors.append(f"Article {a['id']} likes mismatch {a['likes']} != {exp_like[a['id']]}")
            counter_errors += 1
        if a["dislikes"] != exp_dislike[a["id"]]:
            errors.append(f"Article {a['id']} dislikes mismatch {a['dislikes']} != {exp_dislike[a['id']]}")
            counter_errors += 1
        if not (a["views"] > (a["likes"] + a["dislikes"])):
            errors.append(f"Article {a['id']} views {a['views']} not greater than likes+dislikes {a['likes']+a['dislikes']}.")
            view_errors += 1
    
    if counter_errors == 0:
        print("    ✅ Like/dislike counters: All match user actions")
    else:
        print(f"    ⚠️  Like/dislike counters: {counter_errors} mismatches found")
    
    if view_errors == 0:
        print("    ✅ Article views: All greater than total engagements")
    else:
        print(f"    ⚠️  Article views: {view_errors} invalid view counts")

    # Summary
    total_errors = len(errors)
    if total_errors == 0:
        print("    🎉 All validations passed successfully!")
    else:
        print(f"    ❌ Total validation errors: {total_errors}")

    return (len(errors) == 0), errors

def print_stats(users: List[Dict], articles: List[Dict]) -> None:
    """Quick dataset overview."""
    roles = {}
    for u in users:
        roles[u["role"]] = roles.get(u["role"], 0) + 1
    print("\n=== DATASET STATS ===")
    print(f"Users: {len(users)} | Articles: {len(articles)}")
    print("Roles:", roles)
    avg_liked_articles_per_user = sum(len(u["liked_articles"]) for u in users) / max(1, len(users))
    avg_disliked_articles_per_user = sum(len(u["disliked_articles"]) for u in users) / max(1, len(users))
    avg_bookmarked_articles_per_user = sum(len(u["bookmarked_articles"]) for u in users) / max(1, len(users))
    print(f"Avg liked_articles/user: {avg_liked_articles_per_user:.2f} | Avg disliked_articles/user: {avg_disliked_articles_per_user:.2f} | Avg bookmarked_articles/user: {avg_bookmarked_articles_per_user:.2f}")
    avg_views = sum(a["views"] for a in articles) / max(1, len(articles))
    print(f"Avg article views: {avg_views:.1f}")
    total_likes = sum(a["likes"] for a in articles)
    total_dislikes = sum(a["dislikes"] for a in articles)
    print(f"Total likes: {total_likes} | Total dislikes: {total_dislikes}")

# -----------------------
# Main
# -----------------------
def main():
    """
    Main generation function with robust error handling.
    Ensures JSON output is always produced, even if errors occur.
    """
    users = []
    articles = []
    critical_errors = []
    
    # Step 1: Generate Users
    try:
        print("=== STEP 1: Generating users ===")
        users = make_users(NUM_USERS)
        print(f"✅ Created {len(users)} users")
    except Exception as ex:
        error_msg = f"CRITICAL ERROR in user generation: {str(ex)}"
        critical_errors.append(error_msg)
        print(f"❌ {error_msg}")
        traceback.print_exc()
        # Create minimal fallback users to prevent complete failure
        try:
            users = []
            for i in range(min(NUM_USERS, 5)):  # Create at least a few users
                users.append({
                    "id": str(uuid.uuid4()),
                    "full_name": f"Fallback User {i+1}",
                    "email": f"fallback{i+1}@example.com",
                    "password": PASSWORD_CONST,
                    "avatar_url": _last_good_avatar,
                    "role": "user",
                    "created_at": ts(datetime.now()),
                    "liked_articles": [],
                    "disliked_articles": [],
                    "bookmarked_articles": [],
                    "following": [],
                    "followers": [],
                })
            print(f"🔄 Created {len(users)} fallback users")
        except Exception:
            print("💥 Failed to create even fallback users")

    # Step 2: Wire Follow Relationships
    try:
        print("\n=== STEP 2: Wiring follow relationships ===")
        if users:
            wire_follows(users)
            print("✅ Wired follow relationships")
        else:
            print("⚠️ Skipping follow relationships (no users)")
    except Exception as ex:
        error_msg = f"ERROR in follow relationships: {str(ex)}"
        critical_errors.append(error_msg)
        print(f"❌ {error_msg}")
        traceback.print_exc()
        # Set empty relationships as fallback
        for u in users:
            u["following"] = []
            u["followers"] = []

    # Step 3: Generate Articles
    try:
        print("\n=== STEP 3: Generating articles ===")
        if users:
            articles = make_articles(NUM_ARTICLES, users, TOPICS)
            print(f"✅ Created {len(articles)} articles")
        else:
            print("⚠️ Cannot create articles without users")
    except Exception as ex:
        error_msg = f"CRITICAL ERROR in article generation: {str(ex)}"
        critical_errors.append(error_msg)
        print(f"❌ {error_msg}")
        traceback.print_exc()
        # Create minimal fallback articles
        try:
            articles = []
            for i in range(min(NUM_ARTICLES, 2)):  # Create at least a few articles
                fallback_created = rand_dt(START_DATE, END_DATE)
                fallback_updated = fallback_created + timedelta(minutes=random.randint(1, 60))
                
                articles.append({
                    "id": str(uuid.uuid4()),
                    "title": f"Fallback Article {i+1}",
                    "content": f"This is fallback content for article {i+1}.",
                    "abstract": f"Abstract for fallback article {i+1}.",  # Only abstract
                    "status": "draft",
                    "tags": ["fallback"],
                    # No image field
                    "author_id": users[0]["id"] if users else str(uuid.uuid4()),
                    "author_name": users[0]["full_name"] if users else "Fallback Author",
                    "likes": 0,
                    "dislikes": 0,
                    "views": 10,
                    "created_at": ts(fallback_created),
                    "updated_at": ts(fallback_updated),
                })
            print(f"🔄 Created {len(articles)} fallback articles")
        except Exception:
            print("💥 Failed to create even fallback articles")

    # Step 4: Assign User Engagements
    try:
        print("\n=== STEP 4: Assigning user engagements ===")
        if users and articles:
            assign_user_engagements(users, articles)
            print("✅ Assigned user engagements")
        else:
            print("⚠️ Skipping user engagements (missing users or articles)")
    except Exception as ex:
        error_msg = f"ERROR in user engagements: {str(ex)}"
        critical_errors.append(error_msg)
        print(f"❌ {error_msg}")
        traceback.print_exc()

    # Step 5: Roll Up Article Counters
    try:
        print("\n=== STEP 5: Rolling up article counters ===")
        if users and articles:
            rollup_article_counters(users, articles)
            print("✅ Rolled up article counters")
        else:
            print("⚠️ Skipping counter rollup (missing users or articles)")
    except Exception as ex:
        error_msg = f"ERROR in counter rollup: {str(ex)}"
        critical_errors.append(error_msg)
        print(f"❌ {error_msg}")
        traceback.print_exc()

    # Step 6: Validate Dataset
    try:
        print("\n=== STEP 6: Validating dataset ===")
        if users and articles:
            ok, errs = validate_dataset(users, articles)
            if not ok:
                print("❌ Validation errors found:")
                for e in errs[:20]:  # Show first 20 errors
                    print(f"   - {e}")
                if len(errs) > 20:
                    print(f"   ... and {len(errs)-20} more errors.")
                print("⚠️ Dataset has validation issues but will still be saved")
            else:
                print("✅ Validation passed")
        else:
            print("⚠️ Skipping validation (missing users or articles)")
    except Exception as ex:
        error_msg = f"ERROR in validation: {str(ex)}"
        critical_errors.append(error_msg)
        print(f"❌ {error_msg}")
        traceback.print_exc()

    # Step 7: Print Statistics
    try:
        print("\n=== STEP 7: Generating statistics ===")
        if users or articles:
            print_stats(users, articles)
        else:
            print("⚠️ No data to show statistics for")
    except Exception as ex:
        error_msg = f"ERROR in statistics: {str(ex)}"
        critical_errors.append(error_msg)
        print(f"❌ {error_msg}")
        traceback.print_exc()

    # Step 8: Save JSON (ALWAYS ATTEMPT THIS)
    dataset = {"Users": users, "Articles": articles}
    try:
        print(f"\n=== STEP 8: Saving to {OUTPUT_JSON} ===")
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        print(f"✅ Successfully saved {len(users)} users and {len(articles)} articles to {OUTPUT_JSON}")
    except Exception as ex:
        error_msg = f"CRITICAL ERROR saving JSON: {str(ex)}"
        critical_errors.append(error_msg)
        print(f"💥 {error_msg}")
        traceback.print_exc()
        
        # Try alternative save methods
        try:
            backup_name = f"blog_seed_backup_{int(time.time())}.json"
            print(f"🔄 Attempting backup save to {backup_name}")
            with open(backup_name, "w", encoding="utf-8") as f:
                json.dump(dataset, f, ensure_ascii=False, indent=2)
            print(f"✅ Backup saved to {backup_name}")
        except Exception:
            print("💥 Even backup save failed")
            try:
                # Try minimal JSON
                minimal = {"Users": len(users), "Articles": len(articles), "timestamp": ts(datetime.now())}
                with open("blog_seed_minimal.json", "w") as f:
                    json.dump(minimal, f, indent=2)
                print("✅ Saved minimal metadata to blog_seed_minimal.json")
            except Exception:
                print("💥 All save attempts failed")

    # Final Summary
    print(f"\n{'='*50}")
    print("🏁 GENERATION COMPLETE")
    print(f"{'='*50}")
    if critical_errors:
        print(f"❌ {len(critical_errors)} critical errors encountered:")
        for error in critical_errors:
            print(f"   • {error}")
        print("\n⚠️  JSON file generated despite errors - please review the data quality")
    else:
        print("✅ Generation completed successfully!")
    
    print(f"\n📊 Final counts:")
    print(f"   • Users: {len(users)}")
    print(f"   • Articles: {len(articles)}")
    print(f"   • Output file: {OUTPUT_JSON}")
    print(f"\n🎯 You can now use the generated JSON file for your blog application!")

if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        print(f"\n💥 UNHANDLED EXCEPTION IN MAIN: {ex}")
        traceback.print_exc(file=sys.stdout)
        print("\n🔄 Attempting emergency data save...")
        
        # Emergency minimal save
        try:
            emergency_data = {
                "error": str(ex),
                "timestamp": ts(datetime.now()),
                "Users": [],
                "Articles": []
            }
            with open("blog_seed_emergency.json", "w") as f:
                json.dump(emergency_data, f, indent=2)
            print("✅ Emergency file saved as blog_seed_emergency.json")
        except Exception:
            print("💥 Emergency save also failed")
        
        print(f"\n{'='*50}")
        print("💀 CRITICAL FAILURE - Check the error messages above")
        print(f"{'='*50}")




