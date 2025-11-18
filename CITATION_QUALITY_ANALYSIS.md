# Citation Quality Analysis System

## Overview
The Citation Quality Analysis system recursively analyzes citation chains up to 4 levels deep, automatically fetches missing case data from CourtListener API, performs AI-powered quality analysis on each citation, and caches results for reuse across cases.

## Purpose
When viewing a case, understand not just what it cites, but whether those cited cases are still good law. This helps identify:
- Cases that rely on overruled precedent
- Questionable citations that have been criticized
- High-risk citation chains that could undermine legal arguments
- Overall reliability of a case's legal foundation

---

## Architecture Summary

### New Database Table: `citation_quality_analysis`
Stores AI analysis results for each citation relationship, reusable across cases.

### Core Flow
1. User triggers analysis for a case (Opinion ID)
2. Fetch all cases cited by this case (Level 1)
3. For each Level 1 case:
   - Ensure case data exists in DB (fetch from API if missing)
   - Run Haiku AI analysis to determine quality/overruled status
   - Cache analysis result in `citation_quality_analysis` table
4. Repeat recursively for Levels 2, 3, and 4
5. Return aggregated results with risk scoring

---

## Phase 1: Database Schema Design

### New Table: `citation_quality_analysis`

```sql
CREATE TABLE citation_quality_analysis (
    id SERIAL PRIMARY KEY,
    cited_opinion_id INTEGER NOT NULL REFERENCES search_opinion(id),

    -- AI Analysis Results
    quality_assessment VARCHAR(50) NOT NULL,  -- GOOD, QUESTIONABLE, OVERRULED, SUPERSEDED, etc.
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
    UNIQUE(cited_opinion_id, analysis_version)
);

CREATE INDEX idx_citation_quality_opinion ON citation_quality_analysis(cited_opinion_id);
CREATE INDEX idx_citation_quality_assessment ON citation_quality_analysis(quality_assessment);
CREATE INDEX idx_citation_quality_risk ON citation_quality_analysis(risk_score DESC);
```

### Table Relationships
- Links to existing `search_opinion` table
- Complements existing `citation_treatment` table (treatment focuses on parentheticals, this focuses on citation quality)

---

## Phase 2: Backend API Development

### 2.1 Data Fetching Service
**File**: `backend/app/services/citation_data_fetcher.py`

**Purpose**: Fetch missing case data from CourtListener API

**Key Functions**:
- `fetch_opinion_data(opinion_id: int) -> Dict`: Fetch opinion from CL API v4
- `fetch_cluster_data(cluster_id: int) -> Dict`: Fetch cluster metadata
- `ensure_opinion_exists(opinion_id: int, db: Session) -> Opinion`: Check DB, fetch if missing
- `batch_fetch_opinions(opinion_ids: List[int], db: Session)`: Bulk fetch optimization

**CourtListener API Endpoints to Use**:
- `GET /api/rest/v4/opinions/{id}/` - Get opinion details
- `GET /api/rest/v4/clusters/{id}/` - Get cluster details
- `GET /api/rest/v4/opinions-cited/?citing_opinion={id}` - Get citations

**Error Handling**:
- Rate limiting (5000/hour from CL API)
- Retry logic with exponential backoff
- Cache 404s to avoid repeated failed lookups

---

### 2.2 AI Citation Quality Analyzer
**File**: `backend/app/services/citation_quality_analyzer.py`

**Purpose**: Use Claude Haiku 3.5 to analyze citation quality

**Key Functions**:
- `analyze_citation_quality(cited_opinion: Opinion, db: Session) -> CitationQualityResult`
- `get_cached_analysis(opinion_id: int, db: Session) -> Optional[CitationQualityAnalysis]`
- `save_analysis(opinion_id: int, result: CitationQualityResult, db: Session)`

**AI Prompt Template** (for Haiku):
```
Analyze this legal case citation for quality and reliability:

Case: {case_name}
Court: {court_name}
Date Filed: {date_filed}
Citation Count: {citation_count}

Opinion Text (excerpt): {opinion_text_excerpt}

Treatment Status: {treatment_type} ({severity})
- Negative Examples: {negative_treatment_examples}

Task: Determine if this case is safe to rely upon as legal precedent.

Respond in JSON format:
{
  "quality_assessment": "GOOD" | "QUESTIONABLE" | "OVERRULED" | "SUPERSEDED" | "UNCERTAIN",
  "confidence": 0.0-1.0,
  "is_overruled": boolean,
  "is_questioned": boolean,
  "is_criticized": boolean,
  "risk_score": 0-100,
  "summary": "2-3 sentence explanation"
}
```

