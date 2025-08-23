# Backend API - Article Management System

FastAPI-based backend service providing article management, user authentication, and AI-powered search capabilities.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Azure Cosmos DB account
- Azure AI Search service
- Redis instance
- Azure Storage account (for file uploads)

### Installation

1. **Navigate to backend directory:**

   ```bash
   cd backend
   ```
2. **Create virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies:**

   ```bash
   pip install -r ../requirements.txt
   ```
4. **Environment configuration:**

   ```bash
   cp ../.env.example .env
   # Edit .env with your Azure credentials
   ```
5. **Start the server:**

   ```bash
   python main.py
   # Or: uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```

## 🏗️ Architecture

The backend follows a layered architecture pattern:

```
┌─────────────────┐
│   API Layer     │  FastAPI routers (articles, auth, users, search, files, cache)
├─────────────────┤
│  Service Layer  │  Business logic and orchestration
├─────────────────┤
│Repository Layer │  Data access abstraction  
├─────────────────┤
│  Database Layer │  Cosmos DB containers
└─────────────────┘
```

### Request Flow

```
HTTP Request → FastAPI Router → Service Layer → Repository Layer → Cosmos DB
                     ↓
              Authentication Middleware
                     ↓
              Role-based Access Control
```

## 📁 Project Structure

```
backend/
├── main.py                    # FastAPI app entry point
├── utils.py                   # Authentication & utility helpers
├── api/                       # API route handlers
│   ├── article.py             # Article CRUD operations
│   ├── search.py              # AI search endpoints  
│   ├── user.py                # User management
│   ├── file.py                # File upload handling
│   └── cache.py               # Cache management
├── authentication/            # Auth system
│   └── routes.py              # Login/register endpoints
├── services/                  # Business logic layer
│   ├── article_service.py     # Article operations
│   ├── user_service.py        # User operations
│   ├── search_service.py      # AI search integration
│   ├── cache_service.py       # Redis caching
│   └── azure_blob_service.py  # File storage
├── repositories/              # Data access layer
│   ├── article_repo.py        # Article database operations
│   └── user_repo.py           # User database operations
├── database/                  # Database configuration
│   └── cosmos.py              # Cosmos DB client setup
├── config/                    # Configuration modules
│   ├── settings.py            # Environment variables
│   ├── redis_config.py        # Redis connection
│   └── azure_blob.py          # Azure Storage config
├── model/                     # Data models
│   ├── article.py             # Article schema
│   └── user.py                # User schema
└── enum/                      # Enumerations
    └── roles.py               # User role definitions
```

## 🔧 Core Components

### Authentication System

- **JWT-based authentication** with Bearer tokens
- **Role-based access control** (USER, WRITER, ADMIN)
- **Password hashing** using bcrypt
- **Token expiration** and automatic refresh

### Article Management

- **CRUD operations** for articles
- **Rich text content** support
- **Image upload** to Azure Blob Storage
- **Author attribution** and ownership
- **Status management** (draft, published)
- **Tag system** for categorization

### AI-Powered Search

- **Hybrid search** combining multiple algorithms
- **Azure AI Search** integration
- **Vector embeddings** for semantic similarity
- **BM25** for keyword matching
- **Business freshness** scoring
- **Fuzzy matching** for author names

### Caching Layer

- **Redis-based caching** for performance
- **Search result caching** with TTL
- **User session management**
- **Rate limiting** support

## 🔐 Authentication & Authorization

### User Roles

```python
class Role(str, Enum):
    USER = "USER"        # Read-only access
    WRITER = "WRITER"    # Can create/edit own articles
    ADMIN = "ADMIN"      # Full system access
```

### Protected Endpoints

- **Article Creation**: WRITER, ADMIN roles required
- **Article Editing**: Owner or ADMIN role required
- **User Management**: ADMIN role required
- **System Settings**: ADMIN role required

### JWT Token Structure

```json
{
  "sub": "user_id",
  "exp": 1640995200,
  "iat": 1640908800
}
```

## 🌐 API Endpoints

### Authentication

```
POST /api/auth/register   # User registration
POST /api/auth/login      # User login
POST /api/auth/logout     # User logout
```

### Articles

```
GET    /api/articles/              # List articles with pagination
POST   /api/articles/              # Create new article (WRITER+)
GET    /api/articles/{id}          # Get article by ID
PUT    /api/articles/{id}          # Update article (Owner/ADMIN)
DELETE /api/articles/{id}          # Delete article (Owner/ADMIN)
GET    /api/articles/author/{id}   # Get articles by author
GET    /api/articles/popular       # Get popular articles
POST   /api/articles/{id}/view     # Increment view count
```

### Search

```
GET /api/search/articles?q={query}&page_index={idx}&page_size={size}
GET /api/search/authors?q={query}&page_index={idx}&page_size={size}
```

### Users

