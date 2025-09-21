import math
from typing import Dict, Optional, List
from backend.database.cosmos import get_articles_container

async def get_articles():
    return await get_articles_container()

async def insert_article(doc: dict):
    articles = await get_articles()
    await articles.create_item(body=doc)
    return doc["id"]

async def get_article_by_id(article_id: str, app_id: Optional[str] = None) -> Optional[dict]:
    articles = await get_articles()
    
    if app_id:
        query = "SELECT * FROM c WHERE c.id = @id AND c.is_active = true AND c.app_id = @app_id"
        parameters = [{"name": "@id", "value": article_id}, {"name": "@app_id", "value": app_id}]
    else:
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
        existing_article = await articles.read_item(item=article_id, partition_key=article_id)

        existing_article.update(update_doc)

        updated = await articles.upsert_item(body=existing_article)
        
        return updated
    except Exception as e:
        raise 

async def delete_article(article_id: str):
    articles = await get_articles()
    doc = await articles.read_item(item=article_id, partition_key=article_id)
    doc["is_active"] = False
    await articles.replace_item(item=article_id, body=doc)

async def list_articles(page: int = 1, page_size: int = 20, app_id: Optional[str] = None) -> Dict:
    articles = await get_articles()
    
    if app_id:
        count_query = "SELECT VALUE COUNT(1) FROM c WHERE c.is_active = true AND c.app_id = @app_id"
        count_parameters = [{"name": "@app_id", "value": app_id}]
    else:
        count_query = "SELECT VALUE COUNT(1) FROM c WHERE c.is_active = true"
        count_parameters = []
        
    count_result = [item async for item in articles.query_items(
        query=count_query,
        parameters=count_parameters
    )]
    total_items = count_result[0] if count_result else 0
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    skip = (page - 1) * page_size
    
    if app_id:
        data_query = f"SELECT * FROM c WHERE c.is_active = true AND c.app_id = @app_id ORDER BY c.created_at DESC OFFSET {skip} LIMIT {page_size}"
        data_parameters = [{"name": "@app_id", "value": app_id}]
    else:
        data_query = f"SELECT * FROM c WHERE c.is_active = true ORDER BY c.created_at DESC OFFSET {skip} LIMIT {page_size}"
        data_parameters = []

    results = []
    async for doc in articles.query_items(
        query=data_query,
        parameters=data_parameters
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

async def get_article_by_author(author_id: str, page: int = 1, page_size: int = 20, app_id: Optional[str] = None) -> Dict:
    articles = await get_articles()  

    if app_id:
        count_query = "SELECT VALUE COUNT(1) FROM c WHERE c.author_id = @author_id AND c.is_active = true AND c.app_id = @app_id"
        count_parameters = [{"name": "@author_id", "value": author_id}, {"name": "@app_id", "value": app_id}]
    else:
        count_query = "SELECT VALUE COUNT(1) FROM c WHERE c.author_id = @author_id AND c.is_active = true"
        count_parameters = [{"name": "@author_id", "value": author_id}]
        
    count_result = [item async for item in articles.query_items(query=count_query, parameters=count_parameters)]
    total_items = count_result[0] if count_result else 0
    total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1

    results = []
    skip = (page - 1) * page_size
    take = page_size
    index = 0

    if app_id:
        data_query = "SELECT * FROM c WHERE c.author_id = @author_id AND c.is_active = true AND c.app_id = @app_id ORDER BY c.created_at DESC"
        data_parameters = [{"name": "@author_id", "value": author_id}, {"name": "@app_id", "value": app_id}]
    else:
        data_query = "SELECT * FROM c WHERE c.author_id = @author_id AND c.is_active = true ORDER BY c.created_at DESC"
        data_parameters = [{"name": "@author_id", "value": author_id}]
        
    async for doc in articles.query_items(query=data_query, parameters=data_parameters):
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

async def get_author_stats(author_id: str, app_id: Optional[str] = None) -> Dict:
    articles = await get_articles()
    
    if app_id:
        data_query = "SELECT * FROM c WHERE c.author_id = @author_id AND c.is_active = true AND c.app_id = @app_id"
        parameters = [{"name": "@author_id", "value": author_id}, {"name": "@app_id", "value": app_id}]
    else:
        data_query = "SELECT * FROM c WHERE c.author_id = @author_id AND c.is_active = true"
        parameters = [{"name": "@author_id", "value": author_id}]

    total_items = 0
    total_views = 0
    total_likes = 0

    try:
        async for doc in articles.query_items(query=data_query, parameters=parameters):
            try:
                total_items += 1
                total_views += int(doc.get('views', 0) or 0)
                total_likes += int(doc.get('likes', 0) or 0)
            except Exception:
                total_items += 1
                continue
    except Exception:
        return {"articles_count": 0, "total_views": 0, "total_likes": 0}

    return {"articles_count": total_items, "total_views": total_views, "total_likes": total_likes}

async def get_articles_by_ids(article_ids: List[str], app_id: Optional[str] = None):
    articles_repo = await get_articles()

    if not article_ids:
        return []

    ids_placeholders = ", ".join([f"@id{i}" for i in range(len(article_ids))])
    parameters = [{"name": f"@id{i}", "value": id_} for i, id_ in enumerate(article_ids)]

    query = f"SELECT * FROM c WHERE c.id IN ({ids_placeholders}) AND c.is_active = true"
    
    if app_id:
        query += " AND c.app_id = @app_id"
        parameters.append({"name": "@app_id", "value": app_id})

    results = []
    async for doc in articles_repo.query_items(query=query, parameters=parameters):
        results.append(doc)

    order_map = {id_: idx for idx, id_ in enumerate(article_ids)}
    results.sort(key=lambda x: order_map.get(x['id'], len(article_ids)))

    return results

async def get_categories_with_counts(app_id: Optional[str] = None) -> List[Dict]:
    articles = await get_articles()
    
    categories_result = []
    from collections import Counter
    tag_counter = Counter()

    async for item in articles.read_all_items():
        try:
            if not item or not item.get('is_active'):
                continue
            if app_id and item.get('app_id') != app_id:
                continue
            tags = item.get('tags') or []
            for t in tags:
                tag_counter[t] += 1
        except Exception:
            continue

    for tag, count in tag_counter.most_common(10):
        categories_result.append({"name": tag, "count": count})
    
    return categories_result

async def get_articles_by_category(
    category_name: str,
    page: int = 1,
    limit: int = 10,
    app_id: Optional[str] = None
) -> Dict:
    articles = await get_articles()
    
    if app_id:
        query = """
        SELECT * FROM c 
        WHERE c.is_active = true 
        AND ARRAY_CONTAINS(c.tags, @category)
        AND c.app_id = @app_id
        ORDER BY c.created_at DESC
        OFFSET @skip LIMIT @limit
        """
    else:
        query = """
        SELECT * FROM c 
        WHERE c.is_active = true 
        AND ARRAY_CONTAINS(c.tags, @category)
        ORDER BY c.created_at DESC
        OFFSET @skip LIMIT @limit
        """
    
    skip = (page - 1) * limit
    parameters = [
        {"name": "@category", "value": category_name},
        {"name": "@skip", "value": skip},
        {"name": "@limit", "value": limit}
    ]
    if app_id:
        parameters.append({"name": "@app_id", "value": app_id})
    
    results = []
    async for doc in articles.query_items(query=query, parameters=parameters):
        results.append(doc)
    
    count_query = "SELECT VALUE COUNT(1) FROM c WHERE c.status = 'true'"
    if category_name != "all":
        count_query += " AND ARRAY_CONTAINS(c.tags, @category)"
    if app_id:
        count_query += " AND c.app_id = @app_id"
    
    count_parameters = []
    if category_name != "all":
        count_parameters.append({"name": "@category", "value": category_name})
    if app_id:
        count_parameters.append({"name": "@app_id", "value": app_id})
    
    total_items = 0
    async for count in articles.query_items(query=count_query, parameters=count_parameters):
        total_items = count
        break
    
    total_pages = math.ceil(total_items / limit) if total_items > 0 else 1
    
    return {
        "items": results,
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": limit
    }

async def get_total_articles_count_by_author(author_id: str, app_id: Optional[str] = None) -> int:
    try:
        articles = await get_articles()
        
        if app_id:
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.author_id = @author_id AND c.is_active = true AND c.app_id = @app_id"
            parameters = [{"name": "@author_id", "value": author_id}, {"name": "@app_id", "value": app_id}]
        else:
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.author_id = @author_id AND c.is_active = true"
            parameters = [{"name": "@author_id", "value": author_id}]
        
        async for count in articles.query_items(query=query, parameters=parameters):
            return count
        return 0
    except Exception:
        return 0

async def get_total_articles_count(app_id: Optional[str] = None) -> int:
    try:
        articles = await get_articles()
        
        if app_id:
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.is_active = true AND c.app_id = @app_id"
            parameters = [{"name": "@app_id", "value": app_id}]
        else:
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.is_active = true"
            parameters = []
            
        async for count in articles.query_items(query=query, parameters=parameters):
            return count
        return 0
    except Exception:
        return 0

async def get_article_summary_counts(app_id: Optional[str] = None) -> Dict:
    try:
        articles = await get_articles()

        base_filter = "c.is_active = true"
        parameters = []
        if app_id:
            base_filter += " AND c.app_id = @app_id"
            parameters = [{"name": "@app_id", "value": app_id}]

        results = {}
        
        total_query = f"SELECT VALUE COUNT(1) FROM c WHERE {base_filter}"
        async for count in articles.query_items(query=total_query, parameters=parameters):
            results["total"] = count
            break
        
        published_query = f"SELECT VALUE COUNT(1) FROM c WHERE {base_filter} AND c.status = 'published'"
        async for count in articles.query_items(query=published_query, parameters=parameters):
            results["published"] = count
            break
        
        draft_query = f"SELECT VALUE COUNT(1) FROM c WHERE {base_filter} AND c.status = 'draft'"
        async for count in articles.query_items(query=draft_query, parameters=parameters):
            results["draft"] = count
            break
        
        authors_query = f"SELECT c.author_id FROM c WHERE {base_filter} AND IS_DEFINED(c.author_id)"
        unique_authors = set()
        async for item in articles.query_items(query=authors_query, parameters=parameters):
            if item.get("author_id"):
                unique_authors.add(item["author_id"])
        results["authors"] = len(unique_authors)

        return {
            "total_articles": results.get("total", 0),
            "published_articles": results.get("published", 0),
            "draft_articles": results.get("draft", 0),
            "authors": results.get("authors", 0),
        }

    except Exception as e:
        return {
            "total_articles": 0,
            "published_articles": 0,
            "draft_articles": 0,
            "authors": 0,
        }

async def get_article_summary_aggregations(app_id: Optional[str] = None) -> Dict:
    try:
        articles = await get_articles()

        base_filter = "c.is_active = true"
        parameters = []
        if app_id:
            base_filter += " AND c.app_id = @app_id"
            parameters = [{"name": "@app_id", "value": app_id}]

        try:
            views_query = f"SELECT VALUE SUM(IS_NUMBER(c.views) ? c.views : 0) FROM c WHERE {base_filter}"
            total_views = 0
            async for result in articles.query_items(query=views_query, parameters=parameters):
                total_views = int(result) if result is not None else 0
                break
            
            likes_query = f"SELECT VALUE SUM(IS_NUMBER(c.likes) ? c.likes : 0) FROM c WHERE {base_filter}"
            total_likes = 0
            async for result in articles.query_items(query=likes_query, parameters=parameters):
                total_likes = int(result) if result is not None else 0
                break

        except Exception as aggregation_error:
            
            query = f"SELECT c.views, c.likes FROM c WHERE {base_filter}"
            
            total_views = 0
            total_likes = 0
            
            async for item in articles.query_items(query=query, parameters=parameters):
                total_views += int(item.get("views", 0) or 0)
                total_likes += int(item.get("likes", 0) or 0)

        return {
            "total_views": total_views,
            "total_likes": total_likes,
        }

    except Exception as e:
        return {"total_views": 0, "total_likes": 0}

async def count_articles(app_id: Optional[str] = None) -> int:
    """
    Count total number of active articles.
    
    Args:
        app_id: Optional app ID filter
        
    Returns:
        Total count of active articles
    """
    articles = await get_articles()
    
    try:
        if app_id:
            query = "SELECT VALUE COUNT(1) FROM c WHERE c.app_id = @app_id"
            parameters = [{"name": "@app_id", "value": app_id}]
        else:
            query = "SELECT VALUE COUNT(1) FROM c"
            parameters = []
        
        count_result = [item async for item in articles.query_items(
            query=query,
            parameters=parameters
        )]
        
        return count_result[0] if count_result else 0
        
    except Exception as e:
        return 0

async def get_articles_batch(offset: int, batch_size: int, app_id: Optional[str] = None) -> List[dict]:
    """
    Get a batch of articles for processing.
    
    Args:
        offset: Number of articles to skip
        batch_size: Number of articles to return
        app_id: Optional app ID filter
        
    Returns:
        List of article documents
    """
    articles = await get_articles()
    
    try:
        if app_id:
            query = "SELECT * FROM c WHERE c.app_id = @app_id ORDER BY c.created_at OFFSET @offset LIMIT @limit"
            parameters = [
                {"name": "@app_id", "value": app_id},
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": batch_size}
            ]
        else:
            query = "SELECT * FROM c ORDER BY c.created_at OFFSET @offset LIMIT @limit"
            parameters = [
                {"name": "@offset", "value": offset},
                {"name": "@limit", "value": batch_size}
            ]
        
        results = [doc async for doc in articles.query_items(
            query=query,
            parameters=parameters
        )]
        
        return results
        
    except Exception as e:
        return []

async def remove_field_from_article(article_id: str, field_name: str) -> bool:
    """
    Remove a specific field from an article.
    
    Args:
        article_id: The ID of the article to update
        field_name: The name of the field to remove
        
    Returns:
        bool: True if successful, False otherwise
    """
    articles = await get_articles()
    try:
        existing_article = await articles.read_item(item=article_id, partition_key=article_id)
        
        if field_name in existing_article:
            del existing_article[field_name]
            
            await articles.upsert_item(body=existing_article)
            return True
        else:
            return True
            
    except Exception as e:
        return False
