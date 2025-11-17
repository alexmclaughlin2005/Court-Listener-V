# Citation Treatment Detection - Project Plan

## 🎯 Project Goal
Build a system to detect and display whether cases have been overruled, affirmed, distinguished, or otherwise treated by subsequent decisions using parenthetical text analysis.

---

## 📋 Phase 1: Database Schema & Models (30 mins)

### Task 1.1: Create Parenthetical Model
**File**: `backend/app/models/parenthetical.py`
- [ ] Define Parenthetical SQLAlchemy model
- [ ] Fields: id, text, score, described_opinion_id, describing_opinion_id, group_id
- [ ] Add indexes for opinion lookups
- [ ] Add relationship to Opinion model

### Task 1.2: Create Treatment Analysis Table
**File**: `backend/app/models/citation_treatment.py`
- [ ] Define CitationTreatment model
- [ ] Fields: id, opinion_id, treatment_type, severity, treatment_count, last_updated
- [ ] Treatment types: OVERRULED, REVERSED, AFFIRMED, DISTINGUISHED, QUESTIONED, CITED
- [ ] Severity: NEGATIVE, POSITIVE, NEUTRAL, UNKNOWN
- [ ] Add indexes for fast lookups

### Task 1.3: Update Main Models
**File**: `backend/app/models/__init__.py`
- [ ] Export new models
- [ ] Update Opinion model with treatment relationship

**Database Migration**:
```bash
# Create tables
curl -X POST https://court-listener-v-production.up.railway.app/init-db
```

---

## 📋 Phase 2: Data Import (1 hour)

### Task 2.1: Add Parenthetical Import Function
**File**: `scripts/import_csv_bulk.py`
- [ ] Add `import_parentheticals()` function
- [ ] Validate opinion_id references exist
- [ ] Batch insert with error handling
- [ ] Add to argparse and main()

### Task 2.2: Import Sample Parentheticals
**Command**:
```bash
export DATABASE_URL="your_railway_url"
python3 scripts/import_csv_bulk.py \
  --parentheticals search_parenthetical-2025-10-31.csv \
  --limit 100000 \
  --batch-size 10000
```

**Expected result**: ~50K-100K parentheticals with valid opinion references

---

## 📋 Phase 3: Treatment Detection Engine (1.5 hours)

### Task 3.1: Create Treatment Classifier
**File**: `backend/app/services/treatment_classifier.py`

**Keyword Dictionaries**:
```python
NEGATIVE_KEYWORDS = {
    'overruled': 10,      # Strongest negative
    'overruling': 10,
    'reversed': 9,
    'vacated': 9,
    'abrogated': 10,
    'superseded': 9,
    'disapproved': 8,
    'questioned': 6,
    'criticized': 5,
    'limited': 4,
}

POSITIVE_KEYWORDS = {
    'affirmed': 8,
    'followed': 7,
    'adopted': 7,
    'approved': 6,
    'applied': 5,
    'cited with approval': 8,
}

NEUTRAL_KEYWORDS = {
    'distinguished': 5,
    'explained': 3,
    'discussed': 2,
    'cited': 1,
    'mentioned': 1,
}
```

**Functions**:
- [ ] `classify_parenthetical(text: str) -> TreatmentResult`
- [ ] `analyze_opinion_treatment(opinion_id: int) -> TreatmentSummary`
- [ ] `calculate_treatment_score(parentheticals: List) -> float`

### Task 3.2: Create Treatment Analyzer Service
**File**: `backend/app/services/treatment_analyzer.py`
- [ ] Aggregate parentheticals for an opinion
- [ ] Score and classify each parenthetical
- [ ] Calculate overall treatment status
- [ ] Cache results in citation_treatment table
- [ ] Return treatment summary with examples

