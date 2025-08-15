"""
Factory functions for Azure Search clients.
"""

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from config.settings import SETTINGS

def articles_client() -> SearchClient:
    """Create a SearchClient for the articles-index."""
    print("🔧 Creating articles search client...")
    try:
        client = SearchClient(SETTINGS.search_endpoint, "articles-index", AzureKeyCredential(SETTINGS.search_key))
        print(f"✅ Articles client created: {SETTINGS.search_endpoint}/articles-index")
        return client
    except Exception as e:
        print(f"❌ Failed to create articles client: {e}")
        raise

def authors_client() -> SearchClient:
    """Create a SearchClient for the authors-index."""
    print("🔧 Creating authors search client...")
    try:
        client = SearchClient(SETTINGS.search_endpoint, "authors-index", AzureKeyCredential(SETTINGS.search_key))
        print(f"✅ Authors client created: {SETTINGS.search_endpoint}/authors-index")
        return client
    except Exception as e:
        print(f"❌ Failed to create authors client: {e}")
        raise


