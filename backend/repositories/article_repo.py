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
    try:
        return await articles.read_item(item=article_id, partition_key=article_id)
    except Exception:
        return None

async def update_article(article_id: str, update_doc: dict) -> dict:
    articles = await get_articles()
    try:
        existing_article = await articles.read_item(item=article_id, partition_key=article_id)
        existing_article.update(update_doc)
        updated = await articles.upsert_item(body=existing_article)
        return updated
    except Exception as e:
        print(f"Error updating article: {e}")
        raise 


async def delete_article(article_id: str):
    articles = await get_articles()
    await articles.delete_item(item=article_id, partition_key=article_id)


async def list_articles(page: int = 1, page_size: int = 20) -> Dict:
    articles = await get_articles()
    count_query = "SELECT VALUE COUNT(1) FROM c"
    count_result = [item async for item in articles.query_items(
        query=count_query
    )]
    total_items = count_result[0] if count_result else 0
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    skip = (page - 1) * page_size
    data_query = f"SELECT * FROM c OFFSET {skip} LIMIT {page_size}"

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
    article["likes"] = current_likes + 1
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
    article["likes"] = current_likes - 1
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


async def search_response(data: response_ai) -> List[dict]:
    articles = await get_articles()

    query = "SELECT * FROM c WHERE CONTAINS(c.title, @searchTerm) OR CONTAINS(c.content, @searchTerm)"
    parameters = [{"name": "@searchTerm", "value": data.searchTerm}]

    results = []
    async for doc in articles.query_items(query=query, parameters=parameters):
        results.append(doc)

    return results
