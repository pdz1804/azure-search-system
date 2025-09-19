import os
from dotenv import load_dotenv
from azure.cosmos import PartitionKey
from azure.cosmos.aio import CosmosClient

load_dotenv()

ENDPOINT = os.getenv("COSMOS_ENDPOINT")
KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = os.getenv("COSMOS_DB")
ARTICLES_CONTAINER = os.getenv("COSMOS_ARTICLES")
USERS_CONTAINER = os.getenv("COSMOS_USERS")

client: CosmosClient = None
database = None
articles = None
users = None


async def connect_cosmos():
    global client, database, articles, users

    if not all([ENDPOINT, KEY, DATABASE_NAME, ARTICLES_CONTAINER, USERS_CONTAINER]):
        missing = []
        if not ENDPOINT: missing.append("COSMOS_ENDPOINT")
        if not KEY: missing.append("COSMOS_KEY") 
        if not DATABASE_NAME: missing.append("COSMOS_DB")
        if not ARTICLES_CONTAINER: missing.append("COSMOS_ARTICLES")
        if not USERS_CONTAINER: missing.append("COSMOS_USERS")
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    if client is None:
        client = CosmosClient(ENDPOINT, credential=KEY)
        database = await client.create_database_if_not_exists(DATABASE_NAME)

        articles = await database.create_container_if_not_exists(
            id=ARTICLES_CONTAINER,
            partition_key=PartitionKey(path="/id")
        )

        users = await database.create_container_if_not_exists(
            id=USERS_CONTAINER,
            partition_key=PartitionKey(path="/id")
        )


async def close_cosmos():
    global client, database, articles, users
    try:
        if client:
            await client.close()
    except Exception:
        pass
    finally:
        client = None
        database = None
        articles = None
        users = None


async def get_articles_container():
    if articles is None:
        await connect_cosmos()
    return articles


async def get_users_container():
    if users is None:
        await connect_cosmos()
    return users
