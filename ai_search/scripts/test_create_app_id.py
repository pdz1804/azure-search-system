#!/usr/bin/env python3
"""
Dataset Splitter & Interaction Simulator for Multi-App Blog/Article/News Platforms.

This script ingests a source JSON with two top-level arrays: "Users" and "Articles".
It then:
  1) Creates three application IDs (Blog, Article, News) with distinct styles.
  2) Adds `is_active=True` to every user and article.
  3) Removes fields:
       - From users: liked_articles, disliked_articles, bookmarked_articles, following, followers
       - From articles: author_id, author_name, likes, dislikes
  4) Randomly splits users and articles into the three apps and stamps each with an `app_id`.
  5) Inside each app:
       - Assigns an author (author_id, author_name) for every article from users in the same app.
       - Simulates user interactions:
           * liked_articles, disliked_articles, bookmarked_articles for each user
           * per-article counts: likes, dislikes (derived from user actions)
         Rules:
           * A user never likes and dislikes the same article.
           * All references are within the same app.
  6) Validates referential integrity and aggregate counting:
       - All referenced article IDs exist in the app
       - No like/dislike overlap per user
       - Article like/dislike counts EXACTLY match user actions
       - Every article's author exists in the same app
  7) Writes the transformed dataset to `<input_dir>/articles_transformed.json`
     and includes an "Apps" section listing the 3 app UUIDs and styles.

Usage:
    python transform_articles.py --input "C:\\PDZ\\Intern02\\ai-search-cloud\\ai_search\\data\\articles.json"

Notes:
- Randomness is seeded for reproducibility; adjust `RANDOM_SEED` to re-shuffle.
- The script tries to keep per-app distributions even by modulo assignment after shuffling.
- If an app ends up with 0 users or 0 articles (edge case on tiny datasets),
  the script will rebalance minimally to keep each app viable.
"""

import argparse
import json
import os
import random
import uuid
from collections import defaultdict
from typing import Dict, List, Tuple, Set

# -----------------------------
# Configuration
# -----------------------------
RANDOM_SEED = 42  # Change for a different random split and interaction pattern

APP_DEFS = [
    {"name": "Blog app",    "style": "personal, informal, opinion-driven"},
    {"name": "Article app", "style": "structured, informative, analytical"},
    {"name": "News app",    "style": "timely, factual, event-driven"},
]

# Interaction intensity knobs per app (probabilities)
# You can tweak to reflect different "cultures" in each app.
APP_BEHAVIOR = {
    "Blog app":    {"p_like": 0.35, "p_dislike": 0.08, "p_bookmark": 0.20},
    "Article app": {"p_like": 0.40, "p_dislike": 0.05, "p_bookmark": 0.25},
    "News app":    {"p_like": 0.30, "p_dislike": 0.10, "p_bookmark": 0.15},
}

# -----------------------------
# Utility helpers
# -----------------------------

def gen_uuid() -> str:
    """Generate a random UUID4 string."""
    return str(uuid.uuid4())


def ensure_keys_removed(d: dict, keys: List[str]) -> None:
    """Remove keys from dict if present (ignore missing)."""
    for k in keys:
        d.pop(k, None)


def chunk_assign_round_robin(items: List[dict], app_ids: List[str]) -> None:
    """
    Assign items to app_ids in a round-robin fashion after a shuffle.
    Ensures reasonably balanced distribution and avoids empty partitions for moderate sizes.
    """
    random.shuffle(items)
    for idx, item in enumerate(items):
        item["app_id"] = app_ids[idx % len(app_ids)]


def minimal_rebalance_if_empty(groups: Dict[str, List[dict]], need_key: str) -> None:
    """
    If an app group is empty for `need_key` (e.g., "Users" or "Articles"),
    move one element from the biggest group to the empty one to ensure viability.
    """
    empties = [k for k, v in groups.items() if len(v) == 0]
    if not empties:
        return
    # find largest group
    largest_key = max(groups.keys(), key=lambda k: len(groups[k]))
    for empty in empties:
        if groups[largest_key]:
            elem = groups[largest_key].pop()
            groups[empty].append(elem)


# -----------------------------
# Interaction simulation
# -----------------------------

