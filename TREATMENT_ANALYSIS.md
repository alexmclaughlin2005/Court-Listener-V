# Citation Treatment Analysis

## Overview

The Citation Treatment Analysis system automatically detects and classifies how cases have been treated by later courts using keyword analysis of parentheticals. This helps researchers and legal professionals quickly understand a case's current legal status.

## Features

### Treatment Types

The system detects the following treatment classifications:

**Negative Treatments:**
- `OVERRULED` - Case has been explicitly overruled
- `REVERSED` - Decision reversed on appeal
- `VACATED` - Decision vacated by higher court
- `ABROGATED` - Holding no longer valid
- `SUPERSEDED` - Replaced by newer authority
- `QUESTIONED` - Validity questioned by later courts
- `CRITICIZED` - Reasoning or holding criticized

**Positive Treatments:**
- `AFFIRMED` - Decision affirmed on appeal
- `FOLLOWED` - Applied/followed by later courts

**Neutral Treatments:**
- `DISTINGUISHED` - Factually distinguished
- `CITED` - Referenced without strong treatment signal

### Severity Levels

- `NEGATIVE` - Case has negative treatment (overruled, reversed, questioned, etc.)
- `POSITIVE` - Case has positive treatment (affirmed, followed, etc.)
- `NEUTRAL` - Case cited without strong positive or negative treatment
- `UNKNOWN` - No parentheticals available to analyze

### Evidence-Based Classification

Each treatment includes evidence showing WHY the classification was assigned:

- **Summary** - Text explanation of the classification
- **Negative Examples** - Top 5 parentheticals with negative keywords
- **Positive Examples** - Top 5 parentheticals with positive keywords
- **Keywords** - Specific legal terms detected (e.g., "overruling", "affirmed")
- **Citing Opinions** - Which cases contain each parenthetical
- **Scores** - Numerical scores for transparency

#### Example Evidence Structure:

```json
{
  "summary": "OVERRULED based on 2 negative, 2 positive, 14 neutral parentheticals",
  "negative_examples": [
    {
      "text": "courts have no business overruling him because their interpretation differs",
      "keywords": ["overruling"],
      "score": 10,
      "describing_opinion_id": 1372132
    }
  ],
  "positive_examples": [...],
  "total_negative_score": 14,
  "total_positive_score": 16
}
```

## API Endpoints

### Get Treatment Analysis

```
GET /api/v1/treatment/{opinion_id}
```

Returns treatment analysis for a specific opinion.

**Parameters:**
- `opinion_id` (path) - Opinion ID to analyze
- `use_cache` (query, optional) - Use cached results if available (default: true)

**Response:**
```json
{
  "opinion_id": 358034,
  "treatment_type": "OVERRULED",
  "severity": "NEGATIVE",
  "confidence": 0.80,
  "summary": {
    "negative": 2,
    "positive": 2,
    "neutral": 14,
    "total": 18
  },
  "evidence": {
    "summary": "OVERRULED based on 2 negative, 2 positive, 14 neutral parentheticals",
    "negative_examples": [...],
    "positive_examples": [...],
    "total_negative_score": 14,
    "total_positive_score": 16
  },
  "significant_treatments": [...],
  "from_cache": true,
  "last_updated": "2025-11-17T21:34:23.591Z"
}
```

### Get Treatment History

```
GET /api/v1/treatment/{opinion_id}/history
```

Returns chronological treatment history showing all parentheticals over time.

**Parameters:**
- `opinion_id` (path) - Opinion ID
- `limit` (query, optional) - Maximum results (default: 50, max: 200)

**Response:**
```json
{
  "opinion_id": 358034,
  "total_treatments": 18,
  "history": [
    {
      "parenthetical_id": 12345,
      "treatment_type": "OVERRULED",
      "severity": "NEGATIVE",
      "confidence": 0.95,
      "text": "overruling Smith on statute of limitations issue",
      "describing_opinion_id": 1372132,
      "describing_case_name": "Jones v. State",
      "date_filed": "2023-05-15",
      "keywords": ["overruling"]
    }
  ]
}
```

### Force Re-Analysis

```
POST /api/v1/treatment/analyze/{opinion_id}
```

Forces fresh analysis, bypassing cache. Use when new parentheticals are added.

### Batch Analysis

```
POST /api/v1/treatment/batch
```

Analyze multiple opinions at once.

**Request Body:**
```json
{
  "opinion_ids": [358034, 123456, 789012]
}
```

**Parameters:**
- `use_cache` (query, optional) - Use cached results if available (default: true)

**Response:**
```json
{
  "total": 3,
  "results": [
    { /* treatment result 1 */ },
    { /* treatment result 2 */ },
    { /* treatment result 3 */ }
  ]
}
```

