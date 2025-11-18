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

### Table 1: `citation_quality_analysis`
Stores individual citation quality assessments (reusable across analysis trees).

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

### Table 2: `citation_analysis_tree`
Stores complete analysis trees for specific root opinions (for incremental updates and full tree storage).

```sql
CREATE TABLE citation_analysis_tree (
    id SERIAL PRIMARY KEY,
    root_opinion_id INTEGER NOT NULL REFERENCES search_opinion(id),

    -- Analysis Configuration
    max_depth INTEGER NOT NULL,              -- Depth analyzed (1-4)
    current_depth INTEGER NOT NULL,          -- Deepest level completed

    -- Aggregated Results
    total_citations_analyzed INTEGER DEFAULT 0,
    good_count INTEGER DEFAULT 0,
    questionable_count INTEGER DEFAULT 0,
    overruled_count INTEGER DEFAULT 0,
    superseded_count INTEGER DEFAULT 0,

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
    UNIQUE(root_opinion_id, max_depth, analysis_completed_at)
);

CREATE INDEX idx_tree_root_opinion ON citation_analysis_tree(root_opinion_id);
CREATE INDEX idx_tree_status ON citation_analysis_tree(status);
CREATE INDEX idx_tree_risk_level ON citation_analysis_tree(overall_risk_level);
CREATE INDEX idx_tree_completed ON citation_analysis_tree(analysis_completed_at DESC);
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

=== FULL OPINION TEXT ===
{full_opinion_text}
=== END OPINION TEXT ===

Treatment Status: {treatment_type} ({severity})
- Negative Examples: {negative_treatment_examples}
- Negative Treatments Count: {negative_count}
- Total Treatments: {total_treatments}

Context: This case is being cited by another case. We need to determine if it is safe to rely upon as legal precedent.

Task: Determine if this case is safe to rely upon as legal precedent.

Respond in JSON format:
{
  "quality_assessment": "GOOD" | "QUESTIONABLE" | "OVERRULED" | "SUPERSEDED" | "UNCERTAIN",
  "confidence": 0.0-1.0,
  "is_overruled": boolean,
  "is_questioned": boolean,
  "is_criticized": boolean,
  "risk_score": 0-100,
  "summary": "2-3 sentence explanation of why this assessment was made"
}
```

**Note**: Full opinion text is required for accurate analysis. Text will be fetched from:
1. Database `search_opinion.plain_text` or `search_opinion.html` (preferred)
2. CourtListener API `/api/rest/v4/opinions/{id}/` if missing from DB
3. Truncate to 150,000 characters (~37,500 tokens) if necessary for API limits

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

**Algorithm** (Breadth-First):
1. **Initialization**:
   - Check if tree exists for this opinion at requested depth
   - If exists and current_depth >= max_depth: return cached tree
   - If exists but current_depth < max_depth: load tree, continue from next level
   - If not exists: create new tree record with status='in_progress'

2. **For each level (breadth-first)**:
   - Fetch all cited opinions from `opinions_cited` table for current level
   - For each cited opinion:
     - Check if it's been visited (prevent cycles)
     - Ensure opinion data exists in DB:
       - Check for opinion text (plain_text or html)
       - If missing, fetch from CourtListener API
     - Check for cached analysis in `citation_quality_analysis`
     - If no cache:
       - Fetch treatment data from `citation_treatment` table
       - Run AI analysis with FULL opinion text
       - Cache result in `citation_quality_analysis`
     - Add to current level results with relationships
     - Add cited opinions to queue for next level

3. **After completing all levels**:
   - Calculate overall risk score
   - **Re-evaluation Pass**: Check if any Level 3-4 citations have strong negative treatment
     - If yes, re-evaluate their parent citations (Levels 1-2) with this new context
     - Update risk scores for affected parent citations
   - Save complete tree to `citation_analysis_tree`
   - Update status='completed'

4. **Return aggregated results**

**Performance Optimizations**:
- Parallel processing per level using `asyncio.gather()`
- Batch database queries (fetch all level citations in one query)
- Reuse cached analyses across cases
- Limit to 100 citations per level (configurable)
- Incremental updates: skip levels already analyzed

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