**Quality Assessment Categories**:
- `GOOD`: Safe to cite, no negative treatment
- `QUESTIONABLE`: Has some criticism or questioning
- `OVERRULED`: Explicitly overruled
- `SUPERSEDED`: Replaced by statute or newer precedent
- `UNCERTAIN`: Insufficient information

---

### 2.3 Recursive Citation Analysis Engine
**File**: `backend/app/services/recursive_citation_analyzer.py`

**Purpose**: Orchestrate recursive analysis across citation levels

**Key Class**: `RecursiveCitationAnalyzer`

**Key Methods**:
```python
class RecursiveCitationAnalyzer:
    def analyze_citation_tree(
        self,
        root_opinion_id: int,
        max_depth: int = 4,
        db: Session
    ) -> RecursiveCitationAnalysisResult:
        """
        Recursively analyze citations up to max_depth levels.
        Returns aggregated results with risk scoring.
        """

    async def _analyze_level(
        self,
        opinion_ids: List[int],
        current_depth: int,
        max_depth: int,
        visited: Set[int],
        db: Session
    ) -> List[CitationAnalysisNode]:
        """
        Analyze a single level of citations.
        """

    def _calculate_risk_score(
        self,
        analysis_tree: Dict[int, CitationAnalysisNode]
    ) -> RiskAssessment:
        """
        Calculate overall risk based on citation tree.
        Weights by depth (closer citations = higher risk).
        """
```

**Algorithm**:
1. Start with root opinion
2. For current level:
   - Fetch all cited opinions from `opinions_cited` table
   - For each cited opinion:
     - Check if it's been visited (prevent cycles)
     - Ensure opinion data exists (fetch if missing)
     - Check for cached analysis in `citation_quality_analysis`
     - If no cache: run AI analysis and cache result
     - Add to current level results
   - Queue cited opinions for next level
3. Recurse to next level (depth + 1)
4. Aggregate results and calculate risk

**Performance Optimizations**:
- Parallel processing per level using `asyncio.gather()`
- Batch database queries
- Reuse cached analyses across cases
- Limit to 100 citations per level (configurable)

---

### 2.4 API Endpoints
**File**: `backend/app/api/v1/citation_quality.py`

**Router**: `/api/v1/citation-quality`

#### Endpoint 1: Analyze Citation Tree
```python
POST /api/v1/citation-quality/analyze/{opinion_id}
Query Parameters:
  - depth: int (1-4, default=4)
  - force_refresh: bool (default=false)
  - max_nodes: int (default=100)

Response:
{
  "opinion_id": 123456,
  "analysis_depth": 4,
  "total_citations_analyzed": 87,
  "analysis_summary": {
    "good_count": 65,
    "questionable_count": 12,
    "overruled_count": 8,
    "superseded_count": 2
  },
  "overall_risk_assessment": {
    "score": 35.2,
    "level": "MEDIUM",
    "confidence": 0.87,
    "factors": [
      "8 overruled cases in citation tree (9%)",
      "2 overruled cases at depth 1 (high risk)",
      "Most problematic: Smith v. Jones (overruled 2020)"
    ]
  },
  "citation_tree": [
    {
      "depth": 1,
      "opinion_id": 789012,
      "case_name": "Smith v. Jones",
      "quality_assessment": "OVERRULED",
      "confidence": 0.95,
      "risk_score": 85.0,
      "summary": "This case was explicitly overruled...",
      "children_count": 23
    },
    ...
  ],
  "high_risk_citations": [...],
  "cache_hits": 45,
  "cache_misses": 42,
  "execution_time_seconds": 12.3
}
```

#### Endpoint 2: Get Cached Analysis
```python
GET /api/v1/citation-quality/{opinion_id}
Response:
{
  "opinion_id": 123456,
  "quality_assessment": "GOOD",
  "confidence": 0.92,
  "risk_score": 5.0,
  "summary": "...",
  "analyzed_at": "2025-11-18T10:30:00Z",
  "from_cache": true
}
```

