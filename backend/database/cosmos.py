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

# Cosmos client and container references are kept in module-level globals
# so they can be lazily initialized and reused across requests. These are
# asynchronous clients from azure.cosmos.aio.
client: CosmosClient = None
database = None
articles = None
users = None


async def connect_cosmos():
    """Create the CosmosClient and container references.

    This is called during app startup (see `backend.main`) and will
    create the database and containers if they do not exist.
    """
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
    """Release references to the Cosmos client and containers.

    The async Cosmos client does not require an explicit close in this
    project; clearing module-level references is sufficient for the
    short-running dev server scenario. If using a long-lived process or
    a different SDK version, implement proper close() calls here.
    """
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