**UI Layout** (List-Based with Expandable Sections):
```
┌─────────────────────────────────────────────────────────────────┐
│  Citation Quality Analysis                                      │
│  [Analyze Citation Quality (4 levels)] [Export] [Refresh]      │
├─────────────────────────────────────────────────────────────────┤
│  ⚠️  Overall Risk: MEDIUM (35.2/100)                           │
│  87 citations analyzed • 8 overruled • 12 questionable         │
│  Analysis completed in 12.3s • 45 from cache, 42 new          │
├─────────────────────────────────────────────────────────────────┤
│  📊 Quick Stats                                                 │
│  [✅ Good: 65 (75%)] [⚠️  Questionable: 12 (14%)]              │
│  [❌ Overruled: 8 (9%)] [🔄 Superseded: 2 (2%)]                │
├─────────────────────────────────────────────────────────────────┤
│  🚨 High Risk Citations (8) [Click to expand all]              │
│  ▼ Level 1 (2 high-risk citations)                             │
│    • Smith v. Jones (Opinion ID: 789012) ❌ OVERRULED          │
│      Risk: 85/100 | Confidence: 95% | Cited: 2015             │
│      "This case was explicitly overruled in 2020 by..."        │
│      [View Full Analysis] [View Case] [View Network]           │
│                                                                 │
│    • Brown v. Board (Opinion ID: 123456) ⚠️  QUESTIONABLE      │
│      Risk: 67/100 | Confidence: 82% | Cited: 2018             │
│      "Multiple courts have questioned this holding..."         │
│      [View Full Analysis] [View Case] [View Network]           │
│                                                                 │
│  ▶ Level 2 (3 high-risk citations) [Click to expand]          │
│  ▶ Level 3 (2 high-risk citations) [Click to expand]          │
│  ▶ Level 4 (1 high-risk citation) [Click to expand]           │
├─────────────────────────────────────────────────────────────────┤
│  📋 All Citations by Level                                      │
│  ▼ Level 1: Direct Citations (23 cases) [Filter: All ▼]       │
│    ✅ GOOD (18) | ⚠️  QUESTIONABLE (3) | ❌ OVERRULED (2)      │
│                                                                 │
│    1. ✅ Case A v. Case B (Opinion ID: 111222)                 │
│       Risk: 5/100 | Court: 9th Circuit | Date: 2020           │
│       "Well-established precedent with no negative..."         │
│       [Expand to see 12 Level 2 citations] [View Case]        │
│                                                                 │
│    2. ❌ Smith v. Jones (Opinion ID: 789012)                   │
│       Risk: 85/100 | Court: District Court | Date: 2015       │
│       "This case was explicitly overruled..."                  │
│       [Expand to see 8 Level 2 citations] [View Case]         │
│       ...                                                       │
│                                                                 │
│  ▶ Level 2: Secondary Citations (34 cases) [Click to expand]  │
│  ▶ Level 3: Tertiary Citations (21 cases) [Click to expand]   │
│  ▶ Level 4: Quaternary Citations (9 cases) [Click to expand]  │
└─────────────────────────────────────────────────────────────────┘
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

## Design Decisions ✅

1. **Depth Strategy**: ✅ **BREADTH-FIRST** - Analyze all of level 1, then all of level 2, etc.

2. **UI Preference**: ✅ **LIST-BASED VIEW** - Expandable sections organized by depth level

3. **Trigger Point**: ✅ **ON-DEMAND BUTTON** - User clicks "Analyze Citation Quality" button to trigger

4. **Storage Scope**: ✅ **FULL TREE** - Store complete analysis tree with relationships between citations

5. **Incremental Analysis**: ✅ **YES** - Skip previously analyzed levels, only analyze new depths

6. **Opinion Text**: ✅ **FULL TEXT REQUIRED** - Pass complete opinion text (from DB or API) to AI for analysis

7. **Re-evaluation**: ✅ **POST-ANALYSIS REVIEW** - After completing 4 levels, re-evaluate top-level cases if deeper citations show strong negative treatment

---

## Related Documentation

- [TREATMENT_ANALYSIS.md](TREATMENT_ANALYSIS.md) - Citation treatment classifier
- [CITATION_NETWORK_FEATURES.md](CITATION_NETWORK_FEATURES.md) - Citation network visualization
- [courtlistenerapi.md](courtlistenerapi.md) - CourtListener API documentation

---

**Last Updated**: November 18, 2025
**Status**: 📋 Planning Phase
**Next Steps**: Answer design questions, create database migration
