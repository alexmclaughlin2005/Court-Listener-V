# CourtListener Data Import Guide

## Current CSV Files

You have:
- `people_db_court-2025-10-31.csv` (746K) - 3,378 courts
- `search_docket-2025-10-31.csv` (26GB) - 70M dockets
- `search_docket-sample.csv` (1.9M) - 5,000 sample dockets
- `search_opinioncluster-2025-10-31.csv` (11GB) - 74M clusters
- `search_opinionscited-2025-10-31.csv` (2.5GB) - 75M citations

## Missing Files

According to the CourtListener schema, you're missing:
- `search_opinion` - Individual opinion documents with text
  - This is critical because `search_opinionscited` references `opinion_id`
  - Without this, citations won't link properly

## Import Strategy

### Phase 1: Core Data (Start Here)

Import foundation tables first:

```bash
# 1. Import courts (fast - only 3K records)
railway run python backend/scripts/import_railway.py \
  --courts people_db_court-2025-10-31.csv

# 2. Import dockets sample for testing (5K records)
railway run python backend/scripts/import_railway.py \
  --dockets search_docket-sample.csv

# 3. Import matching clusters (test with limit first)
railway run python backend/scripts/import_railway.py \
  --clusters search_opinioncluster-2025-10-31.csv \
  --limit 10000

# 4. Check status
curl "https://court-listener-v-production.up.railway.app/api/v1/import/status"
```

### Phase 2: Scale Up (After Testing)

Once Phase 1 works, import larger datasets:

```bash
# Import first 100K dockets
railway run python backend/scripts/import_railway.py \
  --dockets search_docket-2025-10-31.csv \
  --limit 100000

# Import first 100K clusters
railway run python backend/scripts/import_railway.py \
  --clusters search_opinioncluster-2025-10-31.csv \
  --limit 100000
```

### Phase 3: Full Import (Production)

⚠️ **Warning**: This will take hours/days and use significant database storage

```bash
# Import all dockets (70M records - will take 12+ hours)
railway run python backend/scripts/import_railway.py \
  --dockets search_docket-2025-10-31.csv \
  --batch-size 10000

# Import all clusters (74M records - will take 12+ hours)
railway run python backend/scripts/import_railway.py \
  --clusters search_opinioncluster-2025-10-31.csv \
  --batch-size 10000

# Import citations (75M records - will take 8+ hours)
# NOTE: This will fail if opinions table is empty
railway run python backend/scripts/import_railway.py \
  --citations search_opinionscited-2025-10-31.csv \
  --batch-size 10000
```

## Database Storage Estimates

| Import Level | Dockets | Clusters | Total DB Size |
|-------------|---------|----------|---------------|
| Test (10K) | 10K | 10K | ~50 MB |
| Small (100K) | 100K | 100K | ~500 MB |
| Medium (1M) | 1M | 1M | ~5 GB |
| Large (10M) | 10M | 10M | ~50 GB |
| Full (70M+) | 70M | 74M | ~300-400 GB |

## Recommended Approach

### Option 1: Filtered Import (Recommended)

Import only high-value courts to stay within reasonable database size:

```bash
# After importing courts and dockets, filter clusters by court
# Edit the script to add WHERE clause filtering by court_id
# Focus on: SCOTUS, Circuit Courts, major District Courts
```

### Option 2: Time-Based Import

Import only recent cases:

```bash
# Modify script to filter by date_filed >= '2015-01-01'
# This reduces dataset to ~10-15M cases
```

### Option 3: Incremental Import with Monitoring

Start small and monitor database size:

```bash
# Import 100K at a time
# Check database size after each batch
# Stop when approaching storage limits
```

## Getting Missing Files

To get the `search_opinion` CSV:

1. Visit: https://www.courtlistener.com/api/bulk-data/
2. Download: `search_opinion-YYYY-MM-DD.csv.bz2`
3. Extract: `bunzip2 search_opinion-YYYY-MM-DD.csv.bz2`
4. Upload to project directory

## Monitoring Commands

### Check Import Status
```bash
curl "https://court-listener-v-production.up.railway.app/api/v1/import/status"
```

### Check Database Size on Railway
```sql
SELECT pg_size_pretty(pg_database_size('railway'));
```

### Monitor Import Progress (if running locally)
```bash
# In another terminal, watch the log output
railway logs --follow
```

## Performance Optimization

### Add Indexes After Import

Once import is complete, add these indexes for better query performance:

```sql
-- Docket indexes
CREATE INDEX idx_docket_court ON search_docket(court_id);
CREATE INDEX idx_docket_date ON search_docket(date_filed);

-- Cluster indexes
CREATE INDEX idx_cluster_docket ON search_opinioncluster(docket_id);
CREATE INDEX idx_cluster_date ON search_opinioncluster(date_filed);
CREATE INDEX idx_cluster_citations ON search_opinioncluster(citation_count);

-- Citation indexes (critical for network queries)
CREATE INDEX idx_citations_citing ON search_opinionscited(citing_opinion_id);
CREATE INDEX idx_citations_cited ON search_opinionscited(cited_opinion_id);
```

## Troubleshooting

### Import Fails with "Out of Memory"
- Reduce `--batch-size` from 5000 to 1000
- Use `--limit` to import in smaller chunks

### Foreign Key Violations
- Ensure courts are imported before dockets
- Ensure dockets are imported before clusters
- Check that CSV files have matching IDs

### Citations Import Fails
- You need `search_opinion` table populated first
- Citations reference `opinion_id`, not `cluster_id`
- Skip citations for now, import them after getting opinions file

### Database Full
- Upgrade Railway database plan
- Or use selective import (filter by court/date)
- Or use Railway volumes for extended storage

## Next Steps

1. **Start with Phase 1** - Test import with small dataset
2. **Verify data** - Check that searches work on frontend
3. **Monitor storage** - Watch database size carefully
4. **Scale gradually** - Increase limits step by step
5. **Get opinions file** - Download from CourtListener
6. **Import citations** - After opinions are loaded

## Import Time Estimates

Assuming 5000 records/second (optimistic):

- Courts (3K): 1 second
- Dockets (70M): 4 hours
- Clusters (74M): 4 hours
- Citations (75M): 4 hours

**Total: ~12-16 hours for full import**

Real-world is likely 2-3x slower, so expect **24-48 hours** for complete import.

## Alternative: Use CourtListener API

Instead of importing everything, consider using their API:
- Free tier: 5,000 requests/hour
- Paid tier: Unlimited
- Benefits: No storage costs, always up-to-date
- Drawbacks: Slower queries, API limits

Our current setup can hybrid:
- Import frequently-accessed data (SCOTUS, recent cases)
- Use API for rare queries (old district court cases)
