#!/usr/bin/env python
"""
Blog App Seed Data Generator

This utility generates realistic blog data with users and articles for testing
the search functionality. It creates a structured dataset with proper relationships
between users and articles, including likes, dislikes, bookmarks, and follows.

What it does
------------
1) Creates Users and Articles in memory with UUID v4 IDs
2) Enforces constraints:
   - following <-> followers are consistent (A follows B => B has A in followers)
   - users never like and dislike the same article
   - article like/dislike counters match user actions
   - article views > (likes + dislikes)
   - user lists reference real article IDs
   - article author exists; author_id is a single user ID
3) Optionally uses OpenAI to generate realistic title/abstract/content/tags
   with fallback to synthetic content if no API key is available
4) Saves final JSON to ./blog_seed.json

Usage
-----
python blog_data_generator.py [--output OUTPUT_PATH] [--users N_USERS] [--articles N_ARTICLES]
"""

import os
import json
import random
import uuid
import time
import string
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Any

# Optional dependencies
try:
    import requests
except ImportError:
    requests = None


# -----------------------------------------------------
# Configuration
# -----------------------------------------------------
class Config:
    """Configuration settings for data generation"""
    
    # Generation parameters
    RANDOM_SEED = 42
    NUM_USERS = 20
    NUM_ARTICLES = 50
    CONTENT_WORDS_RANGE = (700, 800)
    MAX_FOLLOWS_PER_USER = 6
    LIKES_RANGE = (1, 8)
    DISLIKES_RANGE = (0, 3)
    BOOKMARKS_RANGE = (0, 6)
    
    # OpenAI settings
    USE_OPENAI_IF_AVAILABLE = True
    OPENAI_MODEL = "gpt-4o-mini"
    OPENAI_TIMEOUT = 60
    
    # Avatar settings
    AVATAR_MIN_ID = 1
    AVATAR_MAX_ID = 70
    
    # Date range for content
    START_DATE = datetime(2020, 1, 1, 0, 0, 0)
    END_DATE = datetime(2024, 12, 31, 23, 59, 59)
    
    # Output path
    OUTPUT_JSON = "blog_seed.json"
    
    # Placeholder password (all users)
    PASSWORD_CONST = "$2a$10$AbCdEfGhIjKlMnOpQrStUvWxYz1234567890"
    
    @classmethod
    def from_args(cls, args: Any) -> 'Config':
        """Create config from command-line arguments"""
        config = Config()
        if args.output:
            config.OUTPUT_JSON = args.output
        if args.users:
            config.NUM_USERS = args.users
        if args.articles:
            config.NUM_ARTICLES = args.articles
        return config


# -----------------------------------------------------
# Topics for article generation
# -----------------------------------------------------
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

# Names for user generation
FIRST_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy",
    "Kevin", "Linda", "Michael", "Nancy", "Oscar", "Patricia", "Quincy", "Rachel", "Steve", "Tina"
]

LAST_NAMES = [
    "Anderson", "Brown", "Clark", "Davis", "Evans", "Fisher", "Garcia", "Harris", "Jackson", "Johnson",
    "King", "Lopez", "Miller", "Nelson", "O'Connor", "Parker", "Quinn", "Robinson", "Smith", "Taylor"
]


