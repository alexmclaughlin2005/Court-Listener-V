-- Migration: Add citation quality analysis tables
-- Date: 2025-11-18
-- Description: Creates citation_quality_analysis and citation_analysis_tree tables for recursive citation quality analysis

-- Table 1: citation_quality_analysis
-- Stores individual citation quality assessments (reusable across analysis trees)
CREATE TABLE IF NOT EXISTS citation_quality_analysis (
    id SERIAL PRIMARY KEY,
    cited_opinion_id INTEGER NOT NULL REFERENCES search_opinion(id) ON DELETE CASCADE,

    -- AI Analysis Results
    quality_assessment VARCHAR(50) NOT NULL,  -- GOOD, QUESTIONABLE, OVERRULED, SUPERSEDED, UNCERTAIN
    confidence FLOAT NOT NULL,                -- 0.0 to 1.0
    ai_summary TEXT,                          -- Brief AI explanation
    ai_model VARCHAR(100),                    -- Model used (e.g., "claude-3-5-haiku-20241022")

    -- Risk Indicators
    is_overruled BOOLEAN DEFAULT FALSE,
    is_questioned BOOLEAN DEFAULT FALSE,
    is_criticized BOOLEAN DEFAULT FALSE,
    risk_score FLOAT DEFAULT 0.0,            -- 0-100 risk score

    -- Metadata
    analysis_version INTEGER DEFAULT 1,      -- For future re-analysis tracking
    analyzed_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW(),

    -- Prevent duplicate analyses
    CONSTRAINT unique_citation_quality UNIQUE(cited_opinion_id, analysis_version)
);

-- Indexes for citation_quality_analysis
CREATE INDEX IF NOT EXISTS idx_citation_quality_opinion ON citation_quality_analysis(cited_opinion_id);
CREATE INDEX IF NOT EXISTS idx_citation_quality_assessment ON citation_quality_analysis(quality_assessment);
CREATE INDEX IF NOT EXISTS idx_citation_quality_risk ON citation_quality_analysis(risk_score DESC);
CREATE INDEX IF NOT EXISTS idx_citation_quality_analyzed_at ON citation_quality_analysis(analyzed_at DESC);

-- Table 2: citation_analysis_tree
-- Stores complete analysis trees for specific root opinions (for incremental updates and full tree storage)
CREATE TABLE IF NOT EXISTS citation_analysis_tree (
    id SERIAL PRIMARY KEY,
    root_opinion_id INTEGER NOT NULL REFERENCES search_opinion(id) ON DELETE CASCADE,

    -- Analysis Configuration
    max_depth INTEGER NOT NULL,              -- Depth requested (1-4)
    current_depth INTEGER NOT NULL,          -- Deepest level completed so far

    -- Aggregated Results
    total_citations_analyzed INTEGER DEFAULT 0,
    good_count INTEGER DEFAULT 0,
    questionable_count INTEGER DEFAULT 0,
    overruled_count INTEGER DEFAULT 0,
    superseded_count INTEGER DEFAULT 0,
    uncertain_count INTEGER DEFAULT 0,

    -- Risk Assessment
    overall_risk_score FLOAT DEFAULT 0.0,
    overall_risk_level VARCHAR(20),          -- LOW, MEDIUM, HIGH
    risk_factors JSONB,                      -- Array of risk factor descriptions

    -- Tree Structure (JSONB for flexibility)
    tree_data JSONB NOT NULL,                -- Full citation tree with relationships
    high_risk_citations JSONB,               -- Subset of most problematic citations

    -- Metadata
    analysis_started_at TIMESTAMP DEFAULT NOW(),
    analysis_completed_at TIMESTAMP,
    last_updated TIMESTAMP DEFAULT NOW(),
    execution_time_seconds FLOAT,
    cache_hits INTEGER DEFAULT 0,
    cache_misses INTEGER DEFAULT 0,

    -- Status tracking
    status VARCHAR(20) DEFAULT 'in_progress', -- in_progress, completed, failed
    error_message TEXT,

    -- Allow multiple analyses per opinion (different depths, re-runs)
    CONSTRAINT unique_tree_analysis UNIQUE(root_opinion_id, max_depth, analysis_completed_at)
);

-- Indexes for citation_analysis_tree
CREATE INDEX IF NOT EXISTS idx_tree_root_opinion ON citation_analysis_tree(root_opinion_id);
CREATE INDEX IF NOT EXISTS idx_tree_status ON citation_analysis_tree(status);
CREATE INDEX IF NOT EXISTS idx_tree_risk_level ON citation_analysis_tree(overall_risk_level);
CREATE INDEX IF NOT EXISTS idx_tree_completed ON citation_analysis_tree(analysis_completed_at DESC);
CREATE INDEX IF NOT EXISTS idx_tree_data ON citation_analysis_tree USING GIN (tree_data);
CREATE INDEX IF NOT EXISTS idx_tree_high_risk ON citation_analysis_tree USING GIN (high_risk_citations);

-- Verify tables were created
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name IN ('citation_quality_analysis', 'citation_analysis_tree')
ORDER BY table_name, ordinal_position;

-- Verify indexes were created
SELECT tablename, indexname
FROM pg_indexes
WHERE tablename IN ('citation_quality_analysis', 'citation_analysis_tree')
ORDER BY tablename, indexname;
