"""Repository layer for articles.

This module performs direct data access against the Cosmos DB
`articles` container. All SQL/queries and container operations live
here so the service layer above can remain database-agnostic.
"""

from calendar import c
import math
import re
from typing import Dict, Optional, List
from backend.api import article
from backend.database.cosmos import get_articles_container
from backend.model.request import response_ai
# from backend.database.mongo import get_db


async def get_articles():
    return await get_articles_container()

async def insert_article(doc: dict):
    articles = await get_articles()
    await articles.create_item(body=doc)
    return doc["id"]



async def get_article_by_id(article_id: str) -> Optional[dict]:
    articles = await get_articles()
    
    query = "SELECT * FROM c WHERE c.id = @id AND c.is_active = true"
    parameters = [{"name": "@id", "value": article_id}]
    
    try:
        results = [doc async for doc in articles.query_items(
            query=query,
            parameters=parameters
        )]
        return results[0] if results else None
    except Exception:
        return None

async def update_article(article_id: str, update_doc: dict) -> dict:
    articles = await get_articles()
    try:
        print(f"🔍 Repository: Reading existing article {article_id} from Cosmos DB")
        existing_article = await articles.read_item(item=article_id, partition_key=article_id)
        
        print(f"📋 Repository: Original article keys: {list(existing_article.keys())}")
        print(f"📝 Repository: Applying update with keys: {list(update_doc.keys())}")
        
        # Apply the updates to the existing article
        existing_article.update(update_doc)
        
        print(f"🔄 Repository: About to upsert article to Cosmos DB")
        print(f"✅ Repository: Article now has recommended field: {'recommended' in existing_article}")
        print(f"📅 Repository: Article now has recommended_time field: {'recommended_time' in existing_article}")
        
        # Upsert the updated article back to Cosmos DB
        updated = await articles.upsert_item(body=existing_article)
        
        print(f"✅ Repository: Successfully upserted article to Cosmos DB")
        print(f"🔍 Repository: Returned article has recommended: {'recommended' in updated}")
        print(f"🔍 Repository: Returned article has recommended_time: {'recommended_time' in updated}")
        
        if 'recommended_time' in updated:
            print(f"⏰ Repository: Final recommended_time value: {updated.get('recommended_time')}")
        
        return updated
    except Exception as e:
        print(f"❌ Repository: Error updating article {article_id}: {e}")
        print(f"❌ Repository: Exception type: {type(e).__name__}")
        raise 


async def delete_article(article_id: str):
    articles = await get_articles()
    doc = await articles.read_item(item=article_id, partition_key=article_id)
    doc["is_active"] = False
    await articles.replace_item(item=article_id, body=doc)


async def list_articles(page: int = 1, page_size: int = 20) -> Dict:
    articles = await get_articles()
    count_query = "SELECT VALUE COUNT(1) FROM c  WHERE c.is_active = true"
    count_result = [item async for item in articles.query_items(
        query=count_query
    )]
    total_items = count_result[0] if count_result else 0
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    skip = (page - 1) * page_size
    data_query = f"SELECT * FROM c  WHERE c.is_active = true ORDER BY c.created_at DESC OFFSET {skip} LIMIT {page_size}"

    results = []
    async for doc in articles.query_items(
        query=data_query
    ):
        results.append(doc)

    return {
        "items": results,
        "totalItems": total_items,
        "totalPages": total_pages,
        "currentPage": page,
        "pageSize": page_size
    }
    


async def increment_article_views(article_id: str):
    articles = await get_articles()
    article = await articles.read_item(
        item=article_id,
        partition_key=article_id
    )
    current_views = article.get("views", 0)
    article["views"] = current_views + 1
    await articles.upsert_item(body=article)

async def increment_article_likes(article_id: str):
    articles = await get_articles()
    article = await articles.read_item(
        item=article_id,
        partition_key=article_id
    )
    current_likes = article.get("likes", 0)
    print(f"Current likes before increment: {current_likes}")
    article["likes"] = current_likes + 1
    print(f"Likes after increment: {article['likes']}")
    await articles.upsert_item(body=article)

async def increment_article_dislikes(article_id: str):
    articles = await get_articles()
    article = await articles.read_item(
        item=article_id,
        partition_key=article_id
    )
    current_dislikes = article.get("dislikes", 0)
    article["dislikes"] = current_dislikes + 1
    await articles.upsert_item(body=article)