**Output Structure**:
```python
{
    "opinion_id": 123,
    "treatment_status": "QUESTIONED",
    "severity": "NEGATIVE",
    "confidence": 0.75,
    "summary": {
        "negative": 3,
        "positive": 15,
        "neutral": 42
    },
    "significant_treatments": [
        {
            "type": "QUESTIONED",
            "describing_opinion_id": 456,
            "case_name": "Smith v. Jones",
            "date": "2023-05-10",
            "excerpt": "...questioned the validity of..."
        }
    ]
}
```

---

## 📋 Phase 4: Backend API Endpoints (45 mins)

### Task 4.1: Treatment API Routes
**File**: `backend/app/api/v1/treatment.py` (new file)

**Endpoints**:
```python
GET /api/v1/treatment/{opinion_id}
# Returns treatment summary for an opinion

GET /api/v1/treatment/{opinion_id}/history
# Returns chronological treatment history

POST /api/v1/treatment/analyze/{opinion_id}
# Triggers fresh analysis (admin only)

GET /api/v1/treatment/batch
# Batch lookup for multiple opinions
```

### Task 4.2: Enhance Citation Endpoints
**File**: `backend/app/api/v1/citations.py`
- [ ] Add treatment data to citation network responses
- [ ] Include treatment badges in node data
- [ ] Filter by treatment type

### Task 4.3: Register Routes
**File**: `backend/app/api/v1/router.py`
- [ ] Import treatment router
- [ ] Add to api_router with prefix="/treatment"

---

## 📋 Phase 5: Frontend UI Components (2 hours)

### Task 5.1: Treatment Badge Component
**File**: `frontend/src/components/TreatmentBadge.tsx`

**Design**:
```tsx
<TreatmentBadge treatment="OVERRULED" count={3} />
// Renders: 🔴 Overruled (3)

<TreatmentBadge treatment="AFFIRMED" count={15} />
// Renders: 🟢 Affirmed (15)

<TreatmentBadge treatment="QUESTIONED" count={2} />
// Renders: 🟡 Questioned (2)
```

**Props**:
- treatment: TreatmentType
- count: number
- showIcon?: boolean
- size?: 'sm' | 'md' | 'lg'
- onClick?: () => void

### Task 5.2: Treatment Summary Panel
**File**: `frontend/src/components/TreatmentSummary.tsx`

**Features**:
- [ ] Overall treatment status indicator
- [ ] Breakdown by treatment type
- [ ] Timeline of significant treatments
- [ ] Links to treating cases
- [ ] Confidence indicator

### Task 5.3: Update Case Detail Page
**File**: `frontend/src/pages/CaseDetailPage.tsx`
- [ ] Fetch treatment data
- [ ] Display prominent treatment status at top
- [ ] Show "⚠️ This case has been questioned" alert
- [ ] List significant treatments
- [ ] Link to full treatment history

### Task 5.4: Update Citation Network
**File**: `frontend/src/pages/CitationNetworkPage.tsx`
- [ ] Add treatment badges to nodes
- [ ] Color-code edges by treatment type
- [ ] Add legend for treatment colors
- [ ] Filter by treatment type

### Task 5.5: Treatment History Page (New)
**File**: `frontend/src/pages/TreatmentHistoryPage.tsx`
- [ ] Timeline view of treatments
- [ ] Grouped by treatment type
- [ ] Sortable and filterable
- [ ] Export functionality

---

## 📋 Phase 6: API Types & Integration (30 mins)

### Task 6.1: Update API Types
**File**: `frontend/src/lib/api.ts`

```typescript
export interface TreatmentSummary {
  opinion_id: number
  treatment_status: TreatmentType
  severity: Severity
  confidence: number
  summary: {
    negative: number
    positive: number
    neutral: number
  }
  significant_treatments: SignificantTreatment[]
}

export type TreatmentType = 
  | 'OVERRULED' | 'REVERSED' | 'AFFIRMED' 
  | 'DISTINGUISHED' | 'QUESTIONED' | 'CITED'

export type Severity = 'NEGATIVE' | 'POSITIVE' | 'NEUTRAL' | 'UNKNOWN'
```

