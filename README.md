# Blog Hybrid Search (Azure AI Search + Cosmos DB + OpenAI/HF Embeddings)

This project wires your existing **Cosmos DB (blogs)** into **Azure AI Search** and exposes a **FastAPI** layer that performs **hybrid search** over articles and authors with an **explicit, weighted score fusion**.

## Architecture

```
Cosmos DB (blogs)
 ├─ articles
 └─ users
        │
        ▼
Azure AI Search (Native Indexers + Manual Ingestion)
        │
        ▼
Azure AI Search
 ├─ articles-index  (BM25 + Semantic + Vector + Freshness)
 └─ authors-index   (BM25 + Semantic + Vector)
        │
        ▼
FastAPI + CLI
 ├─ python main.py create-indexes
 ├─ python main.py ingest
 ├─ python main.py setup-indexers    # Azure-native indexers
 ├─ python main.py check-indexers    # Monitor indexer status
 ├─ python main.py serve
 ├─ GET /search/articles?q=...&page_index=...&page_size=...
 └─ GET /search/authors?q=...&page_index=...&page_size=...
```

## Scoring Strategy

This project wires your existing **Cosmos DB (blogs)** into **Azure AI Search** and exposes a **FastAPI** layer that performs **hybrid search** over articles and authors with an **explicit, weighted score fusion**:

- **Articles**: `final = 0.5 * semantic + 0.3 * BM25 + 0.1 * vector + 0.1 * business`
- **Authors** (default): `final = 0.6 * semantic + 0.4 * BM25` (configurable)

Semantic ≠ Vector in Azure AI Search:

- **Semantic search** = Azure **semantic ranker** that re-ranks text results, returning `@search.rerankerScore`. You don’t store vectors for this.
- **Vector search** = KNN over your **embedding field** (HNSW), returning a similarity `@search.score` for the vector query.

---

## 1) Features

- Two **separate indexes**: `articles-index` and `authors-index` (schema-fit, better relevance, isolation).
- **Azure-native indexers** for automatic Cosmos DB synchronization with high-water mark change detection.
- **Semantic re-ranking** (Azure AI Search semantic ranker) with automatic fallback to BM25.
- **BM25** sparse keyword scoring over `searchable_text` (title + abstract + content).
- **Vector search** on stored embeddings (configurable provider: OpenAI or Hugging Face).
- **Business/Freshness** signal computed from `updated_at || created_at` with exponential decay.
- **Client-side score fusion** with configurable weights.
- **Pagination support** with page_index and page_size parameters.
- **Automatic error recovery** and semantic search capability detection.
- Clean, modular code and configuration-driven behavior.

---

## 2) Project Structure

```
ai-search-cloud/
├─ .env.example
├─ README.md
├─ requirements.txt
├─ main.py              # CLI entry point + FastAPI app
├─ config/
│  └─ settings.py       # Environment configuration
├─ search/
│  ├─ indexes.py        # Index creation logic
│  ├─ ingestion.py      # Manual data ingestion from Cosmos DB
│  └─ azure_indexers.py # Azure-native indexers for automatic sync
├─ app/
│  ├─ clients.py        # Azure Search client factories
│  ├─ models.py         # Pydantic response models
│  └─ services/
│     ├─ embeddings.py  # Embedding provider abstraction
│     ├─ scoring.py     # Score fusion algorithms
│     └─ search_service.py  # High-level search orchestration
├─ utils/
│  ├─ timeparse.py      # Date parsing utilities
│  └─ cli.py           # Command-line argument parser
├─ scripts/
│  └─ blog_data_generator.py  # Generate sample blog data
└─ data/
   ├─ articles.json     # Sample articles data
   ├─ users.json        # Sample users data
   └─ blog_seed_UPDATED.json  # Generated blog data
```

---

## 3) Installation

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env with your keys and choices (see below)
```

**requirements.txt** includes:

- `azure-search-documents`, `azure-cosmos` (Azure SDKs)
- `fastapi`, `uvicorn` (API)
- `openai` (OpenAI embeddings, optional)
- `sentence-transformers`, `torch`, `numpy` (HF embeddings, optional)

---

## 4) CLI Commands

The `main.py` file provides a command-line interface with several subcommands:

### Create Search Indexes

```bash
# Create indexes with default settings (reset existing indexes)
python main.py create-indexes

# Create indexes with verbose debugging output
python main.py create-indexes --verbose

# Create indexes without resetting existing ones
python main.py create-indexes --no-reset
```

### Manual Data Ingestion

```bash
# Ingest data from Cosmos DB to search indexes
python main.py ingest