# -----------------------------------------------------
# Helper functions
# -----------------------------------------------------
def ts(dt: datetime) -> str:
    """Format datetime as 'YYYY-MM-DD HH:mm:ss'."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def rand_dt(start: datetime, end: datetime) -> datetime:
    """Generate a random datetime between start and end."""
    delta = end - start
    seconds = int(delta.total_seconds())
    return start + timedelta(seconds=random.randint(0, max(1, seconds)))


def gen_full_name(i: int) -> str:
    """Generate a random full name."""
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def gen_email(full_name: str, i: int) -> str:
    """Create a simple unique email from the name."""
    base = (
        full_name.lower()
        .replace(" ", ".")
        .replace("'", "")
    )
    base = "".join(ch for ch in base if ch in (string.ascii_lowercase + "._"))
    return f"{base}.{i+1}@example.com"


class AvatarManager:
    """Manager for avatar URLs with fallback capability"""
    
    _last_good_avatar = "https://i.pravatar.cc/150?img=50"
    
    @classmethod
    def pick_avatar_url(cls) -> str:
        """Try to get a working avatar URL, fallback if not possible."""
        if requests is None:
            return cls._last_good_avatar
        
        n = random.randint(Config.AVATAR_MIN_ID, Config.AVATAR_MAX_ID)
        url = f"https://i.pravatar.cc/150?img={n}"
        
        try:
            resp = requests.head(url, timeout=5)
            if resp.status_code != 200:
                resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                cls._last_good_avatar = url
                return url
            return cls._last_good_avatar
        except Exception:
            return cls._last_good_avatar


# -----------------------------------------------------
# OpenAI content generation
# -----------------------------------------------------
class ContentGenerator:
    """Generates article content using OpenAI or fallback synthetic data"""
    
    def __init__(self):
        self.openai_client = self._bootstrap_openai_client() if Config.USE_OPENAI_IF_AVAILABLE else None
    
    def _bootstrap_openai_client(self):
        """Set up the OpenAI client if credentials are available."""
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            # Try loading from .env file
            try:
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.getenv("OPENAI_API_KEY")
            except ImportError:
                pass
        
        if not api_key:
            print("⚠️ No OpenAI API key found. Using synthetic content.")
            return None
            
        try:
            from openai import OpenAI
            client = OpenAI(timeout=Config.OPENAI_TIMEOUT)
            return client
        except ImportError:
            print("⚠️ OpenAI package not found. Using synthetic content.")
            return None
    
    def generate_article_fields(self, topic: str) -> Dict:
        """Generate article fields with OpenAI or fallback to synthetic content."""
        if self.openai_client is None:
            return self._generate_synthetic(topic)
            
        try:
            print(f"    🤖 Generating content for '{topic}' with OpenAI...")
            start_time = time.time()
            
            response = self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": self._build_user_prompt(topic)}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            end_time = time.time()
            print(f"    ✨ Generation completed in {end_time - start_time:.2f} seconds")
            
            obj = json.loads(response.choices[0].message.content)
            
            # Normalize fields
            obj["title"] = obj.get("title", f"{topic}: An Overview").strip()
            obj["abstract"] = obj.get("abstract", f"This article introduces {topic}.").strip()
            content = obj.get("content", f"{topic} fundamentals, applications, and trade-offs.")
            obj["content"] = self._target_word_count(
                content, 
                Config.CONTENT_WORDS_RANGE[0], 
                Config.CONTENT_WORDS_RANGE[1]
            )
            
            # Normalize tags
            tags = obj.get("tags", [])
            if not isinstance(tags, list):
                tags = [str(tags)]
            tags = [str(t).strip()[:40] for t in tags if str(t).strip()]
            tags = tags[:6] if len(tags) > 6 else tags
            if len(tags) < 3:
                tags = list({topic.lower().split()[0], "machine-learning", "deep-learning"})
            obj["tags"] = tags
            
            return {
                "title": obj["title"],
                "abstract": obj["abstract"],
                "content": obj["content"],
                "tags": obj["tags"]
            }
        except Exception as e:
            print(f"    ⚠️ OpenAI generation failed: {str(e)}")
            return self._generate_synthetic(topic)
    
    def _generate_synthetic(self, topic: str) -> Dict:
        """Generate synthetic content as a fallback."""
        print(f"    📝 Generating synthetic content for '{topic}'")
        
        base = f"{topic} is an essential area in modern AI. "
        para = (
            f"{topic} continues to evolve, influencing research and production systems alike. "
            "This article covers fundamentals, practical patterns, failure modes, and deployment tips. "
            "We discuss trade-offs, evaluation, and how to align choices with constraints such as latency, accuracy, and cost. "
        )
        content = base + " ".join([para] * 60)  # Long text, will be trimmed
        content = self._target_word_count(
            content,
            Config.CONTENT_WORDS_RANGE[0],
            Config.CONTENT_WORDS_RANGE[1]
        )
        
        return {
            "title": f"{topic}: A Practical Guide",
            "abstract": f"This article offers a pragmatic introduction to {topic}, including core ideas, pros/cons, and real-world usage patterns.",
            "content": content,
            "tags": list({topic.lower().split()[0], "ml", "dl", "ai"})[:4]
        }
    
    def _target_word_count(self, text: str, min_words: int, max_words: int) -> str:
        """Adjust text to target word count range."""
        words = text.split()
        if len(words) < min_words:
            # Pad with a short reflective coda
            pad = " ".join(["(More details continue with practical tips, examples, caveats, and references.)"] * 3)
            words = (words + pad.split())[:min_words]
        elif len(words) > max_words:
            words = words[:max_words]
        return " ".join(words)
    
    def _get_system_prompt(self) -> str:
        """Return the system prompt for OpenAI."""
        return """You are a concise technical writer that returns STRICT JSON only.