async def decrement_article_likes(article_id: str):
    articles = await get_articles()
    article = await articles.read_item(
        item=article_id,
        partition_key=article_id
    )
    current_likes = article.get("likes", 0)
    print(f"Current likes before decrement: {current_likes}")
    article["likes"] = current_likes - 1
    print(f"Likes after decrement: {article['likes']}")
    await articles.upsert_item(body=article)

async def decrement_article_dislikes(article_id: str):
    articles = await get_articles()
    article = await articles.read_item(
        item=article_id,
        partition_key=article_id
    )
    current_dislikes = article.get("dislikes", 0)
    article["dislikes"] = current_dislikes - 1
    await articles.upsert_item(body=article)

# async def add_user_article_reaction(article_id: str, user_id: str, reaction_type: str):
#     """Add a user's reaction (like/dislike) to an article"""
#     db = get_db()
#     await db["article_reactions"].insert_one({
#         "article_id": ObjectId(article_id),
#         "user_id": ObjectId(user_id),
#         "reaction_type": reaction_type,
#     })

# async def remove_user_article_reaction(article_id: str, user_id: str, reaction_type: str):
#     """Remove a user's reaction from an article"""
#     db = get_db()
#     await db["article_reactions"].delete_one({
#         "article_id": ObjectId(article_id),
#         "user_id": ObjectId(user_id),
#         "reaction_type": reaction_type
#     })

# async def get_user_article_reaction(article_id: str, user_id: str, reaction_type: str):
#     """Check if user has already reacted to an article"""
#     db = get_db()
#     return await db["article_reactions"].find_one({
#         "article_id": ObjectId(article_id),
#         "user_id": ObjectId(user_id),
#         "reaction_type": reaction_type
#     })

async def get_article_by_author(author_id: str, page: int = 1, page_size: int = 20) -> Dict:
    articles = await get_articles()  

    count_query = "SELECT VALUE COUNT(1) FROM c WHERE c.author_id = @author_id"
    parameters = [{"name": "@author_id", "value": author_id}]
    count_result = [item async for item in articles.query_items(query=count_query, parameters=parameters)]
    total_items = count_result[0] if count_result else 0
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    results = []
    skip = (page - 1) * page_size
    take = page_size
    index = 0

    data_query = "SELECT * FROM c WHERE c.author_id = @author_id"
    async for doc in articles.query_items(query=data_query, parameters=parameters):
        if index >= skip and len(results) < take:
            results.append(doc)
        index += 1

    return {
        "items": results,
        "totalItems": total_items,
        "totalPages": total_pages,
        "currentPage": page,
        "pageSize": page_size
    }


async def get_author_stats(author_id: str) -> Dict:
    """Return simple stats for an author by scanning their articles and summing fields in code.

    We avoid server-side aggregation to support partitioned Cosmos containers where some aggregate
    queries may be restricted. This reads the author's active articles and computes counts locally.
    """
    articles = await get_articles()
    data_query = "SELECT * FROM c WHERE c.author_id = @author_id AND c.is_active = true"
    parameters = [{"name": "@author_id", "value": author_id}]

    total_items = 0
    total_views = 0

    try:
        async for doc in articles.query_items(query=data_query, parameters=parameters):
            try:
                total_items += 1
                total_views += int(doc.get('views', 0) or 0)
            except Exception:
                # If a document is malformed, skip its numeric contribution but still count it
                total_items += 1
                continue
    except Exception:
        # On any error, return zeros so caller can fallback
        return {"articles_count": 0, "total_views": 0}

    return {"articles_count": total_items, "total_views": total_views}


async def get_articles_by_ids(article_ids: List[str]):
    articles_repo = await get_articles()

    if not article_ids:
        return []

    ids_placeholders = ", ".join([f"@id{i}" for i in range(len(article_ids))])
    parameters = [{"name": f"@id{i}", "value": id_} for i, id_ in enumerate(article_ids)]

    query = f"SELECT * FROM c WHERE c.id IN ({ids_placeholders}) AND c.is_active = true"

    results = []
    async for doc in articles_repo.query_items(query=query, parameters=parameters):
        results.append(doc)

    order_map = {id_: idx for idx, id_ in enumerate(article_ids)}
    results.sort(key=lambda x: order_map.get(x['id'], len(article_ids)))

    return results
