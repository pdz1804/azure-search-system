# Blog Hybrid Search (Azure AI Search + Cosmos DB + OpenAI/HF Embeddings)

This project wires your existing **Cosmos DB (blogs)** into **Azure AI Search** and exposes a **FastAPI** layer that performs **hybrid search** over articles and authors with an **explicit, weighted score fusion**.

## Architecture

```
Cosmos DB (blogs)
 ├─ articles
 └─ users
        │
        ▼
Ingestion (with chosen embeddings)
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
 ├─ python main.py serve
 ├─ GET /search/articles?q=...   # 0.5 sem + 0.3 bm25 + 0.1 vec + 0.1 business
 └─ GET /search/authors?q=...    # 0.6 sem + 0.4 bm25 (configurable)
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
- **Semantic re-ranking** (Azure AI Search semantic ranker).
- **BM25** sparse keyword scoring over `searchable_text` (title + abstract + content).
- **Vector search** on stored embeddings (configurable provider: OpenAI or Hugging Face).
- **Business/Freshness** signal computed from `updated_at || created_at` with exponential decay.
- **Client-side score fusion** with configurable weights.
- Clean, modular code and configuration-driven behavior.

---

## 2) Project Structure

```
blog-search/
├─ .env.example
├─ README.md
├─ requirements.txt
├─ main.py              # CLI entry point + FastAPI app
├─ config/
│  └─ settings.py
├─ search/
│  ├─ indexes.py        # Index creation logic
│  └─ ingestion.py      # Data ingestion from Cosmos DB
├─ app/
│  ├─ clients.py        # Azure Search client factories
│  ├─ models.py         # Pydantic response models
│  └─ services/
│     ├─ embeddings.py  # Embedding provider abstraction
│     ├─ scoring.py     # Score fusion algorithms
│     └─ search_service.py  # High-level search orchestration
└─ utils/
   ├─ timeparse.py      # Date parsing utilities
   └─ cli.py           # Command-line argument parser
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

### Ingest Data
```bash
# Ingest data from Cosmos DB to search indexes
python main.py ingest

# Ingest with verbose output and custom batch size
python main.py ingest --verbose --batch-size 50
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

## 6) Create Indexes

```bash
# Using the CLI (recommended)
python main.py create-indexes

# Or using direct Python (legacy)
python -c "from search.indexes import create_indexes; create_indexes()"
```

This will:
1. Resolve the **vector dimension** based on your embedding provider/model (or `EMBEDDING_DIM` override).
2. Create **`articles-index`** with fields:
   - Text: `title`, `abstract`, `content`, `searchable_text` (title+abstract+content)
   - Metadata: `author_name`, `author_id`, `status`, `tags`, counts, `created_at`, `updated_at`, `business_date`, `image`
   - **Vector**: `content_vector` (HNSW, cosine)
   - **Semantic config**: `articles-semantic` (title/content/keywords fields)
   - **Freshness profile**: boosts `business_date` over window `P{FRESHNESS_WINDOW_DAYS}D`
3. Create **`authors-index`** with fields:
   - Text: `full_name`, `searchable_text`
   - Metadata: `email`, `role`, `created_at`
   - **Vector**: `name_vector` (optional; for semantic name similarity)
   - **Semantic config**: `authors-semantic` (title=full_name)

> **Behind the scenes (Index creation)**  
> - Azure AI Search allocates a new index with:  
>   a) An **inverted index** for text fields (BM25),  
>   b) An **HNSW graph** for vector fields (approximate nearest neighbors on cosine distance),  
>   c) A **semantic configuration** that tells the semantic ranker which fields are title/content/keywords,  
>   d) A **scoring profile** with a **Freshness** function referencing `business_date`.  
> - The vector dimension must match your embedding model. We compute/resolve it before creating the field.  
> - Analyzers (e.g., `en.lucene`) are attached to searchable fields to tokenize/stem text for BM25.  
> - The service persists this metadata; no data is indexed yet—only the **schema** and **configs**.

---

## 6) Ingest Data from Cosmos

```bash
python -c "from search.ingestion import ingest; ingest()"
```

This will:
1. **Read** items from Cosmos DB containers:
   - `articles` (your long text records)
   - `users` (authors)
2. For each article:
   - Build `searchable_text = title + "\n" + abstract + "\n" + content`  
   - Compute `business_date = updated_at if present else created_at`  
   - **If `ENABLE_EMBEDDINGS=true`**, generate an embedding using the configured provider and store as `content_vector`  
   - Convert `created_at/updated_at` strings into `DateTimeOffset`
   - Upload the document to `articles-index` via `SearchClient.upload_documents()`
3. For each user:
   - Use `full_name` as `searchable_text`
   - **If `ENABLE_EMBEDDINGS=true`**, compute `name_vector`
   - Upload the document to `authors-index`

> **Behind the scenes (Ingestion)**  
> - For **OpenAI**, we call `embeddings.create(model, input=text)` and store the returned float vector.  
> - For **HF**, we instantiate `SentenceTransformer(HF_MODEL_NAME)` and call `.encode(text, normalize_embeddings=True)`; cosine similarity works out-of-the-box.  
> - Azure AI Search builds/updates its **inverted index** postings and **HNSW graph** as documents arrive.  
> - `business_date` is just a normal datetime field; we also configured a Freshness profile that can influence internal scoring.  
> - No semantic magic happens yet; semantic reranking only happens during query time.

---

## 7) Run API

```bash
uvicorn app.main:app --reload --port 8000