def simulate_user_interactions(
    users: List[dict],
    articles: List[dict],
    app_name: str
) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, Set[str]]]:
    """
    For a single app's users & articles, simulate:
      - liked_articles[user_id] = set(article_ids)
      - disliked_articles[user_id] = set(article_ids)
      - bookmarked_articles[user_id] = set(article_ids)

    Guarantees:
      - No overlap between likes and dislikes for the same (user, article)
      - All references are to articles in this app
    """
    p_like = APP_BEHAVIOR[app_name]["p_like"]
    p_dislike = APP_BEHAVIOR[app_name]["p_dislike"]
    p_bookmark = APP_BEHAVIOR[app_name]["p_bookmark"]

    article_ids = [a["id"] for a in articles]
    liked = defaultdict(set)      # user_id -> set(article_id)
    disliked = defaultdict(set)   # user_id -> set(article_id)
    bookmarked = defaultdict(set) # user_id -> set(article_id)

    for u in users:
        uid = u["id"]
        # Iterate through all articles; flip coins per article.
        for aid in article_ids:
            # like/dislike are mutually exclusive; decide dislike first to keep probabilities clean
            do_dislike = random.random() < p_dislike
            if do_dislike:
                disliked[uid].add(aid)
                continue

            do_like = random.random() < p_like
            if do_like:
                liked[uid].add(aid)

            # bookmark is independent (people bookmark even if they didn't like yet)
            do_bookmark = random.random() < p_bookmark
            if do_bookmark:
                bookmarked[uid].add(aid)

        # Extra safety: remove any overlap (shouldn't exist due to the order above)
        liked[uid] -= disliked[uid]

    return liked, disliked, bookmarked


def assign_authors_per_article(users: List[dict], articles: List[dict]) -> None:
    """
    Assign a valid author (author_id, author_name) from the same app to every article.
    If there are no users in the app (very small datasets), author remains None (and validator will flag).
    """
    if not users:
        for a in articles:
            a["author_id"] = None
            a["author_name"] = None
        return

    # Prefer a stable round-robin author assignment for variety
    idx = 0
    for a in articles:
        author = users[idx % len(users)]
        a["author_id"] = author["id"]
        a["author_name"] = author.get("full_name") or author.get("name") or "Unknown"
        idx += 1


# -----------------------------
# Validation (per app)
# -----------------------------

def validate_app_integrity(
    app_name: str,
    users: List[dict],
    articles: List[dict],
    liked: Dict[str, Set[str]],
    disliked: Dict[str, Set[str]],
    bookmarked: Dict[str, Set[str]],
) -> Dict[str, bool]:
    """
    Validate within-app referential integrity and counting.

    Checks:
      - Every referenced article in likes/dislikes/bookmarks exists in the app.
      - No user likes & dislikes the same article.
      - Each article's like/dislike counts match the number of unique users that referenced them.
      - article.author_id/author_name belongs to a user in the same app.

    Returns:
      Dict of check_name -> bool
    """
    results = {}

    # Build article/user id sets for quick lookup
    article_ids = {a["id"] for a in articles}
    user_ids = {u["id"] for u in users}

    # 1) References valid
    ref_ok = True
    for uid, aset in liked.items():
        if uid not in user_ids:
            ref_ok = False
            break
        if not aset.issubset(article_ids):
            ref_ok = False
            break
    if ref_ok:
        for uid, aset in disliked.items():
            if uid not in user_ids or not aset.issubset(article_ids):
                ref_ok = False
                break
    if ref_ok:
        for uid, aset in bookmarked.items():
            if uid not in user_ids or not aset.issubset(article_ids):
                ref_ok = False
                break
    results["references_valid"] = ref_ok

    # 2) No like/dislike overlap
    overlap_ok = True
    for uid in user_ids:
        if uid in liked and uid in disliked:
            if liked[uid] & disliked[uid]:
                overlap_ok = False
                break
    results["no_like_dislike_overlap"] = overlap_ok

    # 3) Author exists in same app
    authors_ok = True
    uid_to_name = {u["id"]: u.get("full_name") or u.get("name") for u in users}
    for a in articles:
        auth_id = a.get("author_id")
        auth_name = a.get("author_name")
        if not auth_id or auth_id not in uid_to_name:
            authors_ok = False
            break
        if uid_to_name[auth_id] != auth_name:
            # Allow "Unknown" only if user has no name; otherwise require exact match
            if uid_to_name[auth_id] and auth_name != uid_to_name[auth_id]:
                authors_ok = False
                break
    results["authors_in_same_app"] = authors_ok

    # 4) Article like/dislike counts match user actions
    # Build reverse counts from user maps
    like_counts = defaultdict(int)
    dislike_counts = defaultdict(int)
    for uid, aset in liked.items():
        for aid in aset:
            like_counts[aid] += 1
    for uid, aset in disliked.items():
        for aid in aset:
            dislike_counts[aid] += 1

    counts_ok = True
    for a in articles:
        if a.get("likes", 0) != like_counts[a["id"]]:
            counts_ok = False
            break
        if a.get("dislikes", 0) != dislike_counts[a["id"]]:
            counts_ok = False
            break
    results["article_counts_match"] = counts_ok

    return results


# -----------------------------
# I/O + Orchestration
# -----------------------------

