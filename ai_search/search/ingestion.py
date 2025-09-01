"""
Ingest Cosmos -> Azure AI Search with embeddings and business_date.
"""

from typing import Dict, Any, List
from datetime import datetime
from azure.cosmos import CosmosClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

from ai_search.config.settings import SETTINGS
from ai_search.app.services.embeddings import encode
from ai_search.utils.timeparse import parse_sql_datetime
from ai_search.utils.text_preprocessing import generate_preprocessed_content

def _article_to_doc(a: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a Cosmos DB article document to optimized Azure AI Search format."""
    title = a.get("title", "")
    abstract = a.get("abstract", "")
    content = a.get("content", "")
    
    # Use preprocessed text if available, otherwise generate it
    preprocessed_text = a.get("preprocessed_searchable_text")
    if not preprocessed_text:
        preprocessed_text = generate_preprocessed_content(a)
        print(f"🔄 Generated preprocessed text for article {a.get('id', 'unknown')}: {len(preprocessed_text)} chars")
    
    # Use preprocessed text for search, keep original for fallback
    searchable_text = preprocessed_text if preprocessed_text else "\n".join([title, abstract, content]).strip()

    updated = a.get("updated_at")
    created = a.get("created_at")
    try:
        business_date: datetime = (
            parse_sql_datetime(updated) if updated else (
                parse_sql_datetime(created) if created else datetime.utcnow()
            )
        )
    except Exception:
        business_date = datetime.utcnow()

    # Only include fields that exist in the optimized index schema
    doc = {
        "id": a["id"],
        "title": title,
        "abstract": abstract,
        "content": content,
        "author_name": a.get("author_name"),
        "status": a.get("status"),
        "tags": a.get("tags", []),
        "created_at": parse_sql_datetime(created) if created else None,
        "updated_at": parse_sql_datetime(updated) if updated else None,
        "business_date": business_date,
        "searchable_text": searchable_text,
        "preprocessed_searchable_text": preprocessed_text,
    }
    
    if SETTINGS.enable_embeddings:
        try:
            # Use preprocessed text for embeddings for better quality
            embedding_text = preprocessed_text if preprocessed_text else searchable_text
            doc["content_vector"] = encode(embedding_text)
        except Exception as e:
            print(f"⚠️ Failed to generate embedding for article {a.get('id', 'unknown')}: {e}")
            doc["content_vector"] = [0.0] * 384  # Fallback empty vector
    
    return doc

def _author_to_doc(u: Dict[str, Any]) -> Dict[str, Any]:
    """Transform a Cosmos DB user document to optimized Azure AI Search author format."""
    full_name = u.get("full_name", "")
    
    # Only include fields that exist in the optimized index schema
    doc = {
        "id": u["id"],
        "full_name": full_name,
        "role": u.get("role"),
        "created_at": parse_sql_datetime(u["created_at"]) if u.get("created_at") else None,
        "searchable_text": full_name,
    }
    
    if SETTINGS.enable_embeddings:
        try:
            doc["name_vector"] = encode(full_name)
        except Exception as e:
            print(f"⚠️ Failed to generate embedding for author {u.get('id', 'unknown')}: {e}")
            doc["name_vector"] = [0.0] * 384  # Fallback empty vector
    
    return doc

def ingest(batch_size: int = 100, verbose: bool = False) -> None:
    """Ingest data from Cosmos DB into Azure AI Search indexes."""
    print("📦 Starting data ingestion from Cosmos DB...")
    print(f"📋 Settings: batch_size={batch_size}, verbose={verbose}, enable_embeddings={SETTINGS.enable_embeddings}")
    
    try:
        # Initialize Cosmos DB clients
        print("🌌 Connecting to Cosmos DB...")
        cosmos = CosmosClient(SETTINGS.cosmos_endpoint, SETTINGS.cosmos_key)
        db = cosmos.get_database_client(SETTINGS.cosmos_db)
        c_articles = db.get_container_client(SETTINGS.cosmos_articles)
        c_users = db.get_container_client(SETTINGS.cosmos_users)
        print("✅ Cosmos DB connection established")

        # Initialize Search clients
        print("🔍 Connecting to Azure AI Search...")
        sc_articles = SearchClient(SETTINGS.search_endpoint, "articles-index", AzureKeyCredential(SETTINGS.search_key))
        sc_authors  = SearchClient(SETTINGS.search_endpoint, "authors-index",  AzureKeyCredential(SETTINGS.search_key))
        print("✅ Azure AI Search connection established")

        # Articles ingestion
        print("📖 Ingesting articles...")
        batch: List[Dict[str, Any]] = []
        articles_count = 0
        batches_uploaded = 0
        
        for item in c_articles.read_all_items():
            if verbose:
                print(f"🔄 Processing article: {item.get('title', item.get('id', 'unknown'))}")
            
            batch.append(_article_to_doc(item))
            articles_count += 1
            
            if len(batch) >= batch_size:
                if verbose:
                    print(f"📤 Uploading batch of {len(batch)} articles...")
                try:
                    result = sc_articles.upload_documents(batch)
                    if verbose:
                        success_count = sum(1 for r in result if r.succeeded)
                        failed_count = len(result) - success_count
                        print(f"📊 Upload results: {success_count} succeeded, {failed_count} failed")
                        if failed_count > 0:
                            for r in result:
                                if not r.succeeded:
                                    print(f"❌ Failed to upload article {r.key}: {r.error_message}")
                    batches_uploaded += 1
                    print(f"✅ Uploaded batch {batches_uploaded} ({len(batch)} articles)")
                except Exception as e:
                    print(f"❌ Failed to upload articles batch: {e}")
                    raise
                batch.clear()
        
        # Upload remaining articles
        if batch: 
            if verbose:
                print(f"📤 Uploading final batch of {len(batch)} articles...")
            try:
                result = sc_articles.upload_documents(batch)
                if verbose:
                    success_count = sum(1 for r in result if r.succeeded)
                    failed_count = len(result) - success_count
                    print(f"📊 Final batch results: {success_count} succeeded, {failed_count} failed")
                    if failed_count > 0:
                        for r in result:
                            if not r.succeeded:
                                print(f"❌ Failed to upload article {r.key}: {r.error_message}")
                batches_uploaded += 1
                print(f"✅ Uploaded final batch ({len(batch)} articles)")
            except Exception as e:
                print(f"❌ Failed to upload final articles batch: {e}")
                raise
        
        print(f"✅ Articles ingestion complete: {articles_count} total articles in {batches_uploaded} batches")

        # Authors ingestion
        print("👥 Ingesting authors...")
        batch = []
        authors_count = 0
        batches_uploaded = 0
        
        for item in c_users.read_all_items():
            if verbose:
                print(f"🔄 Processing author: {item.get('full_name', item.get('id', 'unknown'))}")
            
            batch.append(_author_to_doc(item))
            authors_count += 1
            
            if len(batch) >= batch_size:
                if verbose:
                    print(f"📤 Uploading batch of {len(batch)} authors...")
                try:
                    result = sc_authors.upload_documents(batch)
                    if verbose:
                        success_count = sum(1 for r in result if r.succeeded)
                        failed_count = len(result) - success_count
                        print(f"📊 Upload results: {success_count} succeeded, {failed_count} failed")
                        if failed_count > 0:
                            for r in result:
                                if not r.succeeded:
                                    print(f"❌ Failed to upload author {r.key}: {r.error_message}")
                    batches_uploaded += 1
                    print(f"✅ Uploaded batch {batches_uploaded} ({len(batch)} authors)")
                except Exception as e:
                    print(f"❌ Failed to upload authors batch: {e}")
                    raise
                batch.clear()
        
        # Upload remaining authors
        if batch: 
            if verbose:
                print(f"📤 Uploading final batch of {len(batch)} authors...")
            try:
                result = sc_authors.upload_documents(batch)
                if verbose:
                    success_count = sum(1 for r in result if r.succeeded)
                    failed_count = len(result) - success_count
                    print(f"📊 Final batch results: {success_count} succeeded, {failed_count} failed")
                    if failed_count > 0:
                        for r in result:
                            if not r.succeeded:
                                print(f"❌ Failed to upload author {r.key}: {r.error_message}")
                batches_uploaded += 1
                print(f"✅ Uploaded final batch ({len(batch)} authors)")
            except Exception as e:
                print(f"❌ Failed to upload final authors batch: {e}")
                raise
        
        print(f"✅ Authors ingestion complete: {authors_count} total authors in {batches_uploaded} batches")
        
        # Verify documents were indexed by checking document counts
        print("🔍 Verifying document counts in indexes...")
        try:
            # Give some time for indexing to complete
            import time
            time.sleep(2)
            
            # Check articles count
            articles_result = sc_articles.search("*", top=1, include_total_count=True)
            articles_indexed = getattr(articles_result, '_total_count', 0)
            print(f"📊 Articles index now contains: {articles_indexed} documents")
            
            # Check authors count  
            authors_result = sc_authors.search("*", top=1, include_total_count=True)
            authors_indexed = getattr(authors_result, '_total_count', 0)
            print(f"📊 Authors index now contains: {authors_indexed} documents")
            
            if articles_indexed == 0 and authors_indexed == 0:
                print("⚠️ Warning: No documents found in indexes. This might indicate an indexing delay or error.")
            elif articles_indexed < articles_count or authors_indexed < authors_count:
                print(f"⚠️ Warning: Document counts don't match. Expected {articles_count} articles, {authors_count} authors")
            else:
                print("✅ Document counts verified successfully")
                
        except Exception as e:
            print(f"⚠️ Could not verify document counts: {e}")
        
        print("🎉 Data ingestion completed successfully!")
        
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        raise

def ingest_data(verbose: bool = False, batch_size: int = 100) -> None:
    """Main function for CLI ingestion."""
    ingest(batch_size=batch_size, verbose=verbose)