### Task 6.2: Treatment API Client
```typescript
export const treatmentAPI = {
  getTreatment: (opinionId: number) => Promise<TreatmentSummary>
  getHistory: (opinionId: number) => Promise<TreatmentHistory>
  analyzeBatch: (opinionIds: number[]) => Promise<TreatmentSummary[]>
}
```

---

## 📋 Phase 7: Batch Processing & Caching (1 hour)

### Task 7.1: Background Treatment Analyzer
**File**: `backend/app/services/treatment_processor.py`
- [ ] Batch analyze all opinions with citations
- [ ] Store results in citation_treatment table
- [ ] Schedule periodic updates
- [ ] Progress tracking

### Task 7.2: Run Initial Analysis
**Script**: `scripts/analyze_treatments.py`
```python
# Analyze all opinions with parentheticals
# Cache results for fast API responses
```

### Task 7.3: API Caching Strategy
- [ ] Cache treatment summaries for 24 hours
- [ ] Invalidate on new parentheticals
- [ ] Use PostgreSQL materialized view for fast lookups

---

## 📋 Phase 8: Testing & Validation (1 hour)

### Task 8.1: Backend Tests
- [ ] Test treatment classifier accuracy
- [ ] Test API endpoints
- [ ] Validate treatment scores
- [ ] Edge cases (no parentheticals, conflicting signals)

### Task 8.2: Frontend Tests
- [ ] Treatment badge rendering
- [ ] Treatment summary display
- [ ] Citation network integration
- [ ] Responsive design

### Task 8.3: Integration Testing
- [ ] End-to-end treatment flow
- [ ] Performance with large datasets
- [ ] Caching effectiveness

---

## 📋 Phase 9: Deployment & Documentation (30 mins)

### Task 9.1: Deploy Backend
```bash
cd backend
git add .
git commit -m "Add citation treatment detection system"
git push
```

### Task 9.2: Deploy Frontend
```bash
cd frontend
git add .
git commit -m "Add treatment UI components"
git push
```

### Task 9.3: Update Documentation
- [ ] Add treatment detection to README
- [ ] API documentation
- [ ] User guide for interpreting treatments
- [ ] Known limitations

---

## 📊 Success Metrics

### Minimum Viable Product (MVP)
- ✅ Import 100K+ parentheticals
- ✅ Detect 5 treatment types (overruled, reversed, affirmed, distinguished, cited)
- ✅ Display treatment badges on case detail pages
- ✅ Show treatment in citation network
- ✅ API response time < 200ms

### Full Feature Set
- ✅ All parentheticals imported (1.2GB file)
- ✅ 10+ treatment types detected
- ✅ Confidence scoring
- ✅ Treatment timeline visualization
- ✅ Email alerts for treatment changes
- ✅ Treatment comparison across jurisdictions

---

## 🗓️ Timeline Estimate

| Phase | Time | Dependencies |
|-------|------|--------------|
| 1. Database Schema | 30 min | - |
| 2. Data Import | 1 hour | Phase 1 |
| 3. Detection Engine | 1.5 hours | Phase 2 |
| 4. Backend API | 45 min | Phase 3 |
| 5. Frontend UI | 2 hours | Phase 4 |
| 6. API Integration | 30 min | Phase 4, 5 |
| 7. Batch Processing | 1 hour | Phase 3 |
| 8. Testing | 1 hour | All phases |
| 9. Deployment | 30 min | Phase 8 |
| **Total** | **~9 hours** | |

**MVP in ~4 hours**: Phases 1-4 + basic UI

---

## 🚀 Getting Started

### Step 1: Create Database Models
```bash
# Start with Phase 1, Task 1.1
code backend/app/models/parenthetical.py
```

### Step 2: Import Sample Data
```bash
# Run Phase 2 import
python3 scripts/import_csv_bulk.py --parentheticals search_parenthetical-2025-10-31.csv --limit 100000
```

### Step 3: Build Classifier
```bash
# Create treatment detection logic
code backend/app/services/treatment_classifier.py
```

Ready to start? Let me know which phase you'd like to begin with!