Think through the task privately before answering (do NOT reveal your reasoning).
Follow these rules exactly for the FINAL output:
- Output a single JSON object with keys exactly: "title", "abstract", "content", "tags".
- No preface, no explanations, no markdown, no extra keys, no trailing commas.
- "title": catchy but accurate; ~6-12 words; no emojis; no quotes.
- "abstract": 2-3 sentences, ≤ 60 words total; plain text; no lists.
- "content": 700-800 words; short paragraphs (2-4 sentences each); no headings/markdown.
  Cover: definition, why it matters, core ideas, examples, applications, trade-offs/limits, brief takeaway.
  Prefer clear, concrete language; avoid fluff and repeated phrases.
- "tags": 3-6 short lowercase tags (1-3 words each); deduplicate; no punctuation beyond hyphens."""

    def _build_user_prompt(self, topic: str) -> str:
        """Build the user prompt for a specific topic."""
        return f"""Generate a JSON object for a blog article about the topic below.

Requirements:
- "title": catchy but accurate
- "abstract": 2-3 sentences
- "content": 700-800 words, clear structure, short paragraphs, no markdown headers
- "tags": 3-6 short tags (strings)

Topic: {topic}
Return JSON with keys exactly: title, abstract, content, tags."""


# -----------------------------------------------------
# User and Article generation
# -----------------------------------------------------
class DataGenerator:
    """Generates users and articles with proper relationships."""
    
    def __init__(self, config: Config):
        self.config = config
        random.seed(config.RANDOM_SEED)
        self.content_generator = ContentGenerator()
    
    def make_users(self, n: int) -> List[Dict]:
        """Create user objects with proper attributes."""
        roles = ["admin", "writer", "user"]
        users = []
        
        for i in range(n):
            # Progress indicator
            if i > 0 and (i % 5 == 0 or i == n - 1):
                print(f"  Creating users... {i+1}/{n}")
            
            uid = str(uuid.uuid4())
            full_name = gen_full_name(i)
            users.append({
                "id": uid,
                "full_name": full_name,
                "email": gen_email(full_name, i),
                "password": self.config.PASSWORD_CONST,
                "avatar_url": AvatarManager.pick_avatar_url(),
                "role": random.choices(roles, weights=[1, 3, 8], k=1)[0],
                "created_at": ts(rand_dt(self.config.START_DATE, self.config.END_DATE)),
                "liked_articles": [],
                "disliked_articles": [],
                "bookmarked_articles": [],
                "following": [],
                "followers": []
            })
        
        return users
    
    def wire_follows(self, users: List[Dict]) -> None:
        """Create following/follower relationships between users."""
        print("  Wiring follows between users...")
        ids = [u["id"] for u in users]
        
        # Phase 1: Assign following relationships
        for i, u in enumerate(users):
            # Progress indicator
            if i > 0 and (i % 5 == 0 or i == len(users) - 1):
                print(f"  Following relationships... {i+1}/{len(users)} users")
            
            k = random.randint(0, min(self.config.MAX_FOLLOWS_PER_USER, max(0, len(users)-1)))
            candidates = [x for x in ids if x != u["id"]]
            sample = random.sample(candidates, k) if k > 0 and candidates else []
            u["following"] = sorted(set(sample))
        
        # Phase 2: Build followers from following
        followers_map = {u["id"]: set() for u in users}
        for u in users:
            for v in u["following"]:
                if v in followers_map:  # ensure target user exists
                    followers_map[v].add(u["id"])
        for u in users:
            u["followers"] = sorted(followers_map.get(u["id"], set()))
    
    def make_articles(self, m: int, users: List[Dict]) -> List[Dict]:
        """Create article objects with content."""
        articles = []
        topics_to_use = TOPICS * (1 + m // len(TOPICS))  # Ensure enough topics
        
        for i in range(m):
            # Progress indicator
            if i > 0 and (i % 2 == 0 or i == m - 1):
                print(f"  Creating articles... {i+1}/{m}")
            
            aid = str(uuid.uuid4())
            topic = topics_to_use[i % len(topics_to_use)]
            
            # Choose a single author from users
            author = random.choice(users)
            author_id = author["id"]
            author_name = author["full_name"]
            
            # Created/updated times
            created_at = rand_dt(self.config.START_DATE, self.config.END_DATE)
            min_update_delay = timedelta(minutes=1)
            max_update_delay = timedelta(days=30)
            max_possible_update = min(self.config.END_DATE, created_at + max_update_delay)
            updated_at = rand_dt(created_at + min_update_delay, max_possible_update)
            
            # Generate content
            fields = self.content_generator.generate_article_fields(topic)
            
            articles.append({
                "id": aid,
                "title": fields["title"],
                "content": fields["content"],
                "abstract": fields["abstract"],
                "status": random.choices(["published", "draft"], weights=[85, 15], k=1)[0],
                "tags": sorted(set(fields["tags"])),
                "author_id": author_id,
                "author_name": author_name,
                "likes": 0,
                "dislikes": 0,
                "views": 0,
                "created_at": ts(created_at),
                "updated_at": ts(updated_at)
            })
        
        return articles
    
    def assign_user_engagements(self, users: List[Dict], articles: List[Dict]) -> None:
        """Assign likes, dislikes and bookmarks from users to articles."""
        article_ids = [a["id"] for a in articles]
        
        for i, u in enumerate(users):
            # Progress indicator
            if i > 0 and (i % 5 == 0 or i == len(users) - 1):
                print(f"  Assigning engagements... {i+1}/{len(users)} users")
            
            # How many liked/disliked/bookmarked articles for this user
            n_like = random.randint(
                self.config.LIKES_RANGE[0], 
                min(self.config.LIKES_RANGE[1], len(article_ids))
            )
            n_dislike = random.randint(
                self.config.DISLIKES_RANGE[0], 
                min(self.config.DISLIKES_RANGE[1], len(article_ids))
            )
            
            # Sample likes
            likes = set(random.sample(article_ids, n_like) if n_like > 0 else [])
            
            # Ensure dislikes are disjoint from likes
            remaining = [x for x in article_ids if x not in likes]
            dislikes = set(
                random.sample(remaining, min(n_dislike, len(remaining))) 
                if n_dislike > 0 and remaining else []
            )
            
            # Bookmarks can overlap with likes
            pool_for_bm = list(likes) + random.sample(article_ids, min(len(article_ids), 5))
            n_bm = random.randint(
                self.config.BOOKMARKS_RANGE[0], 
                min(self.config.BOOKMARKS_RANGE[1], len(pool_for_bm))
            )
            bookmarks = set(
                random.sample(pool_for_bm, min(n_bm, len(pool_for_bm))) 
                if n_bm > 0 and pool_for_bm else []
            )
            
            u["liked_articles"] = sorted(likes)
            u["disliked_articles"] = sorted(dislikes)
            u["bookmarked_articles"] = sorted(bookmarks)
    
    def rollup_article_counters(self, users: List[Dict], articles: List[Dict]) -> None:
        """Compute article metrics from user actions."""
        like_count = {a["id"]: 0 for a in articles}
        dislike_count = {a["id"]: 0 for a in articles}
        
        print("  Counting likes and dislikes...")
        for i, u in enumerate(users):
            # Progress indicator
            if i > 0 and (i % 10 == 0 or i == len(users) - 1):
                print(f"    Processing user engagements... {i+1}/{len(users)}")
            
            for aid in u.get("liked_articles", []):
                if aid in like_count:
                    like_count[aid] += 1
            for aid in u.get("disliked_articles", []):
                if aid in dislike_count:
                    dislike_count[aid] += 1
        
        print("  Setting article counters and views...")
        for i, a in enumerate(articles):
            # Progress indicator
            if i > 0 and (i % 3 == 0 or i == len(articles) - 1):
                print(f"    Setting counters... {i+1}/{len(articles)} articles")
            
            L = like_count.get(a["id"], 0)
            D = dislike_count.get(a["id"], 0)
            a["likes"] = int(L)
            a["dislikes"] = int(D)
            # Views greater than total engagements
            base = L + D
            # Add a random extra margin (at least 5)
            margin = random.randint(5, 200)
            a["views"] = int(base + margin)
    
    def validate_dataset(self, users: List[Dict], articles: List[Dict]) -> bool:
        """Validate the generated data for consistency."""
        print("  🔍 Running dataset validations...")
        valid = True
        user_by_id = {u["id"]: u for u in users}
        article_ids = {a["id"] for a in articles}
        
        # 1) Follow consistency
        print("    📋 Validating follow relationships consistency...")
        follow_errors = 0
        for u in users:
            for v in u["following"]:
                if v not in user_by_id:
                    print(f"      ⚠️ User {u['id']} follows non-existent user {v}")
                    follow_errors += 1
                    valid = False
                else:
                    if u["id"] not in user_by_id[v]["followers"]:
                        print(f"      ⚠️ Inconsistent followers: {v} missing follower {u['id']}")
                        follow_errors += 1
                        valid = False
        
        if follow_errors == 0:
            print("    ✅ Follow relationships: All consistent")
        else:
            print(f"    ⚠️ Follow relationships: {follow_errors} errors found")
        
        # 2) Liked/disliked sets (disjoint + exist)
        print("    📋 Validating user engagement data...")
        engagement_errors = 0
        for u in users:
            if set(u["liked_articles"]) & set(u["disliked_articles"]):
                print(f"      ⚠️ User {u['id']} liked_articles & disliked_articles overlap.")
                engagement_errors += 1
                valid = False
            
            for aid in u["liked_articles"] + u["disliked_articles"] + u["bookmarked_articles"]:
                if aid not in article_ids:
                    print(f"      ⚠️ User {u['id']} references non-existent article {aid}")
                    engagement_errors += 1
                    valid = False
        
        if engagement_errors == 0:
            print("    ✅ User engagements: All valid")
        else:
            print(f"    ⚠️ User engagements: {engagement_errors} errors found")
        
        # 3) Article counters match user actions
        counter_errors = 0
        like_count = {}
        dislike_count = {}
        
        for u in users:
            for aid in u.get("liked_articles", []):
                like_count[aid] = like_count.get(aid, 0) + 1
            for aid in u.get("disliked_articles", []):
                dislike_count[aid] = dislike_count.get(aid, 0) + 1
        
        for a in articles:
            if a["likes"] != like_count.get(a["id"], 0):
                print(f"      ⚠️ Article {a['id']} likes mismatch: {a['likes']} vs {like_count.get(a['id'], 0)}")
                counter_errors += 1
                valid = False
            if a["dislikes"] != dislike_count.get(a["id"], 0):
                print(f"      ⚠️ Article {a['id']} dislikes mismatch: {a['dislikes']} vs {dislike_count.get(a['id'], 0)}")
                counter_errors += 1
                valid = False
            if a["views"] < a["likes"] + a["dislikes"]:
                print(f"      ⚠️ Article {a['id']} has fewer views than engagements")
                counter_errors += 1
                valid = False
        
        if counter_errors == 0:
            print("    ✅ Article counters: All consistent")
        else:
            print(f"    ⚠️ Article counters: {counter_errors} errors found")
        
        return valid
    
    def generate_dataset(self) -> Dict:
        """Generate a complete dataset of users and articles."""
        print(f"🏭 Generating dataset with {self.config.NUM_USERS} users and {self.config.NUM_ARTICLES} articles")
        
        # Create users and articles
        users = self.make_users(self.config.NUM_USERS)
        print(f"✅ Created {len(users)} users")
        
        articles = self.make_articles(self.config.NUM_ARTICLES, users)
        print(f"✅ Created {len(articles)} articles")
        
        # Wire up relationships
        self.wire_follows(users)
        print("✅ Established follow relationships")
        
        self.assign_user_engagements(users, articles)
        print("✅ Assigned user engagements")
        
        self.rollup_article_counters(users, articles)
        print("✅ Computed article counters")
        
        # Validate data
        is_valid = self.validate_dataset(users, articles)
        if is_valid:
            print("✅ Dataset validation passed")
        else:
            print("⚠️ Dataset validation found issues")
        
        return {"Users": users, "Articles": articles}


# -----------------------------------------------------
# Main function and CLI
# -----------------------------------------------------
def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate blog seed data")
    parser.add_argument("--output", type=str, help="Output JSON file path")
    parser.add_argument("--users", type=int, help="Number of users to generate")
    parser.add_argument("--articles", type=int, help="Number of articles to generate")
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    config = Config.from_args(args)
    
    print(f"🔧 Blog seed data generator")
    generator = DataGenerator(config)
    
    try:
        # Generate the dataset
        data = generator.generate_dataset()
        
        # Save to file
        output_path = os.path.join(os.getcwd(), config.OUTPUT_JSON)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Print stats
        print(f"📊 Final stats:")
        print(f"  - Users: {len(data['Users'])}")
        print(f"  - Articles: {len(data['Articles'])}")
        print(f"  - Total follows: {sum(len(u['following']) for u in data['Users'])}")
        print(f"  - Total likes: {sum(len(u['liked_articles']) for u in data['Users'])}")
        print(f"  - Total dislikes: {sum(len(u['disliked_articles']) for u in data['Users'])}")
        print(f"  - Total bookmarks: {sum(len(u['bookmarked_articles']) for u in data['Users'])}")
        print(f"📄 Output saved to: {output_path}")
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