```
GET    /api/users/          # List users (ADMIN)
GET    /api/users/me        # Get current user profile
PUT    /api/users/me        # Update own profile
GET    /api/users/{id}      # Get user by ID
PUT    /api/users/{id}      # Update user (ADMIN)
DELETE /api/users/{id}      # Delete user (ADMIN)
```

### Files

```
POST /api/files/upload      # Upload file to Azure Blob
```

### Cache

```
DELETE /api/cache/clear     # Clear Redis cache (ADMIN)
```

## 🗄️ Database Schema

### Articles Collection

```json
{
  "id": "uuid",
  "title": "string",
  "abstract": "string", 
  "content": "string",
  "author_id": "uuid",
  "author_name": "string",
  "tags": ["string"],
  "status": "published|draft",
  "image_url": "string",
  "views": 0,
  "likes": 0,
  "created_at": "datetime",
  "updated_at": "datetime",
  "business_date": "datetime"
}
```

### Users Collection

```json
{
  "id": "uuid",
  "email": "string",
  "full_name": "string",
  "hashed_password": "string",
  "role": "USER|WRITER|ADMIN",
  "avatar_url": "string",
  "bio": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## ⚙️ Configuration

### Environment Variables (.env)

```ini
# Database
COSMOS_ENDPOINT=https://<account>.documents.azure.com:443/
COSMOS_KEY=<primary-key>
COSMOS_DB=blogs
COSMOS_ARTICLES=articles
COSMOS_USERS=users

# Authentication
SECRET_KEY=<jwt-secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Redis Cache
REDIS_URL=redis://localhost:6379/0

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=<connection-string>
AZURE_STORAGE_CONTAINER=uploads

# AI Search (integrates with ai_search module)
AZURE_SEARCH_ENDPOINT=https://<search>.search.windows.net
AZURE_SEARCH_KEY=<admin-key>

# Application
BASE_URL=http://localhost:8001
CORS_ORIGINS=["http://localhost:3000"]
```

## 🔍 Search Integration

The backend integrates with the `ai_search` module to provide advanced search capabilities:

### Search Features

- **Hybrid scoring** combining BM25, vector, and business signals
- **Automatic fallback** when semantic search is unavailable
- **Fuzzy matching** for author name searches
- **Pagination** with configurable page sizes
- **Result caching** for improved performance

### Search Process Flow

1. **Query normalization** and validation
2. **AI Search service** invocation via `ai_search` module
3. **Result transformation** to match API schema
4. **Cache storage** with TTL for repeated queries
5. **Response formatting** with pagination metadata

## 🚀 Development

### Running in Development Mode

```bash
# With auto-reload
python main.py

# With uvicorn directly
uvicorn main:app --reload --port 8001

# With specific configuration
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Database Setup

1. Create Cosmos DB containers with partition keys:

   - `articles` container: partition key `/author_id`
   - `users` container: partition key `/id`
2. Set up indexes for efficient queries:

   - Articles: index on `status`, `tags`, `created_at`
   - Users: index on `email`, `role`

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=backend

# Test specific modules
pytest tests/test_article_service.py
```

## 📊 Monitoring & Logging

### Health Checks

- **Database connectivity** validation
- **Redis connection** status
- **Azure services** availability
- **AI Search service** health

### Logging

- **Structured logging** with timestamp and level
- **Request/response** logging for debugging
- **Error tracking** with stack traces
- **Performance metrics** for slow queries

## 🔧 Performance Optimization

### Caching Strategy

- **Search results**: 5-minute TTL
- **User profiles**: 15-minute TTL
- **Article metadata**: 10-minute TTL
- **Popular articles**: 1-hour TTL

### Database Optimization

- **Efficient queries** with proper indexing
- **Pagination** for large result sets
- **Connection pooling** for Cosmos DB
- **Lazy loading** of related data

## 🚀 Deployment

### Docker Deployment

```bash
# Build image
docker build -f Dockerfile.backend -t article-backend .

# Run container
docker run -p 8001:8001 --env-file .env article-backend
```

### Production Considerations

- **Environment separation** (dev/staging/prod)
- **Secret management** with Azure Key Vault
- **Load balancing** for multiple instances
- **Health monitoring** and alerting
- **Backup strategies** for Cosmos DB

## 🤝 Integration

### Frontend Integration

- **CORS configuration** for React frontend
- **Standardized API responses** with consistent error handling
- **File upload** endpoints for media management
- **Real-time features** via WebSocket (future enhancement)

### AI Search Module Integration

- **Shared configuration** through environment variables
- **Direct module imports** for search functionality
- **Consistent scoring** algorithms across services
- **Error handling** with graceful fallbacks

## 📝 API Documentation

Interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`

## 🔄 Future Enhancements

- **GraphQL** API support
- **Real-time notifications** via WebSocket
- **Advanced analytics** and reporting
- **Content recommendation** system
- **Multi-language** support
- **Advanced caching** with Redis Cluster