#### Endpoint 3: Batch Analysis
```python
POST /api/v1/citation-quality/batch
Body:
{
  "opinion_ids": [123, 456, 789],
  "depth": 2
}

Response:
{
  "results": [
    { "opinion_id": 123, "risk_score": 15.2, ... },
    { "opinion_id": 456, "risk_score": 67.8, ... },
    { "opinion_id": 789, "risk_score": 8.1, ... }
  ]
}
```

#### Endpoint 4: Statistics
```python
GET /api/v1/citation-quality/stats
Response:
{
  "total_analyses": 15234,
  "by_quality": {
    "GOOD": 10234,
    "QUESTIONABLE": 2345,
    "OVERRULED": 1823,
    "SUPERSEDED": 832
  },
  "average_risk_score": 18.5,
  "cache_hit_rate": 0.73
}
```

---

## Phase 3: Frontend Implementation

### 3.1 New Component: `CitationQualityAnalysis.tsx`
**Location**: `frontend/src/components/CitationQualityAnalysis.tsx`

**Purpose**: Display recursive citation analysis results

**Features**:
- Trigger analysis button
- Loading state with progress indicator
- Tree visualization of citation quality
- Risk assessment dashboard
- Expandable nodes showing AI summaries
- Filter by quality assessment
- Export results

**UI Layout**:
```
┌─────────────────────────────────────────────────────┐
│  Citation Quality Analysis                          │
│  [Analyze Citation Tree (4 levels)] [Export]        │
├─────────────────────────────────────────────────────┤
│  Overall Risk: MEDIUM (35.2/100)   ⚠️               │
│  87 citations analyzed • 8 overruled • 12 risky     │
├─────────────────────────────────────────────────────┤
│  ⚠️ High Risk Citations (10)                        │
│  ├─ [Level 1] Smith v. Jones - OVERRULED           │
│  │   Risk: 85/100 • Explicitly overruled in 2020   │
│  │   [View Details] [View Case]                    │
│  ├─ [Level 2] Doe v. State - QUESTIONABLE          │
│  └─ ...                                             │
├─────────────────────────────────────────────────────┤
│  📊 Citation Quality Breakdown                      │
│  [Good: 65] [Questionable: 12] [Overruled: 8]      │
├─────────────────────────────────────────────────────┤
│  🌳 Full Citation Tree (Click to expand levels)     │
│  └─ Current Case                                    │
│     ├─ [✅ GOOD] Case A (cited 45 times)            │
│     │  └─ [✅ GOOD] Case A1                         │
│     │  └─ [⚠️  QUESTIONABLE] Case A2                │
│     ├─ [❌ OVERRULED] Case B                        │
│     └─ [✅ GOOD] Case C                             │
└─────────────────────────────────────────────────────┘
```

---

### 3.2 Integration with Existing Pages

**CitationNetworkPage.tsx**:
- Add "Analyze Citation Quality" button next to "Risk Analysis"
- Show quality badges on network nodes
- Filter network by quality assessment

**CaseDetailFlyout.tsx**:
- Add "Citation Quality" tab
- Show quality assessment for current case
- List problematic citations

**TreatmentSummary.tsx**:
- Add quality score alongside treatment badge
- Link to full citation quality analysis

---

## Phase 4: Caching & Performance Optimization

### 4.1 Multi-Level Caching Strategy

**Level 1: Database Cache** (`citation_quality_analysis` table)
- Permanent storage of AI analyses
- Indexed for fast lookups
- Version tracking for re-analysis

**Level 2: Redis Cache** (future enhancement)
- Cache entire analysis trees (30-day TTL)
- Key format: `citation_quality:tree:{opinion_id}:{depth}`
- Reduces DB load for frequently analyzed cases

**Level 3: Application Memory Cache**
- LRU cache for hot paths
- Cache opinion data fetched from API (1-hour TTL)

### 4.2 Background Processing

**Async Job Queue** (using Celery or similar):
- Queue deep analyses (3-4 levels) as background jobs
- Return analysis ID immediately, poll for completion
- Send webhook/notification when complete

**Preemptive Analysis**:
- Analyze popular cases in background
- Trigger analysis when new citations added
- Re-analyze when treatment changes

---

## Phase 5: Testing Strategy

### 5.1 Unit Tests
- Test `citation_quality_analyzer.py` with mocked AI responses
- Test `recursive_citation_analyzer.py` with sample citation trees
- Test `citation_data_fetcher.py` with mocked API responses

