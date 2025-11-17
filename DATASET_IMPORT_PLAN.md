# CourtListener Dataset Import Strategy

## Overview

This document outlines the strategy for importing the complete CourtListener dataset into our PostgreSQL database on Railway.

## Current Status

**Sample Data (Currently Loaded)**:
- 5 courts
- 20 dockets
- 20 opinion clusters
- 25 opinions
- 28 citation relationships

**Database**: PostgreSQL on Railway with 500MB storage

## CourtListener Dataset Information

### Available Data Sources

1. **CourtListener Bulk Data API**: https://www.courtlistener.com/api/bulk-data/
2. **Direct Download**: Compressed CSV/JSON files
3. **Size Estimates**:
   - Courts: ~400 courts (small dataset)
   - Dockets: ~10M+ records (large)
   - Opinion Clusters: ~10M+ records (large)
   - Opinions: ~12M+ records (very large)
   - Citations: ~50M+ relationships (very large)

### Recommended Approach

Given Railway's 500MB database limit and the massive size of the full dataset, we need a **selective import strategy**.

## Import Strategy Options

### Option 1: Court-Filtered Import (Recommended)

Import only cases from specific high-value courts:

**Target Courts**:
- Supreme Court of the United States (SCOTUS)
- Circuit Courts of Appeals (13 circuits)
- Selected District Courts (high-volume)

**Expected Data Size**:
- SCOTUS: ~35,000 opinions
- Circuit Courts: ~500,000 opinions
- Selected Districts: ~1-2M opinions

**Pros**:
- Fits within database limits
- High-quality, precedential cases
- Most valuable for legal research

**Cons**:
- Missing lower court data
- Less comprehensive coverage

### Option 2: Date-Filtered Import

Import only recent cases (e.g., last 10-20 years):

**Target Range**: 2005-present

**Expected Data**:
- ~3-5M opinions
- More manageable dataset size

**Pros**:
- More recent, relevant cases
- Better citation network (recent cases cite each other)

**Cons**:
- Missing historical precedent
- May still exceed storage limits

### Option 3: Hybrid Approach (Best Option)

Combine both filters:
- **All SCOTUS cases** (complete historical record)
- **Circuit Courts from 2000-present**
- **Selected high-profile District Courts from 2010-present**

**Expected Size**: ~1-2M opinions (manageable)

**Pros**:
- Balanced coverage
- Historical SCOTUS precedent
- Recent lower court decisions
- Fits within storage limits

**Cons**:
- Requires more complex filtering logic

## Implementation Plan

### Phase 1: Data Acquisition

```bash
# Download CourtListener bulk data
# Option 1: Use their API
curl -H "Authorization: Token YOUR_API_KEY" \
  https://www.courtlistener.com/api/bulk-data/opinions/ \
  -o opinions.tar.gz

# Option 2: Direct download from their archive
wget https://com-courtlistener-storage.s3-us-west-2.amazonaws.com/bulk-data/opinions-YYYY-MM-DD.tar.gz
```

### Phase 2: Data Filtering & Processing

Create Python scripts to:

1. **Extract & Filter Courts**:
```python
# backend/scripts/filter_courts.py
import pandas as pd

PRIORITY_COURTS = [
    'scotus',      # Supreme Court
    'ca1', 'ca2', 'ca3', 'ca4', 'ca5', 'ca6',
    'ca7', 'ca8', 'ca9', 'ca10', 'ca11', 'cadc', 'cafc',  # Circuit Courts
    'nyd', 'cad', 'ilnd', 'txsd',  # High-volume district courts
]

def filter_courts(courts_csv):
    df = pd.read_csv(courts_csv)
    filtered = df[df['id'].isin(PRIORITY_COURTS)]
    return filtered
```

2. **Filter by Date**:
```python
def filter_by_date(opinions_csv, start_date='2000-01-01'):
    df = pd.read_csv(opinions_csv)
    df['date_filed'] = pd.to_datetime(df['date_filed'])
    filtered = df[df['date_filed'] >= start_date]
    return filtered
```

3. **Batch Import with Progress Tracking**:
```python
# Import in chunks to avoid memory issues
def import_in_batches(data, batch_size=1000):
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        import_batch(batch)
        log_progress(i, len(data))
```

### Phase 3: Database Import

```bash
# Step 1: Clear existing sample data
curl -X DELETE "https://court-listener-v-production.up.railway.app/api/v1/import/clear?confirm=true"

# Step 2: Import filtered courts
railway run python scripts/import_filtered_data.py \
  --courts data/filtered_courts.csv \
  --date-from 2000-01-01 \
  --max-opinions 1000000

# Step 3: Verify import
curl "https://court-listener-v-production.up.railway.app/api/v1/import/status"
```

