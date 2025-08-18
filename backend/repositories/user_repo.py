from typing import Optional
from backend.database.cosmos import get_users_container

async def get_users():
    return await get_users_container()

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
    return await users.read_item(item=user_id, partition_key=user_id)

async def insert(doc: dict):
    users = await get_users()
    return await users.create_item(body=doc)

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

        followee = get_user_by_id(followee_id)
        if not followee:
            return False
        followee["followers"] = [f for f in followee.get("followers", []) if f != follower_id]
        await users.upsert_item(body=followee)

        return True
    except Exception:
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
        users.upsert_item(body=user)
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
        bookmarks = set(user.get("bookmarked_articles", []))
        bookmarks.add(article_id)
        user["bookmarked_articles"] = list(bookmarks)
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


