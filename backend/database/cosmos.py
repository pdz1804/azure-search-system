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

# Debug: Print environment variables (remove in production)
print(f"🔍 Cosmos Config: ENDPOINT={ENDPOINT}, DB={DATABASE_NAME}, ARTICLES={ARTICLES_CONTAINER}, USERS={USERS_CONTAINER}")

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

    # Validate required environment variables
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

        print("✅ Connected to Azure Cosmos DB")


async def close_cosmos():
    """Close the Cosmos async client and clear module references.

    Properly awaiting client.close() prevents unclosed aiohttp sessions
    and related warnings during application shutdown.
    """
    global client, database, articles, users
    try:
        if client:
            # Azure Cosmos async client exposes an async close
            await client.close()
    except Exception as e:
        print(f"Error closing Cosmos client: {e}")
    finally:
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
