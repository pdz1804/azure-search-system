# AI-Powered Article Search & Management System

A comprehensive full-stack solution combining **Azure AI Search**, **FastAPI backend**, and **React frontend** to deliver intelligent article management with hybrid search capabilities.

## 🚀 System Overview

This platform provides a complete article management ecosystem with advanced AI-powered search, featuring:

- **Hybrid Search Engine** - BM25 + Vector + Semantic + Business scoring
- **Full-Stack Web Application** - Modern React frontend with FastAPI backend
- **Azure Integration** - Cosmos DB, AI Search, Blob Storage, and OpenAI services
- **Advanced Features** - Fuzzy matching, freshness scoring, role-based access control 

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│  │   User Auth     │ │  Article Mgmt   │ │  AI Search UI   │    │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                │ HTTP/REST API
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│  │  Auth & Users   │ │   Article API   │ │   Search API    │    │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    AI Search Module                             │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│  │  Index Mgmt     │ │  Score Fusion   │ │   Embeddings    │    │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                      Azure Services                             │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐    │
│  │   Cosmos DB     │ │   AI Search     │ │  Blob Storage   │    │
│  │   (Articles)    │ │   (Indexes)     │ │   (Files)       │    │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
ai-search-cloud/
├── ai_search/                   # Core AI search engine module
│   ├── app/
│   │   ├── services/            # Search algorithms & scoring
│   │   └── clients.py           # Azure Search clients
│   ├── config/
│   │   ├── settings.py          # Configuration management
│   │   └── prompts.py           # AI prompts and templates
│   ├── search/
│   │   ├── indexes.py           # Index creation & management
│   │   ├── ingestion.py         # Data ingestion pipeline
│   │   └── indexers.py  	       # Auto-sync with Cosmos DB
│   └── main.py                  # CLI interface & FastAPI server
├── backend/                     # FastAPI web application
│   ├── api/                     # REST API endpoints
│   ├── services/                # Business logic layer
│   ├── repositories/            # Data access layer
│   ├── authentication/          # Auth system
│   ├── database/                # Database connections
│   └── main.py                  # Backend server entry point
├── frontend/                    # React web application
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Application pages
│   │   ├── api/                 # Backend integration
│   │   └── context/             # State management
│   └── package.json             # Dependencies & scripts
├── recommender/                 # ML recommendation system (future)
├── docker-compose.yml           # Multi-service orchestration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## ⚡ Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Docker & Docker Compose** (optional)
- **Azure subscription** with:
  - Cosmos DB account
  - AI Search service
  - Storage account
  - OpenAI/Azure OpenAI service

### 🚀 One-Command Setup (Docker) (NOT DONE)

```bash
# Clone repository
git clone <repository-url>
cd ai-search-cloud

# Configure environment
cp .env.example .env
# Edit .env with your Azure credentials

# Start all services
docker-compose up -d

# Access applications
# Frontend: http://localhost:3000
# Backend API: http://localhost:8001
# AI Search API: http://localhost:8000
```

### 🔧 Manual Setup

#### 1. AI Search Engine Setup

```bash
# Navigate to ai_search directory
cd ai_search

# Install dependencies
pip install -r ../requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with Azure credentials

# Create search indexes with updated schema
python -m ai_search.main create-indexes --reset --verbose

# Set up automatic indexers with preprocessing support
python -m ai_search.main setup-indexers --reset --verbose

# Verify setup
python -m ai_search.main health --verbose

# Start AI search service
python -m ai_search.main serve --port 8000
```

#### 2. Backend API Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies (if not done above)
pip install -r ../requirements.txt

# Configure environment (shares .env with ai_search)
# Ensure .env has backend-specific variables

# Start backend server
python main.py
# Or: uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

#### 3. Frontend Application Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Configure environment
echo "REACT_APP_API_BASE_URL=http://localhost:8001" > .env