# Ingest with verbose output and custom batch size
python main.py ingest --verbose --batch-size 50
```

### Azure-Native Indexers (Automatic Sync)

```bash
# Set up Azure indexers for automatic Cosmos DB synchronization
python main.py setup-indexers

# Set up indexers with reset (delete existing first)
python main.py setup-indexers --reset

# Set up indexers with verbose output
python main.py setup-indexers --verbose

# Check status of all indexers
python main.py check-indexers

# Check indexer status with detailed information
python main.py check-indexers --verbose
```

### Start API Server

```bash
# Start server with default settings (127.0.0.1:8000)
python main.py serve

# Start server with custom host/port
python main.py serve --host 0.0.0.0 --port 8080

# Start server in development mode with auto-reload
python main.py serve --reload

# Start server with multiple workers
python main.py serve --workers 4
```

### Get Help

```bash
# Show all available commands
python main.py --help

# Show help for specific command
python main.py create-indexes --help
python main.py ingest --help
python main.py setup-indexers --help
python main.py check-indexers --help
python main.py serve --help
```

---

## 5) Configuration (.env)

```ini
# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://<your-search>.search.windows.net
AZURE_SEARCH_KEY=<admin-key>

# Cosmos DB
COSMOS_ENDPOINT=https://<your-cosmos>.documents.azure.com:443/
COSMOS_KEY=<cosmos-key>
COSMOS_DB=blogs
COSMOS_ARTICLES=articles
COSMOS_USERS=users

# Embeddings backend: "openai" or "hf"
EMBEDDING_PROVIDER=openai
# OpenAI
OPENAI_API_KEY=<key>
OPENAI_BASE_URL=                  # optional (Azure OpenAI)
OPENAI_API_VERSION=2024-06-01
EMBEDDING_MODEL=text-embedding-3-small
# Hugging Face (SentenceTransformers)
HF_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# Optional override for vector dimension (else auto-resolve)
EMBEDDING_DIM=

# Weights (articles)
WEIGHT_SEMANTIC=0.5
WEIGHT_BM25=0.3
WEIGHT_VECTOR=0.1
WEIGHT_BUSINESS=0.1

# Weights (authors) - default semantic+bm25 only
AUTHORS_WEIGHT_SEMANTIC=0.6
AUTHORS_WEIGHT_BM25=0.4
AUTHORS_WEIGHT_VECTOR=0.0
AUTHORS_WEIGHT_BUSINESS=0.0

# Freshness (business) controls
FRESHNESS_HALFLIFE_DAYS=250
FRESHNESS_WINDOW_DAYS=365

# Toggle embedding compute/store during ingestion
ENABLE_EMBEDDINGS=true
```

**Embedding provider choice**:

- `EMBEDDING_PROVIDER=openai` → use OpenAI (`EMBEDDING_MODEL` defaults to `text-embedding-3-small`, dim=1536).
- `EMBEDDING_PROVIDER=hf` → use Hugging Face (`HF_MODEL_NAME` defaults to `all-MiniLM-L6-v2`, dim=384).
- You can force a specific dimension via `EMBEDDING_DIM` if needed.

---

## 6) Index Structure

### Articles Index (`articles-index`)

**Core Fields:**
- `id` (String, key): Primary identifier
- `title` (Searchable String): Article title with `en.lucene` analyzer
- `abstract` (Searchable String): Article summary
- `content` (Searchable String): Full article content
- `author_name` (Searchable String): Author's name
- `searchable_text` (Searchable String): Consolidated text for highlighting
- `content_vector` (Vector): Embedding for semantic similarity

**Metadata Fields:**
- `status` (String): Publication status (filterable, facetable)
- `tags` (Collection[String]): Article tags (filterable, facetable)
- `created_at`, `updated_at`, `business_date` (DateTimeOffset): Temporal fields

**Search Configurations:**
- **Semantic**: `articles-semantic` (title=title, content=abstract+content, keywords=tags)
- **Vector**: HNSW algorithm with cosine similarity
- **Scoring Profile**: Freshness boost based on `business_date`

### Authors Index (`authors-index`)

**Core Fields:**
- `id` (String, key): Primary identifier
- `full_name` (Searchable String): Author's full name
- `searchable_text` (Searchable String): Consolidated searchable text
- `name_vector` (Vector): Name embedding for semantic similarity

**Metadata Fields:**
- `role` (String): User role (filterable, facetable)
- `created_at` (DateTimeOffset): Account creation date

**Search Configurations:**
- **Semantic**: `authors-semantic` (title=full_name, content=searchable_text)
- **Vector**: HNSW algorithm with cosine similarity

---

## 7) Data Synchronization

### Option 1: Manual Ingestion

```bash
# Using CLI (recommended)
python main.py ingest --verbose --batch-size 50

