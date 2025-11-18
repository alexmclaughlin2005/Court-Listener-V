# Citation Quality Analysis - Implementation Progress

## Project Status: Phase 2 - Backend Services 🚧

### Completed ✅

#### Phase 1: Database & Models ✅

**1. Design Decisions Finalized**
- **Depth Strategy**: Breadth-first analysis
- **UI**: List-based with expandable sections
- **Trigger**: On-demand button click
- **Storage**: Full citation tree with relationships
- **Incremental**: Yes, skip previously analyzed levels
- **Opinion Text**: Full text required for AI analysis
- **Re-evaluation**: Post-analysis review for cascading risk

#### 2. Database Schema Created
**File**: `backend/migrations/add_citation_quality_tables.sql`

**Tables Created**:
1. `citation_quality_analysis` - Individual citation assessments
   - Stores AI quality analysis results
   - Reusable across multiple analysis trees
   - Indexed for fast lookups

2. `citation_analysis_tree` - Complete analysis trees
   - Full tree storage with JSONB
   - Incremental update support
   - Status tracking and metrics

**Migration Scripts**:
- `run_citation_quality_migration.py` - SQLAlchemy version
- `run_citation_quality_migration_simple.py` - psycopg2 version (recommended)

**To Run Migration**:
```bash
export DATABASE_URL="postgresql://postgres:PASSWORD@host:port/railway"
python3 backend/migrations/run_citation_quality_migration_simple.py
```

**3. Citation Data Fetcher Service** ✅
**File**: `backend/app/services/citation_data_fetcher.py`

Successfully implemented CourtListener API integration:
- `ensure_opinion_exists()` - Check DB first, fetch from API if missing
- `ensure_opinion_text()` - Ensure full opinion text available
- `get_opinion_text()` - Get text with truncation (150k char limit)
- `batch_ensure_opinions()` - Batch DB lookup + sequential API fetching
- `get_opinion_citations()` - Get cited opinion IDs
- Rate limiting: 0.72s delay (stays under 5000/hour)
- 404 caching (24 hour TTL)
- Retry logic with exponential backoff

**4. Citation Quality Analyzer** ✅
**File**: `backend/app/services/citation_quality_analyzer.py`

Successfully implemented AI-powered quality assessment:
- `analyze_citation_quality()` - Main analysis with Claude Haiku 4.5
- `get_cached_analysis()` - Retrieve cached results
- `save_analysis()` - Persist to citation_quality_analysis table
- Comprehensive prompt with opinion text + treatment context
- JSON response parsing and validation
- Returns: quality_assessment, confidence, risk_score, summary, boolean flags
- Model: claude-haiku-4-5-20251001 (1000 max tokens)
- Quality categories: GOOD, QUESTIONABLE, OVERRULED, SUPERSEDED, UNCERTAIN

---

## In Progress 🚧 (Phase 2: Backend Services)

### Next: Recursive Citation Analyzer

### 2. Create SQLAlchemy Models
**File**: `backend/app/models/citation_quality.py`

**Models Needed**:
- `CitationQualityAnalysis` - Maps to citation_quality_analysis table
- `CitationAnalysisTree` - Maps to citation_analysis_tree table

**Key Fields**:
- Enum for quality_assessment (GOOD, QUESTIONABLE, OVERRULED, etc.)
- Enum for status (in_progress, completed, failed)
- JSON serialization for tree_data

### 3. Implement Citation Data Fetcher
**File**: `backend/app/services/citation_data_fetcher.py`

**Purpose**: Fetch missing case data from CourtListener API

**Functions to Implement**:
- `fetch_opinion_data(opinion_id: int) -> Dict`
- `fetch_cluster_data(cluster_id: int) -> Dict`
- `ensure_opinion_exists(opinion_id: int, db: Session) -> Opinion`
- `ensure_opinion_text(opinion: Opinion, db: Session) -> str`
- `batch_fetch_opinions(opinion_ids: List[int], db: Session)`

**CourtListener API Endpoints**:
- `GET /api/rest/v4/opinions/{id}/`
- `GET /api/rest/v4/clusters/{id}/`
- `GET /api/rest/v4/opinions-cited/?citing_opinion={id}`

**Features**:
- Rate limiting (5000/hour)
- Retry logic with exponential backoff
- Cache 404s to avoid repeated failures
- Fetch full opinion text (plain_text or html)

### 4. Implement AI Citation Quality Analyzer
**File**: `backend/app/services/citation_quality_analyzer.py`

**Purpose**: Use Claude Haiku 3.5 to analyze citation quality

**Functions to Implement**:
- `analyze_citation_quality(opinion: Opinion, db: Session) -> CitationQualityResult`
- `get_cached_analysis(opinion_id: int, db: Session) -> Optional[CitationQualityAnalysis]`
- `save_analysis(opinion_id: int, result: Dict, db: Session)`

**AI Integration**:
- Use Anthropic Python SDK
- Model: `claude-3-5-haiku-20241022`
- Pass FULL opinion text (truncate to 150k chars if needed)
- Include treatment data from `citation_treatment` table
- Parse JSON response for quality_assessment, confidence, risk_score, etc.

