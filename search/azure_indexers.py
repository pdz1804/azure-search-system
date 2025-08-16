"""
Azure AI Search Native Indexers for Cosmos DB Integration.

This module implements Azure-native indexers that automatically sync data from Cosmos DB
to Azure AI Search without requiring custom Change Feed processors or background services.
The indexers run entirely within Azure services and handle all CRUD operations automatically.

Design Pattern: Factory Pattern for creating indexers and data sources.
"""

import json
from typing import Dict, Any, List, Optional
from azure.search.documents.indexes import SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndexerDataContainer,
    SearchIndexerDataSourceConnection,
    SearchIndexer,
    IndexingSchedule,
    IndexingParameters,
    FieldMapping,
    OutputFieldMappingEntry,
    SearchIndexerSkillset,
    WebApiSkill,
    InputFieldMappingEntry,
)

# Try to import AzureOpenAIEmbeddingSkill - fallback to WebApiSkill if not available
try:
    from azure.search.documents.indexes.models import AzureOpenAIEmbeddingSkill
    print("✅ AzureOpenAIEmbeddingSkill available")
    AZURE_OPENAI_SKILL_AVAILABLE = True
except ImportError:
    AZURE_OPENAI_SKILL_AVAILABLE = False
    print("⚠️ AzureOpenAIEmbeddingSkill not available, using WebApiSkill fallback")
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError, HttpResponseError

from config.settings import SETTINGS