### 5.2 Integration Tests
- Test full analysis flow end-to-end
- Test caching behavior
- Test API rate limiting and retries
- Test circular citation handling

### 5.3 Performance Tests
- Benchmark analysis speed (target: <30s for 4 levels)
- Test with 100+ citations per level
- Measure cache hit rates

---

## Phase 6: Monitoring & Observability

### Metrics to Track
- Analysis request volume
- Average analysis time by depth
- Cache hit/miss rates
- AI API costs (Haiku tokens used)
- CourtListener API usage
- Error rates by type

### Logging
- Log all AI analyses with opinion_id and result
- Log API fetches and cache operations
- Log analysis tree structure for debugging

---

## Implementation Timeline

### Week 1: Foundation
- [ ] Design and create `citation_quality_analysis` table
- [ ] Implement `citation_data_fetcher.py` service
- [ ] Set up unit tests

### Week 2: AI Analysis
- [ ] Implement `citation_quality_analyzer.py`
- [ ] Integrate with Anthropic Haiku API
- [ ] Test and refine AI prompts
- [ ] Implement caching logic

### Week 3: Recursive Engine
- [ ] Implement `recursive_citation_analyzer.py`
- [ ] Handle circular citations and depth limits
- [ ] Optimize performance with parallel processing
- [ ] Integration testing

### Week 4: API & Frontend
- [ ] Build API endpoints (`citation_quality.py`)
- [ ] Create `CitationQualityAnalysis.tsx` component
- [ ] Integrate with existing pages
- [ ] End-to-end testing

### Week 5: Polish & Deploy
- [ ] Performance optimization
- [ ] Add monitoring and logging
- [ ] Write documentation
- [ ] Deploy to production
- [ ] Monitor and iterate

---

## Open Questions

1. **Rate Limiting**: How should we handle CourtListener API rate limits (5000/hour)? Should we implement request queuing?

2. **Cost Control**: AI analysis costs scale with citations. Should we limit analyses to paid users or cap free tier usage?

3. **Staleness**: How often should we re-analyze citations? When treatment changes? On a schedule?

4. **Circular Citations**: How should we handle cases that cite each other in a loop?

5. **Missing Data**: What should we do if CourtListener API doesn't have data for a cited case?

6. **Prioritization**: Should we analyze depth-first or breadth-first? Parallel levels or sequential?

---

## Success Metrics

- **Functionality**: Successfully analyze 95%+ of citation trees up to 4 levels deep
- **Performance**: Complete 4-level analysis in <30 seconds for typical cases (<100 total citations)
- **Cache Efficiency**: Achieve 70%+ cache hit rate after initial deployment
- **Accuracy**: AI quality assessments align with manual review 85%+ of the time
- **User Adoption**: 20%+ of case views trigger citation quality analysis within 3 months

---

## Risk Mitigation

**Risk**: CourtListener API rate limits block analyses
**Mitigation**: Implement request queuing, background jobs, aggressive caching

**Risk**: AI analysis costs spiral out of control
**Mitigation**: Usage quotas, cost monitoring, prefer cached results

**Risk**: Performance degrades with deep trees
**Mitigation**: Configurable depth limits, pagination, lazy loading

**Risk**: Circular citations cause infinite loops
**Mitigation**: Visited set tracking, maximum node limits per level

---

## Design Decisions Needed

1. **Depth Strategy**: Should we analyze breadth-first (all of level 1, then all of level 2) or depth-first (follow one citation chain to depth 4 before next chain)?

2. **UI Preference**: Do you want a tree visualization (like your network graph) or a list-based view with expandable sections?

3. **Trigger Point**: Should this be triggered automatically when viewing a case, or only on-demand when user clicks a button?

4. **Storage Scope**: Should we store the full analysis tree (relationships between citations) or just individual citation assessments?

5. **Incremental Analysis**: If we've analyzed levels 1-2 before, should we skip those and just analyze levels 3-4?

---

## Related Documentation

- [TREATMENT_ANALYSIS.md](TREATMENT_ANALYSIS.md) - Citation treatment classifier
- [CITATION_NETWORK_FEATURES.md](CITATION_NETWORK_FEATURES.md) - Citation network visualization
- [courtlistenerapi.md](courtlistenerapi.md) - CourtListener API documentation

---

**Last Updated**: November 18, 2025
**Status**: 📋 Planning Phase
**Next Steps**: Answer design questions, create database migration