**Prompt Format**:
```
Analyze this legal case citation for quality and reliability:

Case: {case_name}
Court: {court_name}
Date Filed: {date_filed}

=== FULL OPINION TEXT ===
{full_opinion_text}
=== END OPINION TEXT ===

Treatment Status: {treatment_type} ({severity})
...
```

### 5. Implement Recursive Citation Analyzer
**File**: `backend/app/services/recursive_citation_analyzer.py`

**Purpose**: Orchestrate breadth-first recursive analysis

**Class**: `RecursiveCitationAnalyzer`

**Methods**:
- `analyze_citation_tree(root_opinion_id, max_depth, db) -> AnalysisResult`
- `_analyze_level(opinion_ids, depth, max_depth, visited, db) -> List[Node]`
- `_calculate_risk_score(tree) -> RiskAssessment`
- `_re_evaluate_parents(tree, db) -> UpdatedRiskScores`

**Algorithm**:
1. Check for existing tree, load if incremental update
2. Breadth-first traversal (level by level)
3. For each citation:
   - Fetch opinion data
   - Ensure full text available
   - Check cache or run AI analysis
   - Store results
4. After all levels: re-evaluate parent citations
5. Save complete tree

### 6. Create API Endpoints
**File**: `backend/app/api/v1/citation_quality.py`

**Endpoints**:
- `POST /api/v1/citation-quality/analyze/{opinion_id}` - Start analysis
- `GET /api/v1/citation-quality/{opinion_id}` - Get cached analysis
- `POST /api/v1/citation-quality/batch` - Batch analysis
- `GET /api/v1/citation-quality/stats` - Statistics

---

## Phase 3: Frontend Implementation

### 7. Build CitationQualityAnalysis Component
**File**: `frontend/src/components/CitationQualityAnalysis.tsx`

**Features**:
- "Analyze Citation Quality" button
- Loading state with progress
- List-based UI with expandable sections:
  - High Risk Citations section (top)
  - Quick Stats dashboard
  - All Citations by Level (expandable)
- Filter by quality assessment
- View full AI summary per citation
- Links to view case details

### 8. Integrate with Existing Pages
- **CitationNetworkPage**: Add analysis button
- **CaseDetailFlyout**: Add "Citation Quality" tab
- **TreatmentSummary**: Show quality score

---

## Technical Decisions

### Caching Strategy
1. **Database Cache**: `citation_quality_analysis` table
2. **Tree Cache**: `citation_analysis_tree` table with incremental support
3. **Future**: Redis for hot analysis trees

### Performance Targets
- Complete 4-level analysis in <30 seconds
- Handle 100 citations per level
- Achieve 70%+ cache hit rate
- Parallel processing per level with `asyncio.gather()`

### Cost Management
- Use Haiku (cheapest model) for quality analysis
- Reuse cached analyses aggressively
- Truncate opinion text to 150k chars (~37.5k tokens)
- Typical cost per analysis: ~$0.0003-0.001

---

## Testing Plan

### Unit Tests
- Test AI analyzer with mocked responses
- Test recursive analyzer with sample trees
- Test data fetcher with mocked API

### Integration Tests
- End-to-end analysis flow
- Caching behavior
- Circular citation handling
- Incremental updates

### Performance Tests
- Benchmark 4-level analysis
- Test with 100+ citations
- Measure cache hit rates

---

## Timeline Estimate

- **Week 1** (Current): Database schema ✅
- **Week 2**: Backend services (data fetcher, AI analyzer)
- **Week 3**: Recursive analyzer + API endpoints
- **Week 4**: Frontend component + integration
- **Week 5**: Testing, optimization, deployment

---

## Running the Migration

**Prerequisites**:
1. PostgreSQL database running
2. `search_opinion` table exists
3. DATABASE_URL environment variable set

**Steps**:
```bash
cd backend

# Set DATABASE_URL
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@switchback.proxy.rlwy.net:49807/railway"

# Run migration
python3 migrations/run_citation_quality_migration_simple.py

# Verify tables created
psql $DATABASE_URL -c "\dt citation_*"
```

**Expected Output**:
```
✅ Migration completed successfully!

Next steps:
  1. Create SQLAlchemy models for these tables
  2. Implement citation_data_fetcher.py service
  3. Implement citation_quality_analyzer.py service
```

---

## Questions / Issues

**Q: What if CourtListener API is rate limited?**
A: Implement request queuing and prioritize cached results. Consider background job processing for deep analyses.

**Q: How to handle circular citations?**
A: Maintain visited set during traversal. Skip citations already in current analysis path.

**Q: What about cost control?**
A: Set per-user quotas, aggressive caching, monitor token usage via Anthropic dashboard.

**Q: Re-evaluation logic details?**
A: After completing all 4 levels, scan for Level 3-4 citations with high risk scores. Propagate risk up to parent citations (Levels 1-2) and update their assessments.

---

**Last Updated**: November 18, 2025
**Status**: ✅ Phase 1 Complete - Database Schema Created
**Next**: Create SQLAlchemy models
