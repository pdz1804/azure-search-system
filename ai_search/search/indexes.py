"""
Create Azure AI Search indexes:
 - articles-index: text fields + semantic config + vector field + freshness profile
 - authors-index : text fields + semantic config + vector field
"""

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchField, SearchFieldDataType,
    VectorSearch, HnswParameters, HnswAlgorithmConfiguration, VectorSearchProfile,
    SemanticSearch, SemanticConfiguration, SemanticField, SemanticPrioritizedFields,
    ScoringProfile, FreshnessScoringFunction, FreshnessScoringParameters
)
import traceback
from azure.core.exceptions import HttpResponseError
from ai_search.config.settings import SETTINGS
from ai_search.app.services.embeddings import resolve_embedding_dim

def _vector_search() -> VectorSearch:
    # Use the 'algorithms' kwarg (the SDK ignores 'algorithm_configurations') so the config is included
    return VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw-cosine",
                parameters=HnswParameters(metric="cosine", m=16, ef_construction=400, ef_search=100),
            )
        ],
        profiles=[VectorSearchProfile(name="vs-default", algorithm_configuration_name="hnsw-cosine")]
    )

def create_indexes(reset: bool = True, verbose: bool = False) -> None:
    dim = resolve_embedding_dim()
    client = SearchIndexClient(SETTINGS.search_endpoint, AzureKeyCredential(SETTINGS.search_key))

    def describe_field(f):
        # Collect common attributes safely for debugging
        info = {
            "py_type": type(f).__name__,
            "repr": repr(f),
        }
        for attr in ("name", "type", "key", "searchable", "filterable", "facetable", "sortable",
                     "analyzer_name", "vector_search_dimensions", "vector_search_profile_name"):
            try:
                info[attr] = getattr(f, attr)
            except Exception:
                info[attr] = None
        # try to dump __dict__ if available
        try:
            info["__dict__"] = dict(getattr(f, "__dict__", {}))
        except Exception:
            info["__dict__"] = None
        return info

    def dump_index_debug(idx):
        print("\n--- Debug: Index to create ---")
        print(f"index.name: {getattr(idx, 'name', None)}")
        print(f"fields (count): {len(getattr(idx, 'fields', []) or [])}")
        for fi, f in enumerate(getattr(idx, 'fields', []) or []):
            info = describe_field(f)
            print(f" field[{fi}]: name={info.get('name')} type={info.get('py_type')} searchable={info.get('searchable')} vector_dims={info.get('vector_search_dimensions')} vector_profile={info.get('vector_search_profile_name')}")
        vs = getattr(idx, 'vector_search', None)
        print(f"vector_search: {vs}")
        try:
            # try to introspect common attrs on VectorSearch
            if vs is not None:
                for a in ("profiles", "algorithm_configurations", "profiles_list", "algorithms"):
                    try:
                        val = getattr(vs, a)
                        print(f" vector_search.{a}: {val}")
                    except Exception:
                        pass
        except Exception:
            print("could not introspect vector_search")
        print(f"semantic_search: {getattr(idx, 'semantic_search', None)}")
        print("--- end debug ---\n")

    # -------- ARTICLES --------
    # Optimized schema based on actual data structure and search requirements
    article_fields = [
        # Primary key
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        
        # Core searchable content fields
        SearchableField(name="title", type=SearchFieldDataType.String, analyzer_name="en.lucene", sortable=True),
        SearchableField(name="abstract", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
        SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
        SearchableField(name="author_name", type=SearchFieldDataType.String, analyzer_name="en.lucene", sortable=True, filterable=True),
        
        # Filtering and faceting fields
        SimpleField(name="status", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="tags", type=SearchFieldDataType.Collection(SearchFieldDataType.String), filterable=True, facetable=True),
        
        # Temporal fields for sorting and freshness scoring
        SimpleField(name="created_at", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
        SimpleField(name="updated_at", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
        SimpleField(name="business_date", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
        
        # Application filtering
        SimpleField(name="app_id", type=SearchFieldDataType.String, filterable=True),
        
        # Consolidated searchable text for highlighting
        SearchableField(name="searchable_text", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
        
        # COMMENTED OUT: Preprocessed searchable text field (removed from articles)
        # SearchableField(name="preprocessed_searchable_text", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
        
        # Vector field for hybrid search
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=dim,
            vector_search_profile_name="vs-default",
        ),
    ]

    articles_semantic = SemanticConfiguration(
        name="articles-semantic",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            content_fields=[
                # SemanticField(field_name="preprocessed_searchable_text"),  # Removed: field no longer exists
                SemanticField(field_name="abstract"), 
                SemanticField(field_name="content")
            ],
            keywords_fields=[SemanticField(field_name="tags")],
        ),
    )

    scoring_profiles = [
        ScoringProfile(
            name="freshness_profile",
            functions=[FreshnessScoringFunction(
                field_name="business_date",
                boost=2.0,
                parameters=FreshnessScoringParameters(boosting_duration=f"P{SETTINGS.freshness_window_days}D")
            )]
        )
    ]

    articles_index = SearchIndex(
        name="articles-index",
        fields=article_fields,
        vector_search=_vector_search(),
        semantic_search=SemanticSearch(
            configurations=[articles_semantic],
            default_configuration_name="articles-semantic"
        ),
        scoring_profiles=scoring_profiles,
    )

    # -------- AUTHORS --------
    # Optimized schema for author/user search based on actual data structure
    author_fields = [
        # Primary key
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        
        # Core searchable fields
        SearchableField(name="full_name", type=SearchFieldDataType.String, analyzer_name="en.lucene", sortable=True),
        
        # Filtering fields
        SimpleField(name="role", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="created_at", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True),
        
        # Application filtering
        SimpleField(name="app_id", type=SearchFieldDataType.String, filterable=True),
        
        # Consolidated searchable text
        SearchableField(name="searchable_text", type=SearchFieldDataType.String, analyzer_name="en.lucene"),
        
        # Vector field for semantic search - COMMENTED OUT for keyword-only search
        # SearchField(
        #     name="name_vector",
        #     type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        #     searchable=True,
        #     vector_search_dimensions=dim,
        #     vector_search_profile_name="vs-default",
        # ),
    ]

    authors_semantic = SemanticConfiguration(
        name="authors-semantic",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="full_name"),
            content_fields=[SemanticField(field_name="searchable_text")],
        ),
    )

    authors_index = SearchIndex(
        name="authors-index",
        fields=author_fields,
        vector_search=_vector_search(),
        semantic_search=SemanticSearch(
            configurations=[authors_semantic],
            default_configuration_name="authors-semantic"
        ),
    )

    # Also create the child chunk index used by the indexer projection (articles-chunks-index)
    # This index stores per-chunk text + vector and a parent_id that links back to the article.
    chunk_fields = [
        SearchField(name="chunk_id", type=SearchFieldDataType.String, key=True, filterable=True, analyzer_name="keyword"),
        SearchField(name="parent_id", type=SearchFieldDataType.String, filterable=True),
        SearchField(name="title", type=SearchFieldDataType.String, searchable=True, filterable=True, sortable=True),
        SearchField(name="chunk", type=SearchFieldDataType.String, searchable=True),
        # Keep ordinal as string to avoid projection type-mismatch unless your enrichment guarantees ints
        SearchField(name="chunk_ordinal", type=SearchFieldDataType.String, filterable=True, sortable=True),
        
        # Application filtering
        SearchField(name="app_id", type=SearchFieldDataType.String, filterable=True),
        
        SearchField(
            name="chunk_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=dim,
            vector_search_profile_name="vs-default",
        ),
    ]

    chunk_index = SearchIndex(
        name="articles-chunks-index", 
        fields=chunk_fields, 
        vector_search=_vector_search()
    )

    # Create or update all indexes we need
    for idx in (articles_index, authors_index, chunk_index):
        if reset:
            try:
                client.delete_index(idx.name)
            except Exception:
                pass
        # dump debug info before attempting to create (if verbose)
        if verbose:
            dump_index_debug(idx)
        try:
            client.create_index(idx)
            print(f"Successfully created index: {idx.name}")
        except HttpResponseError as hre:
            # Check if it's a resource already exists error
            if hre.status_code == 409 or "already exists" in str(hre).lower():
                if verbose:
                    print(f"Index {idx.name} already exists, updating...")
                try:
                    client.create_or_update_index(idx)
                    print(f"Successfully updated index: {idx.name}")
                except Exception as update_error:
                    print(f"Failed to update index {idx.name}: {update_error}")
                    if verbose:
                        traceback.print_exc()
                    raise
            else:
                print(f"HttpResponseError creating index {idx.name}: {type(hre).__name__}: {hre}")
                if verbose:
                    try:
                        # Some HttpResponseError objects include .response or .error
                        if hasattr(hre, 'response') and hre.response is not None:
                            try:
                                body = hre.response.text()
                                print(f"Response body: {body}")
                            except Exception:
                                print("Unable to read hre.response.text()")
                        if hasattr(hre, 'error') and hre.error is not None:
                            print(f"Error model: {hre.error}")
                    except Exception:
                        pass
                    traceback.print_exc()
                raise
        except Exception as e:
            print(f"Unexpected error creating index {idx.name}: {type(e).__name__}: {e}")
            traceback.print_exc()
            raise

    print(f"Created indexes with vector dim={dim}: articles-index, authors-index, articles-chunks-index")