# Start development server
npm start
```

## 🔍 Search Capabilities

### Hybrid Search Algorithm

The system combines multiple search techniques for optimal relevance:

#### Articles Search

```
Final Score = 0.3 × BM25 + 0.6 × Vector + 0.1 × Business
```

- **BM25 (30%)**: Keyword matching with TF-IDF scoring
- **Vector (60%)**: Semantic similarity using OpenAI embeddings
- **Business (10%)**: Freshness decay with configurable half-life

#### Authors Search

```
Pure BM25 with Fuzzy Matching (~1 edit distance)
```

- **Fuzzy BM25**: Handles typos and name variations
- **No vector search**: Optimized for exact name matching
- **Search syntax**: `{normalized_query}~1` with `search_mode="any"`

### Business Freshness Scoring

Content freshness uses exponential decay based on the documented formula:

```
score = exp(-ln(2) × age_days / half_life)
```

**Default Configuration:**

- **Half-life**: 250 days (configurable via `FRESHNESS_HALFLIFE_DAYS`)
- **Score Range**: 1.0 (new) → 0.5 (250 days) → 0.0 (very old)
- **Date Hierarchy**: `business_date` → `updated_at` → `created_at`

## 🔐 Authentication & Roles

### User Roles Hierarchy

```
ADMIN    │ Full system access, user management, system settings
WRITER   │ Create/edit own articles, publish content
USER     │ Read articles, search, personal bookmarks
```

### Security Features

- **JWT Authentication** with configurable expiration
- **Password hashing** using bcrypt
- **Role-based access control** at API level
- **Protected routes** in frontend
- **CORS configuration** for cross-origin requests

### 🧠 Text Preprocessing Features

- **Advanced HTML Cleaning** - Removes images, videos, embeds, CSS, and scripts while preserving text content
- **URL & Email Removal** - Cleans up URLs and email addresses from content
- **Intelligent Punctuation Normalization** - Handles excessive punctuation while preserving meaning
- **Preprocessing for Embeddings** - Optimized text preparation for vector embedding generation
- **Automatic Indexer Integration** - Indexers use preprocessed text for better embedding quality
- **Fallback Handling** - ConditionalSkill ensures backward compatibility with existing content
- **Batch Migration Support** - Tools for migrating existing articles to use preprocessed text

**Key Benefits:**
- Better embedding quality from cleaned text
- Improved search relevance and accuracy
- Consistent text formatting across the system
- Enhanced semantic understanding

## 🗄️ Data Management

### Database Schema

#### Articles Collection (Cosmos DB)

```json
{
  "id": "uuid",
  "title": "string",
  "abstract": "string", 
  "content": "rich-text",
  "author_id": "uuid",
  "author_name": "string",
  "tags": ["category", "technology"],
  "status": "published|draft",
  "business_date": "2024-01-15T10:00:00Z",
  "views": 150,
  "likes": 25,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### Search Index Schema

```json
{
  "id": "string",
  "searchable_text": "title + abstract + content",
  "content_vector": [1536-dim embedding],
  "business_score": 0.75,
  "metadata": {
    "status": "published",
    "tags": ["ai", "search"],
    "author_name": "John Doe"
  }
}
```

### Data Synchronization

#### Automatic Sync (Recommended)

```bash
# Set up Azure indexers for real-time sync with preprocessing
cd ai_search
python -m ai_search.main setup-indexers --verbose

# Monitor sync status
python -m ai_search.main check-indexers --verbose
```

**Features:**

- **High-water mark** change detection using Cosmos DB `_ts`
- **Incremental updates** every 5 minutes
- **Deletion tracking** with soft delete support
- **Error recovery** and retry logic

#### Manual Sync (Legacy)

```bash
# One-time data ingestion
cd ai_search
python main.py ingest --verbose --batch-size 50
```

## 🌐 API Reference

### AI Search API (Port 8000)

```
GET /search/articles?q={query}&k={limit}&page_index={idx}&page_size={size}
GET /search/authors?q={query}&page_index={idx}&page_size={size}
GET /health - System health check
```

### Backend API (Port 8001)

```bash
# Authentication
POST /api/auth/login
POST /api/auth/register

# Articles
GET    /api/articles/              # List with pagination
POST   /api/articles/              # Create (WRITER+)
GET    /api/articles/{id}          # Get by ID
PUT    /api/articles/{id}          # Update (Owner/ADMIN)
DELETE /api/articles/{id}          # Delete (Owner/ADMIN)

# Search (integrates with AI Search)
GET /api/search/articles?q={query}
GET /api/search/authors?q={query}

# Users
GET /api/users/me                  # Current user profile
PUT /api/users/me                  # Update profile
```

### Response Format

```json
{
  "articles": [
    {
      "id": "article-uuid",
      "title": "AI-Powered Search Systems",
      "abstract": "Building intelligent search...",
      "score_final": 0.8421,
      "scores": {
        "bm25": 12.45,
        "vector": 0.87,
        "business": 0.61
      },
      "highlights": {
        "@search.highlights": {
          "searchable_text": ["...AI-powered <em>search</em>..."]
        }
      }
    }
  ],
  "pagination": {
    "page_index": 0,
    "page_size": 10,
    "total_results": 156,
    "has_next": true
  }
}
```

## ⚙️ Configuration

### Environment Variables (.env)

```ini
# === Azure AI Search ===
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your-admin-key

# === Cosmos DB ===
COSMOS_ENDPOINT=https://your-cosmos.documents.azure.com:443/
COSMOS_KEY=your-cosmos-key
COSMOS_DB=blogs
COSMOS_ARTICLES=articles
COSMOS_USERS=users

# === OpenAI/Azure OpenAI ===
OPENAI_API_KEY=your-openai-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-azure-openai-key
AZURE_OPENAI_DEPLOYMENT=text-embedding-ada-002

# === Authentication ===
SECRET_KEY=your-jwt-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# === Search Configuration ===
# Article scoring weights
WEIGHT_BM25=0.3
WEIGHT_VECTOR=0.6
WEIGHT_BUSINESS=0.1

# Author scoring (BM25 only with fuzzy matching)
AUTHORS_WEIGHT_BM25=1.0
AUTHORS_WEIGHT_VECTOR=0.0

# Business freshness
FRESHNESS_HALFLIFE_DAYS=250

# === Caching ===
ENABLE_INDEXER_CACHE=true
AZURE_STORAGE_CONNECTION_STRING=your-storage-connection

# === Redis (Backend) ===
REDIS_URL=redis://localhost:6379/0
```

## 🚀 Deployment

### Docker Compose (Recommended)

```bash
# Production deployment
docker-compose -f docker-compose.yml up -d

# Development with hot-reload
docker-compose -f docker-compose.dev.yml up -d
```

### Individual Service Deployment

#### AI Search Service

```bash
# Build image
docker build -f Dockerfile.backend -t ai-search-service .

# Run container
docker run -p 8000:8000 --env-file .env ai-search-service
```

#### Backend API

```bash
# Build and run
docker build -f Dockerfile.backend -t article-backend .
docker run -p 8001:8001 --env-file .env article-backend
```

#### Frontend Application

```bash
# Build and run
docker build -f Dockerfile.frontend -t article-frontend .
docker run -p 3000:3000 article-frontend
```

## 📊 Monitoring & Health

### Health Checks

```bash
# AI Search service health
curl http://localhost:8000/health

# Backend API health
curl http://localhost:8001/api/health

# Check indexer status
cd ai_search
python main.py check-indexers --verbose
```

### Performance Monitoring

- **Search latency**: Track query response times
- **Index stats**: Monitor document counts and update frequency
- **Cache hit rates**: Redis performance metrics
- **Error rates**: API and search error tracking

## 🎯 Usage Examples

### Basic Article Search

```bash
# Search articles
curl "http://localhost:8000/search/articles?q=artificial%20intelligence&k=5"

# Search with pagination
curl "http://localhost:8000/search/articles?q=machine%20learning&page_index=1&page_size=10"
```

### Author Search with Fuzzy Matching

```bash
# Exact name
curl "http://localhost:8000/search/authors?q=John%20Smith"

# Fuzzy matching (handles typos)
curl "http://localhost:8000/search/authors?q=Jon%20Smyth"  # Finds "John Smith"
```

### Article Management via Backend

```bash
# Get articles (requires auth)
curl -H "Authorization: Bearer your-jwt-token" \
     "http://localhost:8001/api/articles/"

# Create article (WRITER role required)
curl -X POST \
     -H "Authorization: Bearer your-jwt-token" \
     -H "Content-Type: application/json" \
     -d '{"title":"New Article","content":"Content...","tags":["tech"]}' \
     "http://localhost:8001/api/articles/"
```

## 🔧 Development

### Running Tests

```bash
# AI Search module tests
cd ai_search
pytest tests/ -v

# Backend API tests  
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

### Code Quality

```bash
# Python linting
cd ai_search
flake8 app/ search/
black app/ search/

# JavaScript/React linting
cd frontend
npm run lint
npm run format
```

## 📈 Performance Optimization

### Search Performance

- **Index optimization**: Proper field configurations and analyzers
- **Caching strategy**: 5-minute TTL for search results
- **Batch operations**: Efficient bulk indexing
- **Connection pooling**: Reuse Azure Search clients

### Application Performance

- **Code splitting**: Route-based React lazy loading
- **Image optimization**: Lazy loading and compression
- **Database indexing**: Cosmos DB partition keys and indexes
- **CDN delivery**: Static asset optimization

## 🔮 Future Enhancements

### Planned Features

- **ML Recommendations** - Content recommendation engine
- **Real-time Collaboration** - Multi-user article editing
- **Advanced Analytics** - User behavior and content insights
- **Multi-language Support** - International content management
- **Progressive Web App** - Offline capability and push notifications

### AI/ML Roadmap

- **Custom embedding models** for domain-specific search
- **Query expansion** using GPT for better recall
- **Semantic clustering** for content organization
- **Auto-tagging** using NLP classification
- **Content quality scoring** using AI assessment

## 🆘 Troubleshooting

### Common Issues

#### Search Index Problems

```bash
# Check index status
cd ai_search
python -m ai_search.main check-indexers --verbose

# Recreate indexes if corrupted (with preprocessing support)
python -m ai_search.main create-indexes --reset --verbose

# Recreate indexers with updated skillset
python -m ai_search.main setup-indexers --reset --verbose
```

#### Authentication Issues

```bash
# Verify JWT configuration
echo $SECRET_KEY
python -c "from backend.utils import create_access_token; print('JWT OK')"
```

#### Database Connection

```bash
# Test Cosmos DB connection
cd ai_search  
python -c "from search.ingestion import test_cosmos; test_cosmos()"
```

### Performance Issues

1. **Slow search**: Check index fragmentation and rebuild if needed
2. **High memory usage**: Adjust batch sizes and connection pools
3. **Auth timeouts**: Increase JWT expiration or implement refresh tokens

## 📚 Documentation

- **AI Search Module**: [`ai_search/README.md`](./ai_search/README.md)
- **Backend API**: [`backend/README.md`](./backend/README.md)
- **Frontend App**: [`frontend/README.md`](./frontend/README.md)
- **API Documentation**:
  - Swagger UI (AI Search): `http://localhost:8000/docs`
  - Swagger UI (Backend): `http://localhost:8001/docs`

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes** and add tests
4. **Run quality checks**: `make lint test`
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Create Pull Request**

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Documentation**: Check component-specific README files
- **Issues**: Create GitHub issues for bug reports
- **Questions**: Use GitHub Discussions for questions
- **Enterprise Support**: Contact the development team

---

**Built with ❤️ using Azure AI Search, FastAPI, and React**
