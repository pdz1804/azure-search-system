"""
Factory functions for Azure Search clients.
Provides consistent client creation pattern for different index types.

CURRENT IMPLEMENTATION: Simplified single index approach
OLD IMPLEMENTATION: Chunking with parent and child indexes (commented out for easy restoration)
"""

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from ai_search.config.settings import SETTINGS

# ==========================================
# OLD IMPLEMENTATION: Parent + Chunks Index (COMMENTED OUT)
# ==========================================
# To restore chunking functionality, uncomment this and comment out the NEW IMPLEMENTATION below:
#
# def articles_client() -> tuple[SearchClient, SearchClient]:
#     """
#     Create SearchClients for both articles-index (parent) and articles-chunks-index (child).
#     
#     Returns:
#         tuple: (parent_client, chunks_client) for multi-index chunking approach
#         
#     Raises:
#         Exception: If client creation fails
#     """
#     print("🔧 Creating articles search clients...")
#     try:
#         parent = SearchClient(SETTINGS.search_endpoint, "articles-index", AzureKeyCredential(SETTINGS.search_key))
#         chunks = SearchClient(SETTINGS.search_endpoint, "articles-chunks-index", AzureKeyCredential(SETTINGS.search_key))
#         print(f"✅ Articles clients created: parent=articles-index, chunks=articles-chunks-index")
#         return parent, chunks
#     except Exception as e:
#         print(f"❌ Failed to create articles clients: {e}")
#         raise

# ==========================================
# NEW IMPLEMENTATION: Single Articles Index
# ==========================================
def articles_client() -> SearchClient:
    """
    Create a SearchClient for the articles-index only (simplified implementation).
    
    Returns:
        SearchClient: Configured client for articles index
        
    Raises:
        Exception: If client creation fails
    """
    print("🔧 Creating articles search client...")
    try:
        client = SearchClient(SETTINGS.search_endpoint, "articles-index", AzureKeyCredential(SETTINGS.search_key))
        print(f"✅ Articles client created: articles-index")
        return client
    except Exception as e:
        print(f"❌ Failed to create articles client: {e}")
        raise

def authors_client() -> SearchClient:
    """
    Create a SearchClient for the authors-index.
    
    Returns:
        SearchClient: Configured client for authors index
        
    Raises:
        Exception: If client creation fails
    """
    print("🔧 Creating authors search client...")
    try:
        client = SearchClient(SETTINGS.search_endpoint, "authors-index", AzureKeyCredential(SETTINGS.search_key))
        print(f"✅ Authors client created: {SETTINGS.search_endpoint}/authors-index")
        return client
    except Exception as e:
        print(f"❌ Failed to create authors client: {e}")
        raise