### Treatment Statistics

```
GET /api/v1/treatment/stats/summary
```

Returns overall statistics about treatments in the database.

**Response:**
```json
{
  "total_analyzed": 11562,
  "total_parentheticals": 6234567,
  "by_severity": {
    "negative": 1114,
    "positive": 1235,
    "neutral": 9213
  }
}
```

## How It Works

### Classification Algorithm

1. **Negation Detection**: First detects negation patterns that reverse keyword meanings (e.g., "declined to follow" vs "followed")
2. **Keyword Detection**: Scans parenthetical text for legal treatment keywords, skipping positions covered by negations
3. **Context Analysis**: Examines ±50 characters around keywords to detect modifiers that intensify or weaken signals
4. **Score Calculation**: Weights keywords by severity (overruled=10, affirmed=8, cited=1) and applies context modifiers
5. **Aggregation**: Combines scores across all parentheticals mentioning the case
6. **Classification**: Determines overall treatment based on dominant signals
7. **Confidence**: Calculates confidence score based on signal strength and count
8. **Evidence Collection**: Gathers top examples with keywords and citing opinions

### Enhanced Features (Nov 2025)

#### Negation Pattern Detection
The classifier now detects negative keyword combinations that reverse meaning:

- **"declined to follow"** → Negative (not positive for "follow")
- **"refused to adopt"** → Negative (not positive for "adopt")
- **"no longer followed"** → Strong negative
- **"not followed"** → Negative
- **"distinguished and rejected"** → Complex negative

This prevents false positives where a positive keyword appears in a negated context.

#### Context Window Analysis
The classifier examines 50 characters before and after keywords to detect modifiers:

**Intensifiers (increase score by 20-40%):**
- "expressly", "explicitly" → 1.3x multiplier
- "unequivocally", "categorically" → 1.4x multiplier
- "clearly", "firmly", "strongly" → 1.2x multiplier

**Weakeners (decrease score by 20-40%):**
- "arguably", "possibly" → 0.6-0.7x multiplier
- "might", "could", "seems" → 0.6-0.7x multiplier
- "implicitly", "appears" → 0.7-0.8x multiplier

Examples:
- "expressly overruled" → stronger signal than just "overruled" (13 vs 10 points)
- "arguably questioned" → weaker signal than just "questioned" (4 vs 6 points)

### Keyword Weights

**Negative Keywords (High → Low):**
- `overruled`, `abrogated` (score: 10)
- `reversed`, `vacated`, `superseded` (score: 9)
- `disapproved` (score: 8)
- `rejected` (score: 7)
- `questioned`, `doubted` (score: 6)
- `criticized` (score: 5)
- `limited`, `narrowed` (score: 4)

**Positive Keywords:**
- `affirmed` (score: 8)
- `followed`, `adopted` (score: 7)
- `approved`, `endorsed` (score: 6)
- `applied`, `agreed` (score: 5)

**Neutral Keywords:**
- `distinguished` (score: 5)
- `explained` (score: 3)
- `discussed` (score: 2)
- `cited`, `mentioned`, `referenced` (score: 1)

### Classification Rules

1. **Negative takes priority**: Any negative signal marks case as negative
2. **Positive vs Neutral**: If positive score > neutral score, mark as positive
3. **Default**: Otherwise mark as neutral (cited)
4. **Confidence**: Increases with number of supporting signals

## Database Schema

### citation_treatment Table

```sql
CREATE TABLE citation_treatment (
    opinion_id INTEGER PRIMARY KEY REFERENCES search_opinion(id),
    treatment_type VARCHAR(20) NOT NULL,  -- Enum: OVERRULED, AFFIRMED, etc.
    severity VARCHAR(20) NOT NULL,        -- Enum: NEGATIVE, POSITIVE, NEUTRAL
    confidence FLOAT NOT NULL,            -- 0.0 to 1.0
    negative_count INTEGER DEFAULT 0,
    positive_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,
    evidence JSONB,                       -- Evidence with examples and keywords
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_treatment_severity ON citation_treatment(severity);
CREATE INDEX idx_treatment_type ON citation_treatment(treatment_type);
```

## Bulk Processing

### analyze_treatments_bulk_optimized.py

Script for analyzing treatments in bulk directly from the database (no API calls).

**Features:**
- Processes millions of parentheticals efficiently
- Batch processing (default: 1000 opinions at a time)
- Progress tracking with statistics
- Evidence capture with keywords and examples
- UPSERT support (idempotent)

**Usage:**