### Phase 4: Monitoring & Optimization

1. **Monitor Database Size**:
```sql
SELECT pg_size_pretty(pg_database_size('railway'));
```

2. **Add Indexes for Performance**:
```sql
CREATE INDEX idx_opinions_date ON search_opinion(date_created);
CREATE INDEX idx_clusters_citation_count ON search_opinioncluster(citation_count);
CREATE INDEX idx_citations_citing ON search_opinionscited(citing_opinion_id);
CREATE INDEX idx_citations_cited ON search_opinionscited(cited_opinion_id);
```

3. **Monitor Query Performance**:
```python
# Add timing to API endpoints
import time

@router.get("/cases")
async def search_cases(...):
    start = time.time()
    # ... query logic
    duration = time.time() - start
    logger.info(f"Search took {duration:.2f}s")
```

## Database Storage Estimates

### Table Sizes (Estimated)

| Table | Rows | Size per Row | Total Size |
|-------|------|--------------|------------|
| Courts | ~20 | 1 KB | 20 KB |
| Dockets | ~500K | 500 B | 250 MB |
| Opinion Clusters | ~500K | 800 B | 400 MB |
| Opinions | ~600K | 2 KB | 1.2 GB |
| Citations | ~2M | 50 B | 100 MB |

**Total Estimated**: ~2 GB (exceeds Railway limit)

### Optimizations to Reduce Size

1. **Exclude Opinion Text**: Store only metadata, link to CourtListener for full text
   - Saves ~1.5 KB per opinion
   - Reduces Opinions table from 1.2 GB to 300 MB

2. **Limit Citation Depth**: Import only direct citations (depth=1)
   - Reduces Citations table by 60%
   - Still provides valuable network data

3. **Compress Text Fields**: Use PostgreSQL TEXT compression
   - Automatic compression for large text fields

### Revised Estimate with Optimizations

| Table | Rows | Optimized Size |
|-------|------|----------------|
| Courts | 20 | 20 KB |
| Dockets | 500K | 250 MB |
| Opinion Clusters | 500K | 400 MB |
| Opinions (no text) | 600K | 300 MB |
| Citations (depth=1) | 800K | 40 MB |

**Total**: ~990 MB (still exceeds 500 MB limit)

## Final Recommendation

### Pragmatic Approach for 500MB Database

**Import Strategy**:
1. **SCOTUS Complete**: All Supreme Court cases (~35K opinions)
2. **Circuit Courts**: Last 10 years only (~100K opinions)
3. **No full opinion text**: Store only excerpts (first 500 chars)
4. **Citation network**: Direct citations only (depth=1)

**Expected Size**: ~450 MB (fits within limit with buffer)

**Implementation**:

```python
# backend/scripts/import_filtered.py

IMPORT_CONFIG = {
    'courts': ['scotus', 'ca1', 'ca2', 'ca3', 'ca4', 'ca5', 'ca6',
               'ca7', 'ca8', 'ca9', 'ca10', 'ca11', 'cadc', 'cafc'],
    'date_filters': {
        'scotus': None,  # Import all
        'circuit': '2015-01-01',  # Last 10 years
    },
    'opinion_text': {
        'max_length': 500,  # Store only excerpt
        'full_text_url': 'https://www.courtlistener.com/opinion/{id}/'
    },
    'citations': {
        'max_depth': 1  # Direct citations only
    }
}
```

## Execution Checklist

- [ ] Download CourtListener bulk data
- [ ] Create filtering scripts
- [ ] Test import with small subset (1000 cases)
- [ ] Monitor database size during import
- [ ] Verify citation network integrity
- [ ] Test API performance with real data
- [ ] Add database indexes
- [ ] Update frontend to handle larger datasets
- [ ] Document data sources and filters used

## Future Scaling Options

If we need more data:

1. **Upgrade Railway Plan**: Move to Pro plan with larger database
2. **External Storage**: Store full opinion text in S3/storage service
3. **Database Sharding**: Split by court or time period
4. **Caching Layer**: Add Redis for frequently accessed data
5. **Alternative**: Use CourtListener API directly for some queries

## Timeline Estimate

- **Phase 1** (Data Acquisition): 2-4 hours
- **Phase 2** (Filtering): 4-6 hours
- **Phase 3** (Import): 6-12 hours (depending on data size)
- **Phase 4** (Optimization): 2-4 hours

**Total**: 14-26 hours of work

---

## Next Steps

1. Get CourtListener API key
2. Download and explore bulk data structure
3. Create filtering scripts
4. Run test import with 1000 cases
5. Monitor and optimize
6. Execute full filtered import
