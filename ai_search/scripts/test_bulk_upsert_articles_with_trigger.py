# bulk_upsert_articles_with_trigger.py
"""
Bulk test for Cosmos DB pre-trigger:
- Reads .env (COSMOS_ENDPOINT, COSMOS_KEY, COSMOS_DB, COSMOS_ARTICLES, COSMOS_USERS)
- Ensures trigger 'addIsActiveField' (Pre, All) exists for both containers
- Loads data/articles.json and data/users.json (if exists)
- Upserts each document with pre_trigger_include so 'is_active' is added if missing
- Prints a summary + verifies documents
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from azure.cosmos import CosmosClient

# ---------- Setup ----------
load_dotenv()
ENDPOINT = os.environ["COSMOS_ENDPOINT"]
KEY = os.environ["COSMOS_KEY"]
DB_ID = os.environ["COSMOS_DB"]
ARTICLES_CONTAINER_ID = os.environ["COSMOS_ARTICLES"]
USERS_CONTAINER_ID = os.environ["COSMOS_USERS"]

ARTICLES_PATH = r"..\data\articles.json"  # <- your input file
USERS_PATH = r"..\data\users.json"  # <- users input file (if exists)

client = CosmosClient(ENDPOINT, KEY)
db = client.get_database_client(DB_ID)
articles_container = db.get_container_client(ARTICLES_CONTAINER_ID)
users_container = db.get_container_client(USERS_CONTAINER_ID)

# ---------- Ensure pre-trigger exists ----------
TRIGGER_ID = "addIsActiveField"
TRIGGER_BODY = """
function addIsActiveField() {
    var context = getContext();
    var request = context.getRequest();
    var body = request.getBody();
    if (!body) { throw new Error("Document body must be provided."); }
    if (typeof body === "string") { body = JSON.parse(body); }  // tolerate string payloads
    if (typeof body !== "object") { throw new Error("Document body must be an object."); }
    if (!Object.prototype.hasOwnProperty.call(body, "is_active")) {
        body.is_active = true;
        request.setBody(body);
    }
}
"""

def ensure_trigger(container, container_name: str) -> None:
    """Create or replace the pre-trigger to add is_active field (operation = All)."""
    try:
        container.scripts.create_trigger(
            body={
                "id": TRIGGER_ID,
                "body": TRIGGER_BODY,
                "triggerType": "Pre",
                "triggerOperation": "All"
            }
        )
        print(f"[trigger] Created '{TRIGGER_ID}' for {container_name}")
    except Exception as e:
        if getattr(e, "status_code", None) == 409:
            container.scripts.replace_trigger(
                trigger=TRIGGER_ID,
                body={
                    "id": TRIGGER_ID,
                    "body": TRIGGER_BODY,
                    "triggerType": "Pre",
                    "triggerOperation": "All"
                }
            )
            print(f"[trigger] Replaced '{TRIGGER_ID}' for {container_name}")
        else:
            raise

# ---------- Data loading ----------
def load_articles(path_str: str) -> List[Dict[str, Any]]:
    """Load articles from JSON file. Accepts list or an object with 'Articles'/'articles'."""
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        articles = data
    elif isinstance(data, dict):
        if "Articles" in data and isinstance(data["Articles"], list):
            articles = data["Articles"]
        elif "articles" in data and isinstance(data["articles"], list):
            articles = data["articles"]
        else:
            raise ValueError("JSON must be a list or contain 'Articles'/'articles' array.")
    else:
        raise ValueError("Unsupported JSON structure for articles.")

    # Remove Cosmos system properties if present (they break writes)
    for a in articles:
        for sys in ("_rid", "_self", "_etag", "_attachments", "_ts"):
            a.pop(sys, None)
    return articles

def load_users(path_str: str) -> List[Dict[str, Any]]:
    """Load users from JSON file. Returns empty list if file doesn't exist."""
    path = Path(path_str)
    if not path.exists():
        print(f"[info] Users file not found: {path}. Skipping users processing.")
        return []

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        users = data
    elif isinstance(data, dict):
        if "Users" in data and isinstance(data["Users"], list):
            users = data["Users"]
        elif "users" in data and isinstance(data["users"], list):
            users = data["users"]
        else:
            raise ValueError("JSON must be a list or contain 'Users'/'users' array.")
    else:
        raise ValueError("Unsupported JSON structure for users.")

    # Remove Cosmos system properties if present (they break writes)
    for u in users:
        for sys in ("_rid", "_self", "_etag", "_attachments", "_ts"):
            u.pop(sys, None)
    return users

