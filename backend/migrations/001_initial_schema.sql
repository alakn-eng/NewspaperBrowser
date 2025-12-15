-- Time Browser - Initial Schema
-- This migration creates the core browse and retrieval tables

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- BROWSE TABLES (Canonical Data)
-- ============================================================================

-- Newspapers: Publication metadata
CREATE TABLE newspapers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    city TEXT,
    country TEXT,
    start_year INT,
    end_year INT,
    description TEXT,
    source_type TEXT NOT NULL DEFAULT 'upload', -- upload, loc_batch, etc
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_newspapers_name ON newspapers(name);

-- Issues: Specific dated publications
CREATE TABLE issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    newspaper_id UUID NOT NULL REFERENCES newspapers(id) ON DELETE CASCADE,
    issue_date DATE NOT NULL,
    num_pages INT DEFAULT 0,
    source_type TEXT NOT NULL DEFAULT 'upload',
    source_external_id TEXT, -- ID from LoC or other external source
    metadata JSONB, -- Flexible future use
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_newspaper_issue UNIQUE (newspaper_id, issue_date)
);

CREATE INDEX idx_issues_newspaper ON issues(newspaper_id);
CREATE INDEX idx_issues_date ON issues(issue_date DESC);
CREATE INDEX idx_issues_newspaper_date ON issues(newspaper_id, issue_date DESC);

-- Pages: Individual scanned pages with OCR
CREATE TABLE pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID NOT NULL REFERENCES issues(id) ON DELETE CASCADE,
    page_number INT NOT NULL,
    image_path TEXT NOT NULL, -- Supabase Storage path

    -- OCR data (canonical storage)
    ocr_text TEXT,
    ocr_confidence REAL,
    ocr_provider TEXT,
    ocr_version TEXT,
    ocr_meta JSONB,

    ingestion_status TEXT NOT NULL DEFAULT 'pending', -- pending, ocr_pending, ocr_completed, ocr_failed, indexed
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_issue_page UNIQUE (issue_id, page_number)
);

CREATE INDEX idx_pages_issue ON pages(issue_id);
CREATE INDEX idx_pages_status ON pages(ingestion_status);

-- ============================================================================
-- RETRIEVAL TABLES (Rebuildable Index)
-- ============================================================================

-- Segments: Text chunks with embeddings for semantic search
CREATE TABLE segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    segment_index INT NOT NULL, -- 0-based index within page
    segment_text TEXT NOT NULL,
    segment_hash TEXT NOT NULL, -- Deterministic hash for idempotency
    segmenter_version TEXT NOT NULL DEFAULT 'v0_fixed_chars_800_100',
    metadata JSONB,

    -- Embedding vector (can be moved to separate table later)
    embedding VECTOR(1536), -- OpenAI text-embedding-3-small

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT unique_page_segment_hash UNIQUE (page_id, segment_hash)
);

CREATE INDEX idx_segments_page ON segments(page_id);
CREATE INDEX idx_segments_hash ON segments(segment_hash);

-- Vector similarity search index (IVFFlat for performance)
-- Note: This requires training data. For small datasets, use brute force (no index)
-- CREATE INDEX idx_segments_embedding ON segments USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- For MVP with small data, use this simpler index:
CREATE INDEX idx_segments_embedding ON segments USING ivfflat (embedding vector_cosine_ops);

-- ============================================================================
-- INGEST JOBS (Async Job Tracking)
-- ============================================================================

-- Ingest Jobs: Track ingestion progress and enable idempotency
CREATE TABLE ingest_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key TEXT UNIQUE NOT NULL,
    issue_id UUID REFERENCES issues(id) ON DELETE SET NULL,

    status TEXT NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed

    -- Progress tracking (JSONB for flexibility)
    progress JSONB DEFAULT '{
        "pages_total": 0,
        "pages_processed": 0,
        "pages_succeeded": 0,
        "pages_failed": 0,
        "current_stage": "initializing",
        "errors": []
    }'::jsonb,

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ingest_jobs_key ON ingest_jobs(idempotency_key);
CREATE INDEX idx_ingest_jobs_status ON ingest_jobs(status);
CREATE INDEX idx_ingest_jobs_created ON ingest_jobs(created_at DESC);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for pages table
CREATE TRIGGER update_pages_updated_at
    BEFORE UPDATE ON pages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for ingest_jobs table
CREATE TRIGGER update_ingest_jobs_updated_at
    BEFORE UPDATE ON ingest_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- NOTES
-- ============================================================================

-- Browse vs Retrieval Boundary:
-- - Browse tables (newspapers, issues, pages) are canonical and never depend on retrieval
-- - Retrieval tables (segments) can be dropped and rebuilt without affecting browse
-- - Search results are page-centric (SearchHit has page_id, not segment_id)

-- Idempotency:
-- - Issues: UNIQUE (newspaper_id, issue_date)
-- - Pages: UNIQUE (issue_id, page_number)
-- - Segments: UNIQUE (page_id, segment_hash)
-- - Ingest Jobs: UNIQUE (idempotency_key)

-- Future Migrations:
-- - Separate embeddings into embeddings table if needed
-- - Add articles table for extracted entities
-- - Add timeline/knowledge graph tables