# Try:
# http://localhost:8000/search/articles?q=transformers
# http://localhost:8000/search/authors?q=david
```

### Endpoints

- `GET /search/articles?q=...&k=10`  
  Returns a list of hits with fields: `id`, `title`, `abstract`, `author_name`, `score_final`, and component `scores` + highlights.

- `GET /search/authors?q=...&k=10`  
  Returns a list of author hits with `id`, `full_name`, `score_final`, and component `scores`.

---

## 8) What Happens During Queries (End-to-End)

### 8.1 Articles flow

1. **Receive query** `q` and `k`.
2. **Compute query embedding** (using configured provider) for **vector** search.
3. **Text+Semantic call** to Azure AI Search:
   - `query_type="semantic"` with `semantic_configuration_name="articles-semantic"`
   - Azure does **BM25 retrieval** over `searchable_text` ⇒ candidate set
   - Azure applies **semantic ranker** to those candidates ⇒ adds `@search.rerankerScore`
   - We collect:
     - BM25 score: `@search.score` (higher → better keyword match)
     - Semantic score: `@search.rerankerScore` (captures meaning, synonyms, intent; often ~0..4)
     - `business_date` for our freshness
4. **Vector KNN call** to Azure:
   - `VectorizedQuery(vector=qvec, k=k, fields="content_vector")`
   - Azure searches the **HNSW** index and returns `@search.score` = cosine similarity.
5. **Merge** text+semantic results and vector results by document ID (fetch missing docs for vector-only hits).  
6. **Compute business score** (freshness) per doc:
   - `business = exp(-ln(2) * age_days / FRESHNESS_HALFLIFE_DAYS)`
7. **Normalize** BM25, Semantic, Vector to `[0,1]` within the result set (min-max robustly).  
8. **Fuse** with weights from `.env`:
   - `final = 0.5*semantic + 0.3*bm25 + 0.1*vector + 0.1*business`
9. **Sort** by final score and **return** results (with optional `@search.highlights`).

### 8.2 Authors flow

1. **Text+Semantic call** (authors-semantic): get BM25 + semantic scores.  
2. (Optional) **Vector** over `name_vector` if you enable a vector weight.  
3. **Fuse** with `AUTHORS_*` weights (defaults: 0.6 semantic, 0.4 BM25).  
4. Return results.

> **Behind the scenes (Query)**  
> - BM25 uses the inverted index; cost is proportional to term postings.  
> - Semantic ranker runs on the candidate set (not the whole corpus), adding an **intent-aware** reranking signal.  
> - Vector search uses the **HNSW graph** in memory for fast approximate nearest neighbors.  
> - Our client-side fusion ensures your **exact** weighting (Azure’s built-in “hybrid” uses RRF instead).

---

## 9) Tuning & Tips

- **Freshness window**: `FRESHNESS_WINDOW_DAYS` in the scoring profile influences internal boosting; our explicit business score has its own **half-life** for precise 0.1 weight. Align both if needed.
- **Embedding provider**:  
  - **OpenAI** (`text-embedding-3-small`): strong general-purpose vectors, 1536 dims.  
  - **HF MiniLM-L6-v2**: fast, local, 384 dims, great for names and shorter texts.  
- **Long content**: If `content` is very long, consider **chunked multi-vector** indexing and aggregate top chunk scores per article.
- **Tracing**: Inspect `@search.rerankerScore`, `@search.score` (BM25), and vector scores per hit to debug relevance.
- **Costs**: Only enable vectors where needed (articles). Vector fields increase memory for the HNSW graph.

---

## 10) Troubleshooting

- **Dimension mismatch** when creating the index: set `EMBEDDING_DIM` to the correct size or ensure your provider/model is correct.
- **No semantic scores**: ensure `query_type="semantic"` and a valid `semantic_configuration_name` with proper prioritized fields.
- **Low vector quality**: verify embeddings are computed with the same provider/model at both **index** and **query** time.
- **Date parsing issues**: input dates must match `'YYYY-MM-DD HH:MM:SS'` for ingestion; adjust parser if your format differs.
- **Choppy performance**: reduce `k`, increase hardware, or prune fields; for vectors, tune HNSW parameters (`ef_search`, `m`).

---

## 11) API Examples

```bash
curl "http://localhost:8000/search/articles?q=transformers&k=5"
curl "http://localhost:8000/search/authors?q=david&k=5"
```

Example (articles) response shape:

```json
[
  {
    "id": "13006997-e576-40f2-8633-5f73b35c7c90",
    "title": "Transformers Revolutionizing Natural Language Processing",
    "abstract": "Transformers have transformed the field...",
    "author_name": "David Jackson",
    "score_final": 0.8421,
    "scores": {
      "semantic": 3.82,
      "bm25": 12.45,
      "vector": 0.87,
      "business": 0.61
    },
    "highlights": {
      "@search.highlights": { "searchable_text": ["..."] }
    }
  }
]
```

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