# Using direct Python (legacy)
python -c "from search.ingestion import ingest; ingest()"
```

**Process:**
1. Read items from Cosmos DB containers (`articles` and `users`)
2. For each article: build `searchable_text`, compute `business_date`, generate embeddings
3. For each user: create `searchable_text` from `full_name`, generate name embeddings
4. Upload documents to respective search indexes

### Option 2: Azure-Native Indexers (Automatic)

```bash
# Set up automatic synchronization
python main.py setup-indexers --verbose

# Monitor indexer status
python main.py check-indexers --verbose
```

**Features:**
- **High-water mark change detection** using Cosmos DB `_ts` field
- **Automatic scheduling** (runs every 5 minutes)
- **Skillsets** for computed fields (searchable_text, business_date, embeddings)
- **Error handling** and retry logic
- **Zero-downtime sync** with incremental updates

---

## 8) API Endpoints

### Starting the Server

```bash
# Using CLI (recommended)
python main.py serve --reload --port 8000

# Using uvicorn directly
uvicorn main:app --reload --port 8000
```

### Article Search

```
GET /search/articles?q={query}&k={limit}&page_index={index}&page_size={size}
```

**Parameters:**
- `q` (required): Search query text
- `k` (optional, default=10): Number of results to return
- `page_index` (optional): Zero-based page index for pagination
- `page_size` (optional): Number of results per page

**Response Format:**
```json
{
  "articles": [
    {
      "id": "article-uuid",
      "title": "Article Title",
      "abstract": "Article summary...",
      "author_name": "Author Name",
      "score_final": 0.8421,
      "scores": {
        "semantic": 3.82,
        "bm25": 12.45,
        "vector": 0.87,
        "business": 0.61
      },
      "highlights": {
        "@search.highlights": {
          "searchable_text": ["...highlighted text..."]
        }
      }
    }
  ],
  "pagination": {
    "page_index": 0,
    "page_size": 10,
    "total_results": 156,
    "total_pages": 16,
    "has_next": true,
    "has_previous": false
  }
}
```

### Author Search

```
GET /search/authors?q={query}&k={limit}&page_index={index}&page_size={size}
```

**Parameters:** Same as article search

**Response Format:**
```json
{
  "authors": [
    {
      "id": "user-uuid",
      "full_name": "Dr. Sarah Johnson",
      "score_final": 0.9231,
      "scores": {
        "semantic": 3.45,
        "bm25": 8.76,
        "vector": 0.0,
        "business": 0.0
      }
    }
  ],
  "pagination": {
    "page_index": 0,
    "page_size": 10,
    "total_results": 23,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false
  }
}
```

### Interactive Documentation

Access Swagger UI at: `http://localhost:8000/docs`

---

## 9) Search Process (End-to-End)

### Articles Search Flow

1. **Query Processing**: Receive query text, pagination parameters
2. **Semantic Search Capability Check**: Automatically detect if semantic search is available
3. **Text Search**: Execute BM25 + semantic search (with automatic fallback to BM25-only)
4. **Vector Search**: Generate query embedding and perform KNN search
5. **Result Merging**: Combine text and vector results by document ID
6. **Score Computation**: Calculate business/freshness scores
7. **Score Fusion**: Apply configurable weights to combine all score components
8. **Pagination**: Apply page_index and page_size if specified
9. **Response**: Return structured results with pagination metadata

### Authors Search Flow

1. **Query Processing**: Similar to articles but optimized for name search
2. **Text Search**: BM25 + semantic search on author names
3. **Optional Vector Search**: Only if `AUTHORS_WEIGHT_VECTOR > 0`
4. **Score Fusion**: Combine semantic and BM25 scores (vector/business optional)
5. **Pagination**: Apply pagination if requested
6. **Response**: Return author results with pagination metadata

### Automatic Error Recovery

- **Semantic Search Fallback**: Automatically falls back to BM25 if semantic search fails
- **Runtime Detection**: Tests semantic capability on startup and during queries
- **Graceful Degradation**: Continues operation even if some components fail

---

## 12) Why two indexes (articles & authors)?

- Different schemas/analyzers, different semantic configs, different scoring needs (freshness for articles, not for users).
- Better performance and relevance; smaller per-index HNSW graphs.
- Operational isolation (rebuild articles without touching users).
- Code is cleaner: each API targets just one index.

---

## 13) Next steps (optional)

- **Chunked multi-vector** for long documents.
- **Integrated vectorization** with Azure indexers and skills.
- **RRF**-based hybrid as an alternative to client-side weighted fusion.
- **Telemetry dashboards** for score components and latency.
- **Synonyms / custom analyzers** for domain terms.