def load_source(path: str) -> Tuple[List[dict], List[dict]]:
    """Load the source JSON and return (users, articles)."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    users = data.get("Users", []) or []
    articles = data.get("Articles", []) or []
    return users, articles


def write_output(path: str, apps_meta: List[dict], users: List[dict], articles: List[dict]) -> str:
    """
    Write the transformed dataset next to the input file.
    Returns the output path.
    """
    out_dir = os.path.dirname(path)
    out_path = os.path.join(out_dir, "articles_transformed.json")
    payload = {
        "Apps": apps_meta,
        "Users": users,
        "Articles": articles,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return out_path


def main(input_path: str) -> None:
    random.seed(RANDOM_SEED)

    # 1) Load
    users, articles = load_source(input_path)

    # 2) Create three app IDs
    apps_meta = []
    for app in APP_DEFS:
        apps_meta.append({
            "app_id": gen_uuid(),
            "app_name": app["name"],
            "style": app["style"],
            "is_active": True,
        })

    # Maps to help by name -> id, and id -> name
    app_name_to_id = {a["app_name"]: a["app_id"] for a in apps_meta}
    app_ids = [a["app_id"] for a in apps_meta]

    # 3) Add is_active to all & remove requested fields
    for u in users:
        u["is_active"] = True
        ensure_keys_removed(u, ["liked_articles", "disliked_articles", "bookmarked_articles", "following", "followers"])
    for a in articles:
        a["is_active"] = True
        ensure_keys_removed(a, ["author_id", "author_name", "likes", "dislikes"])

    # 4) Assign app_id via balanced round-robin
    chunk_assign_round_robin(users, app_ids)
    chunk_assign_round_robin(articles, app_ids)

    # Build per-app partitions
    users_by_app: Dict[str, List[dict]] = defaultdict(list)
    articles_by_app: Dict[str, List[dict]] = defaultdict(list)
    for u in users:
        users_by_app[u["app_id"]].append(u)
    for a in articles:
        articles_by_app[a["app_id"]].append(a)

    # Rebalance if any app accidentally has 0 users or 0 articles (edge case on tiny data)
    minimal_rebalance_if_empty(users_by_app, need_key="Users")
    minimal_rebalance_if_empty(articles_by_app, need_key="Articles")

    # 5) For each app: assign authors, simulate interactions, and set counts back on articles & lists back on users
    all_validations = {}
    for app in apps_meta:
        app_id = app["app_id"]
        app_name = app["app_name"]

        app_users = users_by_app[app_id]
        app_articles = articles_by_app[app_id]

        # Assign authors from same app
        assign_authors_per_article(app_users, app_articles)

        # Simulate interactions within app
        liked_map, disliked_map, bookmarked_map = simulate_user_interactions(app_users, app_articles, app_name)

        # Write interactions back to users (sorted lists for readability)
        for u in app_users:
            uid = u["id"]
            u["liked_articles"] = sorted(list(liked_map.get(uid, set())))
            u["disliked_articles"] = sorted(list(disliked_map.get(uid, set())))
            u["bookmarked_articles"] = sorted(list(bookmarked_map.get(uid, set())))
            # We intentionally keep following/followers removed as requested.

        # Compute article counts from user actions
        like_counts = defaultdict(int)
        dislike_counts = defaultdict(int)
        for uid, aset in liked_map.items():
            for aid in aset:
                like_counts[aid] += 1
        for uid, aset in disliked_map.items():
            for aid in aset:
                dislike_counts[aid] += 1

        for a in app_articles:
            a["likes"] = like_counts[a["id"]]
            a["dislikes"] = dislike_counts[a["id"]]

        # Validate integrity in this app
        all_validations[app_name] = validate_app_integrity(
            app_name=app_name,
            users=app_users,
            articles=app_articles,
            liked=liked_map,
            disliked=disliked_map,
            bookmarked=bookmarked_map,
        )

    # 6) Persist
    out_path = write_output(input_path, apps_meta, users, articles)

    # 7) Report
    print(f"\n✅ Transformation complete. Output written to:\n  {out_path}\n")
    print("Validation summary (per app):")
    for app in apps_meta:
        app_name = app["app_name"]
        checks = all_validations.get(app_name, {})
        ok_all = all(checks.values()) if checks else False
        print(f"\n— {app_name} — ({'PASS' if ok_all else 'FAIL'})")
        for k, v in checks.items():
            print(f"  {k:28s}: {'OK' if v else 'FAIL'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transform and split blog dataset across three apps with consistent interactions.")
    parser.add_argument(
        "--input",
        default=r"C:\PDZ\Intern02\ai-search-cloud\ai_search\data\blog_seed_v1.json",
        help="Path to the input JSON containing 'Users' and 'Articles'."
    )
    args = parser.parse_args()
    main(args.input)
