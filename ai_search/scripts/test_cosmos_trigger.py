"""
Minimal trigger test using azure-cosmos
- Reads .env
- Ensures trigger exists (Pre, All)
- Upserts the document with pre_trigger_include so trigger runs
- Reads back and prints is_active
"""
import os
import json
from dotenv import load_dotenv
from azure.cosmos import CosmosClient

load_dotenv()

ENDPOINT = os.environ["COSMOS_ENDPOINT"]
KEY = os.environ["COSMOS_KEY"]
DB_ID = os.environ["COSMOS_DB"]
CONTAINER_ID = os.environ["COSMOS_ARTICLES"]

client = CosmosClient(ENDPOINT, KEY)
db = client.get_database_client(DB_ID)
container = db.get_container_client(CONTAINER_ID)

# 1) Ensure the pre-trigger exists (Pre + All)
TRIGGER_ID = "addIsActiveField"
TRIGGER_BODY = """
function addIsActiveField() {
    var context = getContext();
    var request = context.getRequest();
    var body = request.getBody();
    if (!body) { throw new Error("Document body must be provided."); }
    if (typeof body === "string") { body = JSON.parse(body); }
    if (typeof body !== "object") { throw new Error("Document body must be an object."); }
    if (!Object.prototype.hasOwnProperty.call(body, "is_active")) {
        body.is_active = true;
        request.setBody(body);
    }
}
"""

try:
    container.scripts.create_trigger(
        body={
            "id": TRIGGER_ID,
            "body": TRIGGER_BODY,
            "triggerType": "Pre",
            "triggerOperation": "All"
        }
    )
    print(f"Created trigger '{TRIGGER_ID}'.")
except Exception as e:
    # If already exists, replace to ensure latest body
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
        print(f"Replaced trigger '{TRIGGER_ID}'.")
    else:
        raise

# 2) Your sample document (no is_active -> trigger should add it)
doc = {
    "id": "18042004-e576-40f2-8633-5f73b35c7c90",
    "title": "Quang Phu Dep Trai",
    "content": "Quang Phu Dep Trai supercute vippro",
    "abstract": "Quang Phu Dep Trai is a comprehensive overview of transformers in natural language processing",
    "status": "published",
    "tags": ["deep-learning","language-models","nlp","transformers"],
    "author_id": "48762781-bf56-42ef-bbf9-1e5e5961c79e",
    "author_name": "David Jackson",
    "likes": 0,
    "dislikes": 0,
    "views": 107,
    "created_at": "2022-04-04 18:36:24",
    "updated_at": "2022-04-06 15:11:46",
    "image": "https://picsum.photos/seed/9c31fa31-a09a-4f87-bfe3-d2d7f893ca71/800/400"
}

# 3) Resolve partition key value from container definition
props = container.read()
pk_path = props.get("partitionKey", {}).get("paths", ["/id"])[0]
segments = pk_path.lstrip("/").split("/")
pk_value = doc
for seg in segments:
    if isinstance(pk_value, dict) and seg in pk_value:
        pk_value = pk_value[seg]
    else:
        raise ValueError(f"Document is missing partition key property '{pk_path}'")

# 4) Upsert WITH the pre-trigger so it runs
created = container.upsert_item(
    body=doc,
    pre_trigger_include=[TRIGGER_ID]
)

print("Created/replaced item:", {"id": created["id"], "is_active": created.get("is_active")})

# 5) Read back to verify
read_back = container.read_item(item=doc["id"], partition_key=pk_value)
print("Read back is_active =", read_back.get("is_active"))

# 6) Test with users container - add a user document
USERS_CONTAINER_ID = os.environ["COSMOS_USERS"]
users_container = db.get_container_client(USERS_CONTAINER_ID)

# Ensure trigger exists for users container too
try:
    users_container.scripts.create_trigger(
        body={
            "id": TRIGGER_ID,
            "body": TRIGGER_BODY,
            "triggerType": "Pre",
            "triggerOperation": "All"
        }
    )
    print(f"Created trigger '{TRIGGER_ID}' for users container.")
except Exception as e:
    if getattr(e, "status_code", None) == 409:
        users_container.scripts.replace_trigger(
            trigger=TRIGGER_ID,
            body={
                "id": TRIGGER_ID,
                "body": TRIGGER_BODY,
                "triggerType": "Pre",
                "triggerOperation": "All"
            }
        )
        print(f"Replaced trigger '{TRIGGER_ID}' for users container.")
    else:
        raise

# 7) Sample user document (no is_active -> trigger should add it)
user_doc = {
    "id": "phu-dep-zai-001",
    "full_name": "Phu Dep Zai",
    "email": "quangphunguyen1804@gmail.com",
    "password": "$2a$12$p34tQS7nvA45iVbOV0hmSusrOVhYO69eDZ3zTsQi0ZSzUtSwL87x2",
    "avatar_url": "https://i.pravatar.cc/150?img=42",
    "role": "admin",
    "created_at": "2025-08-19 15:15:00",
    "liked_articles": [],
    "disliked_articles": [],
    "bookmarked_articles": [],
    "following": [],
    "followers": []
}

# 8) Resolve partition key for users container
users_props = users_container.read()
users_pk_path = users_props.get("partitionKey", {}).get("paths", ["/id"])[0]
users_segments = users_pk_path.lstrip("/").split("/")
users_pk_value = user_doc
for seg in users_segments:
    if isinstance(users_pk_value, dict) and seg in users_pk_value:
        users_pk_value = users_pk_value[seg]
    else:
        raise ValueError(f"User document is missing partition key property '{users_pk_path}'")

# 9) Upsert user WITH the pre-trigger so it runs
created_user = users_container.upsert_item(
    body=user_doc,
    pre_trigger_include=[TRIGGER_ID]
)

print("Created/replaced user:", {"id": created_user["id"], "full_name": created_user["full_name"], "is_active": created_user.get("is_active")})

# 10) Read back user to verify
read_back_user = users_container.read_item(item=user_doc["id"], partition_key=users_pk_value)
print("Read back user is_active =", read_back_user.get("is_active"))
