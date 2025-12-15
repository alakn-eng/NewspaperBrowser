# Time Browser - Backend

FastAPI backend for the Time Browser historical newspaper exploration application.

## Architecture

This backend follows a clean architecture with clear boundaries:

- **Browse Context**: Canonical newspaper data (newspapers, issues, pages)
- **Retrieval Context**: Rebuildable search index (segments, embeddings)
- **Use Cases**: Orchestration layer (ingestion, search)
- **Services**: Pluggable external integrations (OCR, storage, embeddings)
- **Repositories**: Data access layer

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key (admin access)
- `OPENAI_API_KEY`: OpenAI API key for embeddings and summaries
- `ADMIN_API_KEY`: Secret key for admin endpoints

### 3. Run Database Migration

Run the migration SQL against your Supabase database:

```sql
-- In Supabase SQL editor, run:
-- migrations/001_initial_schema.sql
```

Or use the Supabase CLI:

```bash
supabase db push
```

### 4. Run Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Acceptance tests (boundary verification)
pytest tests/acceptance/ -v
```

### Run Tests with Coverage

```bash
pytest --cov=app --cov-report=html
```

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Environment configuration
│   ├── dependencies.py          # Dependency injection
│   ├── models/
│   │   ├── db/                  # Database models (Pydantic)
│   │   │   ├── browse.py        # Browse context models
│   │   │   └── retrieval.py     # Retrieval context models
│   │   └── api/                 # API request/response models
│   ├── repositories/            # Data access layer
│   ├── services/                # External integrations
│   ├── usecases/                # Business logic orchestration
│   ├── routes/                  # API endpoints
│   └── middleware/              # Auth, CORS, etc.
├── migrations/                  # Database migrations (SQL)
├── tests/                       # Test suite
└── requirements.txt
```

## Key Design Principles

### Browse vs Retrieval Boundary

- **Browse endpoints** (`/api/issues`, `/api/pages`) only query browse tables
- **Search endpoints** (`/api/search`) use retrieval index but return page-centric results
- **Retrieval tables can be dropped and rebuilt** without affecting browse functionality

### Idempotency

All ingestion operations are idempotent via:
- `UNIQUE (newspaper_id, issue_date)` on issues
- `UNIQUE (issue_id, page_number)` on pages
- `UNIQUE (page_id, segment_hash)` on segments
- `Idempotency-Key` header on ingest jobs

### API Contracts

Search results are always **page-centric**:
- `SearchHit` contains `page_id`, `snippet`, `score`
- Internal segment/chunk IDs are never exposed to clients

## Development Workflow

### Branch-Based Development

Each feature is developed in isolation:

1. Create feature branch
2. Implement feature with tests
3. Verify tests pass
4. Merge to main

See root README for detailed branch plan.

## API Documentation

Once the server is running, visit:
- **Interactive docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
