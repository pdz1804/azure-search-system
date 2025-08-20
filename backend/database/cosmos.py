import os
from dotenv import load_dotenv
from azure.cosmos import PartitionKey
from azure.cosmos.aio import CosmosClient

load_dotenv()

ENDPOINT = os.getenv("ENDPOINT")
KEY = os.getenv("KEY")
DATABASE_NAME = os.getenv("DATABASE_NAME")
ARTICLES_CONTAINER = os.getenv("ARTICLES_CONTAINER")
USERS_CONTAINER = os.getenv("USERS_CONTAINER")

client: CosmosClient = None
database = None
articles = None
users = None

async def connect_cosmos():
    global client, database, articles, users

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

        print("✅ Connected to Azure Cosmos DB")


def close_cosmos():
    """CosmosClient không có async close, chỉ cần xóa tham chiếu."""
    global client, database, articles, users
    client = None
    database = None
    articles = None
    users = None
    print("🛑 Cosmos DB connection closed")


async def get_articles_container():
    if articles is None:
        await connect_cosmos()
    return articles


async def get_users_container():
    if users is None:
        await connect_cosmos()
    return users