class AzureIndexerManager:
    """
    Manages Azure AI Search indexers for automatic Cosmos DB synchronization.
    
    This class provides methods to create, configure, and manage Azure-native indexers
    that automatically sync data from Cosmos DB containers to search indexes without
    requiring any custom code or background processes.
    """
    
    def __init__(self):
        """Initialize the indexer client."""
        self.client = SearchIndexerClient(
            SETTINGS.search_endpoint,
            AzureKeyCredential(SETTINGS.search_key)
        )
    
    def create_cosmos_data_source(self, name: str, container_name: str, query: Optional[str] = None) -> SearchIndexerDataSourceConnection:
        """
        Create a Cosmos DB data source for Azure AI Search indexer.
        
        Args:
            name: Name of the data source
            container_name: Cosmos DB container name
            query: Optional SQL query to filter documents
            
        Returns:
            Created data source connection
        """
        # Construct Cosmos DB connection string
        cosmos_connection_string = (
            f"AccountEndpoint={SETTINGS.cosmos_endpoint};"
            f"AccountKey={SETTINGS.cosmos_key};"
            f"Database={SETTINGS.cosmos_db}"
        )
        
        # Create data container configuration
        container = SearchIndexerDataContainer(
            name=container_name,
            query=query
        )
        
        # Create data source
        data_source = SearchIndexerDataSourceConnection(
            name=name,
            type="cosmosdb",
            connection_string=cosmos_connection_string,
            container=container,
            description=f"Cosmos DB data source for {container_name} container"
        )
        
        return data_source
    
    def create_articles_indexer(self) -> SearchIndexer:
        """
        Create an indexer for articles with field mappings and automatic scheduling.
        
        Returns:
            Configured articles indexer
        """
        # Field mappings from Cosmos DB to search index
        field_mappings = [
            FieldMapping(source_field_name="id", target_field_name="id"),
            FieldMapping(source_field_name="title", target_field_name="title"),
            FieldMapping(source_field_name="abstract", target_field_name="abstract"),
            FieldMapping(source_field_name="content", target_field_name="content"),
            FieldMapping(source_field_name="author_name", target_field_name="author_name"),
            FieldMapping(source_field_name="status", target_field_name="status"),
            FieldMapping(source_field_name="tags", target_field_name="tags"),
            FieldMapping(source_field_name="created_at", target_field_name="created_at"),
            FieldMapping(source_field_name="updated_at", target_field_name="updated_at"),
            # business_date and searchable_text will be set by output field mappings
        ]
        
        # Output field mappings for computed fields (using raw dict due to SDK/API mismatch)
        output_field_mappings = [
            # Set searchable_text to content
            {
                "sourceFieldName": "/document/content",
                "targetFieldName": "searchable_text"
            }
        ]
        
        # For business_date, we'll add a field mapping in the field_mappings list
        # Since we can't use conditional logic in the indexer directly
        field_mappings.append(FieldMapping(source_field_name="updated_at", target_field_name="business_date"))
        
        # Add output field mappings for embedding skills if enabled
        if SETTINGS.enable_embeddings and SETTINGS.embedding_provider.lower() == "openai":
            # Use raw dict to match REST API schema
            output_field_mappings.append({
                "sourceFieldName": "/document/content_vector",
                "targetFieldName": "content_vector"
            })
        
        # Indexing parameters for high-water mark change detection
        # Note: No configuration needed for Cosmos DB (dataToExtract/parsingMode not supported)
        parameters = IndexingParameters(
            batch_size=100,
            max_failed_items=10,
            max_failed_items_per_batch=5
            # No configuration parameter for Cosmos DB - parsing configs not supported
        )
        
        # Schedule for automatic runs (every 5 minutes)
        schedule = IndexingSchedule(interval="PT5M")  # ISO 8601 duration format
        
        # Create indexer with skillset if embeddings enabled
        if SETTINGS.enable_embeddings:
            indexer = SearchIndexer(
                name="articles-indexer",
                data_source_name="articles-datasource",
                target_index_name="articles-index",
                skillset_name="articles-skillset",
                field_mappings=field_mappings,
                output_field_mappings=output_field_mappings,
                parameters=parameters,
                schedule=schedule,
                description="Automatic indexer for articles from Cosmos DB"
            )
        else:
            indexer = SearchIndexer(
                name="articles-indexer",
                data_source_name="articles-datasource",
                target_index_name="articles-index",
                field_mappings=field_mappings,
                parameters=parameters,
                schedule=schedule,
                description="Automatic indexer for articles from Cosmos DB"
            )
        
        return indexer
    
    def create_authors_indexer(self) -> SearchIndexer:
        """
        Create an indexer for authors with field mappings and automatic scheduling.
        
        Returns:
            Configured authors indexer
        """
        # Field mappings from Cosmos DB to search index
        field_mappings = [
            FieldMapping(source_field_name="id", target_field_name="id"),
            FieldMapping(source_field_name="full_name", target_field_name="full_name"),
            FieldMapping(source_field_name="role", target_field_name="role"),
            FieldMapping(source_field_name="created_at", target_field_name="created_at"),
        ]
        
        # Output field mappings for computed fields (using raw dict due to SDK/API mismatch)
        output_field_mappings = [
            # Set searchable_text to full_name
            {
                "sourceFieldName": "/document/full_name",
                "targetFieldName": "searchable_text"
            }
        ]
        
        # No output field mappings - placeholder skills don't map to index fields
        
        # Indexing parameters
        # Note: No configuration needed for Cosmos DB (dataToExtract/parsingMode not supported)
        parameters = IndexingParameters(
            batch_size=100,
            max_failed_items=10,
            max_failed_items_per_batch=5
            # No configuration parameter for Cosmos DB - parsing configs not supported
        )
        
        # Schedule for automatic runs (every 5 minutes)
        schedule = IndexingSchedule(interval="PT5M")
        
        # Create indexer with skillset if embeddings enabled
        if SETTINGS.enable_embeddings:
            indexer = SearchIndexer(
                name="authors-indexer",
                data_source_name="authors-datasource",
                target_index_name="authors-index",
                skillset_name="authors-skillset",
                field_mappings=field_mappings,
                output_field_mappings=output_field_mappings,
                parameters=parameters,
                schedule=schedule,
                description="Automatic indexer for authors from Cosmos DB"
            )
        else:
            indexer = SearchIndexer(
                name="authors-indexer",
                data_source_name="authors-datasource",
                target_index_name="authors-index",
                field_mappings=field_mappings,
                parameters=parameters,
                schedule=schedule,
                description="Automatic indexer for authors from Cosmos DB"
            )
        
        return indexer
    
    def create_articles_skillset(self) -> SearchIndexerSkillset:
        """
        Create a skillset for articles to compute derived fields and embeddings.
        
        Returns:
            Configured skillset for articles processing
        """
        # Simple text processing skill that works reliably
        skills = []
        
        if SETTINGS.enable_embeddings and SETTINGS.embedding_provider.lower() == "openai":
            # Use proper AzureOpenAIEmbeddingSkill if available, otherwise fallback to WebApiSkill
            if AZURE_OPENAI_SKILL_AVAILABLE:
                print("✅ AzureOpenAIEmbeddingSkill available in skillset of articles-indexer")
                embedding_skill = AzureOpenAIEmbeddingSkill(
                    name="generate-embeddings",
                    description="Generate embeddings using Azure OpenAI",
                    context="/document",
                    resource_url=SETTINGS.azure_openai_endpoint,
                    api_key=SETTINGS.azure_openai_key,
                    deployment_name=SETTINGS.azure_openai_model_name,
                    model_name=SETTINGS.azure_openai_model_name,
                    inputs=[
                        InputFieldMappingEntry(name="text", source="/document/content")
                    ],
                    outputs=[
                        OutputFieldMappingEntry(name="embedding", target_name="content_vector")
                    ]
                )
                skills.append(embedding_skill)
            else:
                # Fallback to WebApiSkill for Azure OpenAI REST API
                embedding_skill = WebApiSkill(
                    name="generate-embeddings",
                    description="Generate embeddings using Azure OpenAI REST API",
                    context="/document",
                    uri=f"{SETTINGS.azure_openai_endpoint}openai/deployments/{SETTINGS.azure_openai_deployment}/embeddings?api-version=2024-12-01-preview",
                    http_method="POST",
                    timeout="PT60S",
                    batch_size=10,
                    degree_of_parallelism=1,
                    inputs=[
                        InputFieldMappingEntry(name="input", source="/document/content")
                    ],
                    outputs=[
                        OutputFieldMappingEntry(name="embedding", target_name="content_vector")
                    ],
                    http_headers={
                        "Authorization": f"Bearer {SETTINGS.azure_openai_key}" if SETTINGS.azure_openai_key else None
                    }
                )
                skills.append(embedding_skill)
        # For now, use simple skillset without index projections
        # Index projections require specific index schema with parent_id field
        skillset = SearchIndexerSkillset(
            name="articles-skillset",
            description="Skillset for processing articles data with embeddings",
            skills=skills
        )
        
        return skillset
    
    def create_authors_skillset(self) -> SearchIndexerSkillset:
        """
        Create a skillset for authors to compute derived fields and embeddings.
        
        Returns:
            Configured skillset for authors processing
        """
        # Simple skillset for authors - add basic text processing skill
        skills = []
        
        if SETTINGS.enable_embeddings and SETTINGS.embedding_provider.lower() == "openai":
            # Use proper AzureOpenAIEmbeddingSkill for author names if available
            if AZURE_OPENAI_SKILL_AVAILABLE:
                print("✅ AzureOpenAIEmbeddingSkill available in skillset of authors-indexer")
                embedding_skill = AzureOpenAIEmbeddingSkill(
                    name="generate-author-embeddings",
                    description="Generate embeddings for author names using Azure OpenAI",
                    context="/document",
                    resource_url=SETTINGS.azure_openai_endpoint,
                    deployment_name=SETTINGS.azure_openai_model_name,
                    model_name=SETTINGS.azure_openai_model_name,
                    api_key=SETTINGS.azure_openai_key,
                    inputs=[
                        InputFieldMappingEntry(name="text", source="/document/full_name")
                    ],
                    outputs=[
                        OutputFieldMappingEntry(name="embedding", target_name="name_vector")
                    ]
                )
                skills.append(embedding_skill)
            else:
                # Fallback to WebApiSkill for Azure OpenAI REST API
                embedding_skill = WebApiSkill(
                    name="generate-author-embeddings",
                    description="Generate embeddings for author names using Azure OpenAI REST API",
                    context="/document",
                    uri=f"{SETTINGS.azure_openai_endpoint}openai/deployments/{SETTINGS.azure_openai_deployment}/embeddings?api-version=2024-12-01-preview",
                    http_method="POST",
                    timeout="PT60S",
                    batch_size=10,
                    degree_of_parallelism=1,
                    inputs=[
                        InputFieldMappingEntry(name="input", source="/document/full_name")
                    ],
                    outputs=[
                        OutputFieldMappingEntry(name="embedding", target_name="name_vector")
                    ],
                    http_headers={
                        "Authorization": f"Bearer {SETTINGS.azure_openai_key}" if SETTINGS.azure_openai_key else None
                    }
                )
                skills.append(embedding_skill)
        
        # Create skillset
        skillset = SearchIndexerSkillset(
            name="authors-skillset",
            description="Skillset for processing authors data",
            skills=skills
        )
        
        return skillset
    
    def setup_indexers(self, reset: bool = False, verbose: bool = False) -> None:
        """
        Set up all indexers, data sources, and skillsets for automatic sync.
        
        Args:
            reset: Whether to delete existing resources before creating new ones
            verbose: Enable verbose logging
        """
        if verbose:
            print("🔧 Setting up Azure AI Search indexers for automatic Cosmos DB sync...")
        
        try:
            # Delete existing resources if reset is requested
            if reset:
                self._cleanup_indexers(verbose)
            
            # 1. Create or update data sources
            if verbose:
                print("📊 Creating/updating Cosmos DB data sources...")
            
            articles_ds = self.create_cosmos_data_source(
                "articles-datasource", 
                SETTINGS.cosmos_articles,
                "SELECT * FROM c WHERE c._ts >= @HighWaterMark ORDER BY c._ts"
            )
            
            authors_ds = self.create_cosmos_data_source(
                "authors-datasource", 
                SETTINGS.cosmos_users,
                "SELECT * FROM c WHERE c._ts >= @HighWaterMark ORDER BY c._ts"
            )
            
            self._create_or_update_data_source(articles_ds, verbose)
            self._create_or_update_data_source(authors_ds, verbose)
            
            if verbose:
                print("✅ Data sources configured successfully")
            
            # 2. Create or update skillsets if embeddings are enabled
            if SETTINGS.enable_embeddings:
                if verbose:
                    print("🧠 Creating/updating skillsets for content processing...")
                
                articles_skillset = self.create_articles_skillset()
                authors_skillset = self.create_authors_skillset()
                
                self._create_or_update_skillset(articles_skillset, verbose)
                self._create_or_update_skillset(authors_skillset, verbose)
                
                if verbose:
                    print("✅ Skillsets configured successfully")
            else:
                if verbose:
                    print("⚠️ Embeddings disabled - using basic indexing without computed fields")
            
            # 3. Create or update indexers
            if verbose:
                print("⚙️ Creating/updating indexers...")
            
            articles_indexer = self.create_articles_indexer()
            authors_indexer = self.create_authors_indexer()
            
            self._create_or_update_indexer(articles_indexer, verbose)
            self._create_or_update_indexer(authors_indexer, verbose)
            
            if verbose:
                print("✅ Indexers configured successfully")
            
            # 4. Run indexers once to populate data
            if verbose:
                print("🚀 Running initial indexing...")
            
            self.client.run_indexer("articles-indexer")
            self.client.run_indexer("authors-indexer")
            
            if verbose:
                print("✅ Initial indexing started")
                print("🔄 Indexers are now configured to run automatically every 5 minutes")
                print("📈 Data will be automatically synchronized from Cosmos DB to Azure AI Search")
            
        except Exception as e:
            print(f"❌ Failed to setup indexers: {e}")
            raise
    
    def _cleanup_indexers(self, verbose: bool = False) -> None:
        """Clean up existing indexers, skillsets, and data sources."""
        if verbose:
            print("🧹 Cleaning up existing indexer resources...")
        
        resources_to_delete = [
            ("indexer", ["articles-indexer", "authors-indexer"]),
            ("skillset", ["articles-skillset", "authors-skillset"]),
            ("data_source_connection", ["articles-datasource", "authors-datasource"])
        ]
        
        for resource_type, names in resources_to_delete:
            for name in names:
                try:
                    if resource_type == "indexer":
                        self.client.delete_indexer(name)
                    elif resource_type == "skillset":
                        self.client.delete_skillset(name)
                    elif resource_type == "data_source_connection":
                        self.client.delete_data_source_connection(name)
                    
                    if verbose:
                        print(f"🗑️ Deleted {resource_type}: {name}")
                        
                except ResourceNotFoundError:
                    if verbose:
                        print(f"ℹ️ {resource_type} {name} not found (already deleted)")
                except Exception as e:
                    if verbose:
                        print(f"⚠️ Failed to delete {resource_type} {name}: {e}")
    
    def _create_or_update_data_source(self, data_source: SearchIndexerDataSourceConnection, verbose: bool = False) -> None:
        """
        Create or update a data source connection.
        
        Args:
            data_source: The data source to create or update
            verbose: Enable verbose logging
        """
        try:
            self.client.create_data_source_connection(data_source)
            if verbose:
                print(f"   ✅ Created data source: {data_source.name}")
        except ResourceExistsError as e:
            # Resource already exists, update it instead
            if verbose:
                print(f"   🔍 Data source {data_source.name} already exists, updating...")
            try:
                self.client.create_or_update_data_source_connection(data_source)
                if verbose:
                    print(f"   🔄 Updated existing data source: {data_source.name}")
            except Exception as update_error:
                print(f"   ❌ Failed to update data source {data_source.name}: {update_error}")
                print(f"   🔍 Update error type: {type(update_error).__name__}")
                raise
        except HttpResponseError as e:
            # Check if it's a resource exists error in HTTP response
            if e.status_code == 409 or "already exists" in str(e).lower():
                if verbose:
                    print(f"   🔍 HTTP 409 or 'already exists' detected for {data_source.name}, updating...")
                try:
                    self.client.create_or_update_data_source_connection(data_source)
                    if verbose:
                        print(f"   🔄 Updated existing data source: {data_source.name}")
                except Exception as update_error:
                    print(f"   ❌ Failed to update data source {data_source.name}: {update_error}")
                    print(f"   🔍 Update error type: {type(update_error).__name__}")
                    raise
            else:
                print(f"   ❌ HTTP error creating data source {data_source.name}: {e}")
                print(f"   🔍 HTTP error details: status={e.status_code}, message={e.message}")
                raise
        except Exception as e:
            print(f"   ❌ Failed to create data source {data_source.name}: {e}")
            print(f"   🔍 Exception type: {type(e).__name__}")
            print(f"   🔍 Exception details: {str(e)}")
            raise
    
    def _create_or_update_skillset(self, skillset: SearchIndexerSkillset, verbose: bool = False) -> None:
        """
        Create or update a skillset.
        
        Args:
            skillset: The skillset to create or update
            verbose: Enable verbose logging
        """
        try:
            self.client.create_skillset(skillset)
            if verbose:
                print(f"   ✅ Created skillset: {skillset.name}")
        except ResourceExistsError as e:
            # Resource already exists, update it instead
            if verbose:
                print(f"   🔍 Skillset {skillset.name} already exists, updating...")
            try:
                self.client.create_or_update_skillset(skillset)
                if verbose:
                    print(f"   🔄 Updated existing skillset: {skillset.name}")
            except Exception as update_error:
                print(f"   ❌ Failed to update skillset {skillset.name}: {update_error}")
                print(f"   🔍 Update error type: {type(update_error).__name__}")
                raise
        except HttpResponseError as e:
            # Check if it's a resource exists error in HTTP response
            if e.status_code == 409 or "already exists" in str(e).lower():
                if verbose:
                    print(f"   🔍 HTTP 409 or 'already exists' detected for {skillset.name}, updating...")
                try:
                    self.client.create_or_update_skillset(skillset)
                    if verbose:
                        print(f"   🔄 Updated existing skillset: {skillset.name}")
                except Exception as update_error:
                    print(f"   ❌ Failed to update skillset {skillset.name}: {update_error}")
                    print(f"   🔍 Update error type: {type(update_error).__name__}")
                    raise
            else:
                print(f"   ❌ HTTP error creating skillset {skillset.name}: {e}")
                print(f"   🔍 HTTP error details: status={e.status_code}, message={e.message}")
                raise
        except Exception as e:
            print(f"   ❌ Failed to create skillset {skillset.name}: {e}")
            print(f"   🔍 Exception type: {type(e).__name__}")
            print(f"   🔍 Exception details: {str(e)}")
            raise
    
    def _create_or_update_indexer(self, indexer: SearchIndexer, verbose: bool = False) -> None:
        """
        Create or update an indexer.
        
        Args:
            indexer: The indexer to create or update
            verbose: Enable verbose logging
        """
        try:
            if verbose:
                print(f"   🔍 Creating indexer: {indexer.name}")
                print(f"   📋 Indexer details:")
                print(f"      - Data source: {indexer.data_source_name}")
                print(f"      - Target index: {indexer.target_index_name}")
                print(f"      - Skillset: {indexer.skillset_name}")
                print(f"      - Field mappings count: {len(indexer.field_mappings or [])}")
                print(f"      - Output field mappings count: {len(indexer.output_field_mappings or [])}")
                
                # Debug field mappings
                if indexer.field_mappings:
                    print(f"   🗂️ Field mappings:")
                    for i, fm in enumerate(indexer.field_mappings):
                        print(f"      [{i}] {fm.source_field_name} -> {fm.target_field_name}")
                
                # Debug output field mappings  
                if indexer.output_field_mappings:
                    print(f"   📤 Output field mappings:")
                    for i, ofm in enumerate(indexer.output_field_mappings):
                        if isinstance(ofm, dict):
                            # Handle raw dict format
                            source = ofm.get('sourceFieldName', 'NO_SOURCE')
                            target = ofm.get('targetFieldName', 'NO_TARGET')
                            print(f"      [{i}] {source} -> {target}")
                            print(f"      [{i}] Type: dict (raw API format)")
                        else:
                            # Handle SDK object format
                            print(f"      [{i}] {getattr(ofm, 'name', 'NO_NAME')} -> {getattr(ofm, 'target_name', 'NO_TARGET')}")
                            print(f"      [{i}] Type: {type(ofm).__name__}")
                            print(f"      [{i}] All attributes: {[attr for attr in dir(ofm) if not attr.startswith('_')]}")
            
            self.client.create_indexer(indexer)
            if verbose:
                print(f"   ✅ Created indexer: {indexer.name}")
        except ResourceExistsError as e:
            # Resource already exists, update it instead
            if verbose:
                print(f"   🔍 Indexer {indexer.name} already exists, updating...")
            try:
                self.client.create_or_update_indexer(indexer)
                if verbose:
                    print(f"   🔄 Updated existing indexer: {indexer.name}")
            except Exception as update_error:
                print(f"   ❌ Failed to update indexer {indexer.name}: {update_error}")
                print(f"   🔍 Update error type: {type(update_error).__name__}")
                raise
        except HttpResponseError as e:
            # Check if it's a resource exists error in HTTP response
            if e.status_code == 409 or "already exists" in str(e).lower():
                if verbose:
                    print(f"   🔍 HTTP 409 or 'already exists' detected for {indexer.name}, updating...")
                try:
                    self.client.create_or_update_indexer(indexer)
                    if verbose:
                        print(f"   🔄 Updated existing indexer: {indexer.name}")
                except Exception as update_error:
                    print(f"   ❌ Failed to update indexer {indexer.name}: {update_error}")
                    print(f"   🔍 Update error type: {type(update_error).__name__}")
                    raise
            else:
                print(f"   ❌ HTTP error creating indexer {indexer.name}: {e}")
                print(f"   🔍 HTTP error details: status={e.status_code}, message={e.message}")
                raise
        except Exception as e:
            print(f"   ❌ Failed to create indexer {indexer.name}: {e}")
            print(f"   🔍 Exception type: {type(e).__name__}")
            print(f"   🔍 Exception details: {str(e)}")
            raise
    
    def get_indexer_status(self, indexer_name: str) -> Dict[str, Any]:
        """
        Get the status of an indexer.
        
        Args:
            indexer_name: Name of the indexer
            
        Returns:
            Indexer status information
        """
        try:
            status = self.client.get_indexer_status(indexer_name)
            return {
                "name": indexer_name,
                "status": status.status,
                "last_result": {
                    "status": status.last_result.status if status.last_result else None,
                    "start_time": status.last_result.start_time if status.last_result else None,
                    "end_time": status.last_result.end_time if status.last_result else None,
                    "item_count": status.last_result.item_count if status.last_result else 0,
                    "failed_item_count": status.last_result.failed_item_count if status.last_result else 0,
                    "errors": [str(error) for error in (status.last_result.errors or [])] if status.last_result else []
                }
            }
        except Exception as e:
            return {"name": indexer_name, "error": str(e)}
    
    def list_indexer_status(self, verbose: bool = False) -> List[Dict[str, Any]]:
        """
        List status of all indexers.
        
        Args:
            verbose: Enable verbose output
            
        Returns:
            List of indexer status information
        """
        indexers = ["articles-indexer", "authors-indexer"]
        statuses = []
        
        for indexer_name in indexers:
            status = self.get_indexer_status(indexer_name)
            statuses.append(status)
            
            if verbose:
                print(f"\n📊 {indexer_name}:")
                print(f"   Status: {status.get('status', 'Unknown')}")
                if 'last_result' in status and status['last_result']['status']:
                    lr = status['last_result']
                    print(f"   Last Run: {lr['status']} ({lr['start_time']} - {lr['end_time']})")
                    print(f"   Items: {lr['item_count']} processed, {lr['failed_item_count']} failed")
                    if lr['errors']:
                        print(f"   Errors: {lr['errors']}")
        
        return statuses


def setup_azure_indexers(reset: bool = False, verbose: bool = False) -> None:
    """
    Main function to set up Azure AI Search indexers for automatic Cosmos DB sync.
    
    Args:
        reset: Whether to reset existing indexers
        verbose: Enable verbose logging
    """
    manager = AzureIndexerManager()
    manager.setup_indexers(reset=reset, verbose=verbose)


def check_indexer_status(verbose: bool = False) -> List[Dict[str, Any]]:
    """
    Check the status of all indexers.
    
    Args:
        verbose: Enable verbose output
        
    Returns:
        List of indexer status information
    """
    manager = AzureIndexerManager()
    return manager.list_indexer_status(verbose=verbose)