# ---------- Partition-key helpers ----------
def get_pk_path(container) -> str:
    """Read container PK path, defaulting to '/id'."""
    props = container.read()
    return props.get("partitionKey", {}).get("paths", ["/id"])[0]

def resolve_pk_value(doc: Dict[str, Any], pk_path: str) -> Any:
    """Resolve nested partition key value from a document given a path like '/author_id' or '/user/pk'."""
    node: Any = doc
    for seg in pk_path.lstrip("/").split("/"):
        if isinstance(node, dict) and seg in node:
            node = node[seg]
        else:
            raise ValueError(f"Document {doc.get('id')} is missing partition key property '{pk_path}'")
    return node

# ---------- Bulk upsert with trigger ----------
def bulk_upsert_with_trigger(container, docs: List[Dict[str, Any]], container_name: str) -> None:
    pk_path = get_pk_path(container)
    total = len(docs)
    done = 0
    created_or_replaced = 0

    for d in docs:
        # Ensure id exists
        if "id" not in d:
            raise ValueError("Every document must have an 'id' field.")

        # Verify the document has the partition key property required by the container
        _ = resolve_pk_value(d, pk_path)  # raises if missing; value comes from body for upsert

        # Upsert WITH the pre-trigger included (this is the key point)
        try:
            # Most SDK versions: do NOT pass `partition_key` for create/upsert
            res = container.upsert_item(
                body=d,
                pre_trigger_include=[TRIGGER_ID]
            )
        except TypeError:
            # Some newer versions accept partition_key; fall back if needed
            pk_val = resolve_pk_value(d, pk_path)
            res = container.upsert_item(
                body=d,
                partition_key=pk_val,
                pre_trigger_include=[TRIGGER_ID]
            )

        created_or_replaced += 1
        done += 1
        if done % 50 == 0 or done == total:
            print(f"[progress] {container_name}: {done}/{total} upserted")

    print(f"[summary] Upserted {created_or_replaced} {container_name} documents with pre-trigger '{TRIGGER_ID}'")

# ---------- Verification ----------
def verify_any(container, docs: List[Dict[str, Any]], container_name: str) -> None:
    """Read back one of the docs and show is_active."""
    if not docs:
        print(f"[verify] No documents to verify for {container_name}")
        return
        
    pk_path = get_pk_path(container)
    sample = docs[0]
    pk_val = resolve_pk_value(sample, pk_path)
    back = container.read_item(item=sample["id"], partition_key=pk_val)
    print(f"[verify] {container_name} - id={back['id']} is_active={back.get('is_active')}")

    # Count how many items still miss is_active (should be 0 for the ones you just upserted)
    q = "SELECT VALUE COUNT(1) FROM c WHERE NOT IS_DEFINED(c.is_active)"
    missing = list(container.query_items(q, enable_cross_partition_query=True))
    # The SDK returns [count] for VALUE COUNT(1)
    if missing:
        print(f"[verify] {container_name} - Items missing is_active: {missing[0]}")

# ---------- Main ----------
def main():
    # Setup triggers for both containers
    ensure_trigger(articles_container, "articles")
    ensure_trigger(users_container, "users")
    
    # Load and process articles
    articles = load_articles(ARTICLES_PATH)
    print(f"[load] Loaded {len(articles)} articles from {ARTICLES_PATH}")
    
    # Load users from separate file
    users = load_users(USERS_PATH)
    if users:
        print(f"[load] Loaded {len(users)} users from {USERS_PATH}")
    else:
        print(f"[info] No users data found or users file doesn't exist")
    
    # Bulk upsert articles
    bulk_upsert_with_trigger(articles_container, articles, "articles")
    verify_any(articles_container, articles, "articles")
    
    # Bulk upsert users
    if users:
        bulk_upsert_with_trigger(users_container, users, "users")
        verify_any(users_container, users, "users")
    else:
        print("[info] No users to upsert")

if __name__ == "__main__":
    main()