```bash
# Analyze first 10,000 opinions
export DATABASE_URL="postgresql://..."
python3 scripts/analyze_treatments_bulk_optimized.py --limit 10000 --batch-size 5000

# Show statistics only
python3 scripts/analyze_treatments_bulk_optimized.py --stats-only

# Re-analyze opinions that lack evidence
python3 scripts/analyze_treatments_bulk_optimized.py --force-reanalyze --batch-size 5000

# Process with offset (for parallel processing)
python3 scripts/analyze_treatments_bulk_optimized.py --limit 10000 --offset 10000
```

**Output:**
```
2025-11-17 16:33:47 - INFO - Current Statistics:
  Total opinions with parentheticals: 1,153,435
  Already analyzed: 11,562
  Remaining to analyze: 1,141,873
  By severity: {'NEGATIVE': 993, 'POSITIVE': 1138, 'NEUTRAL': 9431}

2025-11-17 16:34:01 - INFO - Progress: 5,000/11,562 (43.2%) | Analyzed: 5,000
2025-11-17 16:34:13 - INFO - Progress: 10,000/11,562 (86.5%) | Analyzed: 10,000
2025-11-17 16:34:20 - INFO - Progress: 11,562/11,562 (100.0%) | Analyzed: 11,562

2025-11-17 16:34:23 - INFO - Final Statistics:
  Newly analyzed: 11,562
  Total cached: 11,562
  Remaining: 1,141,873
```

### Performance

- **Speed**: ~3,000-5,000 opinions per minute
- **Memory**: ~500MB for 10K batch
- **Database**: Uses batch inserts and UPSERT for efficiency

## On-Demand Analysis

The API automatically analyzes opinions on-demand when accessed:

1. Check if treatment is cached
2. If cached, return immediately with evidence
3. If not cached:
   - Fetch parentheticals from database
   - Run treatment classification
   - Collect evidence (keywords, examples, citing opinions)
   - Cache result with evidence
   - Return analysis

This ensures treatments are always available when viewing cases in the UI, even if they haven't been pre-computed.

## Implementation Files

### Backend

- **[treatment.py](backend/app/api/v1/treatment.py)** - API endpoints
- **[treatment_classifier.py](backend/app/services/treatment_classifier.py)** - Core classification logic
- **[citation_treatment.py](backend/app/models/citation_treatment.py)** - Database model

### Scripts

- **[analyze_treatments_bulk_optimized.py](scripts/analyze_treatments_bulk_optimized.py)** - Bulk processing with evidence
- **[analyze_treatments_bulk.py](scripts/analyze_treatments_bulk.py)** - Legacy API-based bulk processing

## Use Cases

### Legal Research
- Quickly determine if a case is still good law
- Identify when and how a case was overruled
- Track treatment changes over time

### Citation Analysis
- Find cases with negative treatment to avoid relying on overruled precedent
- Identify most strongly affirmed cases
- Discover cases that questioned or criticized a holding

### Case Law Monitoring
- Monitor treatment of important cases
- Alert when cases receive negative treatment
- Track citation patterns over time

## Future Enhancements

### Planned Features
- [ ] Natural language explanations of treatment
- [ ] Treatment timeline visualization
- [ ] Treatment alert system
- [ ] ML-based classification for improved accuracy
- [ ] Jurisdiction-specific treatment rules
- [ ] Treatment impact scoring (weighted by citing court authority)

### Optimization Opportunities
- [ ] Incremental analysis (only analyze new parentheticals)
- [ ] Parallel processing for bulk analysis
- [ ] Caching layer (Redis) for frequently accessed treatments
- [ ] Background job queue for automatic re-analysis

## Accuracy and Limitations

### Strengths
- Evidence-based with transparent reasoning
- Covers all major treatment types
- Scales to millions of parentheticals
- Real-time and batch processing support

### Limitations
- Keyword-based (may miss subtle treatment signals)
- Requires parentheticals (won't work without them)
- English language only
- May misclassify edge cases with ambiguous language

### Best Practices
- Always review evidence when making legal decisions
- Consider context beyond keyword matching
- Verify treatment with primary sources
- Use confidence scores to gauge reliability

## Statistics

**Current Database (as of Nov 17, 2025):**
- Total opinions with parentheticals: 1,153,435
- Analyzed treatments: 11,562
- Negative treatments: 1,114 (9.6%)
- Positive treatments: 1,235 (10.7%)
- Neutral treatments: 9,213 (79.7%)
- Total parentheticals: 6,234,567

**Processing Performance:**
- Bulk analysis speed: ~290 opinions/second
- Average parentheticals per opinion: 5.4
- Re-analysis with evidence: ~40 seconds for 11,562 opinions

---

**Last Updated**: November 17, 2025
