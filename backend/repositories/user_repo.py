"""Repository functions that read/write user documents in Cosmos DB.

Encapsulates Cosmos-specific queries so services can call simple
functions like `get_by_email`, `follow_user`, `like_article`, etc.
"""

from typing import Optional
from backend.database.cosmos import get_users_container


async def get_users():
    return await get_users_container()

async def get_list_user(app_id: Optional[str] = None):
    users = await get_users()
    
    # Note: Users don't have app_id directly, but we can filter users who have articles in the specified app
    # For now, we'll return all users since users are shared across apps, but in the service layer
    # we'll filter their stats by app_id
    query = "SELECT * FROM c"
    parameters = []
    results = []
    async for item in users.query_items(
        query=query,
        parameters=parameters
    ):
        results.append(item)
    return results

async def get_by_email(email: str) -> Optional[dict]:
    users = await get_users()
    query = "SELECT * FROM c WHERE c.email = @email"
    parameters = [{"name": "@email", "value": email}]
    
    results = []
    async for item in users.query_items(
        query=query,
        parameters=parameters
    ):
        results.append(item)

    return results[0] if results else None
    

async def get_by_full_name(full_name: str) -> Optional[dict]:
    users = await get_users()
    query = "SELECT * FROM c WHERE c.full_name = @full_name"
    parameters = [{"name": "@full_name", "value": full_name}]

    results = []
    async for item in users.query_items(
        query=query,
        parameters=parameters
    ):
        results.append(item)

    return results[0] if results else None

async def get_user_by_id(user_id: str) -> Optional[dict]:
    users = await get_users()
    query = "SELECT * FROM c WHERE c.id = @user_id"
    parameters = [{"name": "@user_id", "value": user_id}]
    
    results = []
    async for item in users.query_items(
        query=query,
        parameters=parameters
    ):
        results.append(item)

    return results[0] if results else None

async def insert(doc: dict):
    users = await get_users()
    return await users.create_item(body=doc)


async def update_user(user_id: str, update_data: dict) -> Optional[dict]:
    """Update user document in Cosmos DB"""
    try:
        users = await get_users()
        
        # Get the existing user document
        existing_user = await get_user_by_id(user_id)
        if not existing_user:
            return None
        
        # Update the user document with new data
        for key, value in update_data.items():
            existing_user[key] = value
        
        # Use upsert to update the document
        updated_user = await users.upsert_item(body=existing_user)
        return updated_user
        
    except Exception as e:
        print(f"Error updating user in repository: {e}")
        raise

async def follow_user(follower_id: str, followee_id: str) -> bool:
    users = await get_users()
    try:
        follower = await get_user_by_id(follower_id)
        if not follower:
            return False
        following = set(follower.get("following", []))
        if followee_id in following:
            return False  # Already following
        following.add(followee_id)
        follower["following"] = list(following)
        await users.upsert_item(body=follower)

        followee = await get_user_by_id(followee_id)
        if not followee:
            return False
        followers = set(followee.get("followers", []))
        followers.add(follower_id)
        followee["followers"] = list(followers)
        await users.upsert_item(body=followee)

        return True
    except Exception:
        return False


async def unfollow_user(follower_id: str, followee_id: str) -> bool:
    users = await get_users()
    try:
        follower = await get_user_by_id(follower_id)
        if not follower:
            return False
        follower["following"] = [f for f in follower.get("following", []) if f != followee_id]
        await users.upsert_item(body=follower)

        followee = await get_user_by_id(followee_id)
        if not followee:
            return False
        followee["followers"] = [f for f in followee.get("followers", []) if f != follower_id]
        await users.upsert_item(body=followee)

        return True
    except Exception as e:
        print(f"Error unfollowing user: {e}")
        return False


async def check_follow_status(follower_id: str, followee_id: str) -> bool:
    users = await get_users()
    try:
        follower = await get_user_by_id(follower_id)
        if not follower:
            return False
        return followee_id in follower.get("following", [])
    except Exception:
        return False


async def like_article(user_id: str, article_id: str) -> bool:
    users = await get_users()
    try:
        user = await get_user_by_id(user_id)
        liked = set(user.get("liked_articles", []))
        liked.add(article_id)
        user["liked_articles"] = list(liked)
        await users.upsert_item(body=user)
        return True
    except Exception:
        return False


async def unlike_article(user_id: str, article_id: str) -> bool:
    users = await get_users()
    try:
        user = await get_user_by_id(user_id)
        user["liked_articles"] = [a for a in user.get("liked_articles", []) if a != article_id]
        await users.upsert_item(body=user)
        return True
    except Exception:
        return False


async def dislike_article(user_id: str, article_id: str) -> bool:
    users = await get_users()
    try:
        user = await get_user_by_id(user_id)
        disliked = set(user.get("disliked_articles", []))
        disliked.add(article_id)
        user["disliked_articles"] = list(disliked)
        await users.upsert_item(body=user)
        return True
    except Exception:
        return False


async def undislike_article(user_id: str, article_id: str) -> bool:
    users = await get_users()
    try:
        user = await get_user_by_id(user_id)
        user["disliked_articles"] = [a for a in user.get("disliked_articles", []) if a != article_id]
        await users.upsert_item(body=user)
        return True
    except Exception:
        return False


async def bookmark_article(user_id: str, article_id: str) -> bool:
    users = await get_users()
    try:
        user = await get_user_by_id(user_id)
        bookmarked = set(user.get("bookmarked_articles", []))
        bookmarked.add(article_id)
        user["bookmarked_articles"] = list(bookmarked)
        await users.upsert_item(body=user)
        return True
    except Exception:
        return False


async def unbookmark_article(user_id: str, article_id: str) -> bool:
    users = await get_users()
    try:
        user = await get_user_by_id(user_id)
        user["bookmarked_articles"] = [a for a in user.get("bookmarked_articles", []) if a != article_id]
        await users.upsert_item(body=user)
        return True
    except Exception:
        return False


async def get_users_by_ids(user_ids: list) -> list:
    users = await get_users()
    if not user_ids:
        return []
    ids_placeholders = ", ".join([f"@id{i}" for i in range(len(user_ids))])
    parameters = [{"name": f"@id{i}", "value": id_} for i, id_ in enumerate(user_ids)]

    query = f"SELECT * FROM c WHERE c.id IN ({ids_placeholders}) AND c.is_active = true"

    results = []
    async for doc in users.query_items(query=query, parameters=parameters):
        results.append(doc)

    order_map = {id_: idx for idx, id_ in enumerate(user_ids)}
    results.sort(key=lambda x: order_map.get(x['id'], len(user_ids)))

    return results
    