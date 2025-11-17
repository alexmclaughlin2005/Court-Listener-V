# Opinion Text Import Guide

## Overview

This guide explains how to import opinion text data into your CourtListener database. Opinion text is the actual content of legal opinions (court decisions) that users can read on your platform.

## Current Status

**What you have:**
- ✅ Courts, Dockets, Opinion Clusters (case metadata)
- ✅ Citations and Parentheticals (relationships)
- ❌ Opinion text (plain_text and html fields are null)

**What you need:**
- The `search_opinion` CSV file from CourtListener with actual opinion text

---

## Step 1: Get the Opinions CSV File

### Option A: Download from CourtListener Bulk Data

1. Visit: https://www.courtlistener.com/api/bulk-data/
2. Look for `search_opinion-YYYY-MM-DD.csv.bz2`
3. Download the file (Warning: Very large - 10GB+ compressed, 50GB+ uncompressed)

```bash
# Download
wget https://com-courtlistener-storage.s3-us-west-2.amazonaws.com/bulk-data/opinions-2025-10-31.tar.gz

# Extract
tar -xzvf opinions-2025-10-31.tar.gz
```

### Option B: Use CourtListener API (Smaller Sample)

If you don't want the full dataset, you can get a subset via their API:

```bash
# Get API key from CourtListener
# Then fetch specific opinions you need
```

---

## Step 2: Prepare Your Database Connection

Export your Railway DATABASE_URL:

```bash
# Get from Railway Dashboard -> Postgres -> Connect Tab
export DATABASE_URL="postgresql://username:password@host:port/database"
```

---

## Step 3: Import Opinions

### Test Import (Recommended First)

Start with a small test to verify everything works:

```bash
python3 scripts/import_csv_bulk.py \
    --opinions search_opinion-2025-10-31.csv \
    --limit 1000 \
    --batch-size 500
```

This will import the first 1,000 opinions (~5-10MB of data).

### Check Test Results

```bash
# Query the API to see if opinions have text
curl "https://court-listener-v-production.up.railway.app/api/v1/search/cases?q=United&limit=5" | python3 -m json.tool
```

Look for cases where `opinion_count > 0`, then check one:

```bash
curl "https://court-listener-v-production.up.railway.app/api/v1/search/cases/<CASE_ID>" | python3 -m json.tool
```

Verify the opinion has `plain_text` or `html` content (not null).

---

## Step 4: Full Import

Once testing is successful, import more opinions based on your storage limits:

### Small Import (100K opinions - ~100MB)
```bash
python3 scripts/import_csv_bulk.py \
    --opinions search_opinion-2025-10-31.csv \
    --limit 100000 \
    --batch-size 5000
```

### Medium Import (1M opinions - ~1GB)
```bash
python3 scripts/import_csv_bulk.py \
    --opinions search_opinion-2025-10-31.csv \
    --limit 1000000 \
    --batch-size 5000
```

### Full Import (All opinions - WARNING: Very large!)
```bash
python3 scripts/import_csv_bulk.py \
    --opinions search_opinion-2025-10-31.csv \
    --batch-size 5000
```

**Note:** Railway's free tier has a 500MB database limit. Monitor your usage!

---

## Step 5: Monitor Import Progress

The script provides real-time progress updates:

```
2025-11-17 10:30:00 - INFO - Importing opinions from search_opinion-2025-10-31.csv
2025-11-17 10:30:05 - INFO - Loading valid cluster IDs from database...
2025-11-17 10:30:10 - INFO - Found 13194 valid clusters
2025-11-17 10:32:15 - INFO - ✓ Imported 5000 opinions (skipped 245)
2025-11-17 10:34:20 - INFO - ✓ Imported 10000 opinions (skipped 512)
...
2025-11-17 11:45:30 - INFO - ✅ Imported 100000 opinions total (skipped 2847)
```

**Skipped opinions** occur when:
- The opinion references a cluster_id that doesn't exist in your database
- Required fields are missing
- Data format issues

---

## Step 6: Verify Results

### Check Database Counts

```bash
# Count opinions in database
curl "https://court-listener-v-production.up.railway.app/api/v1/search/cases?q=United&limit=100" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Cases with opinions: {sum(1 for r in d[\"results\"] if r[\"opinion_count\"] > 0)}')"
```

### Test Frontend

1. Visit: https://court-listener-v.vercel.app
2. Search for "United States"
3. Click on a case with `Opinions: 1` badge (green text)
4. Verify you can see the full opinion text

---

## Storage Considerations

### Opinion Text Size Estimates

| Import Size | Opinions | Estimated Storage | Recommended For |
|-------------|----------|-------------------|-----------------|
| Test | 1,000 | ~5-10 MB | Initial testing |
| Small | 100,000 | ~100-200 MB | Railway free tier |
| Medium | 1,000,000 | ~1-2 GB | Railway Pro plan |
| Large | 10,000,000 | ~10-20 GB | Dedicated hosting |

### Railway Storage Limits

- **Free Tier**: 500 MB
- **Pro Tier**: 8 GB+

Check your current usage:
```bash
# In Railway dashboard -> Postgres -> Metrics
```

---

## Selective Import Strategy

If storage is limited, import only the most valuable opinions:

### Strategy 1: High Citation Count Cases

Filter your CSV to only include opinions from cases with many citations:

```bash
# First, get cluster IDs with high citation counts
# Then filter the opinions CSV to only include those clusters
```

### Strategy 2: Recent Cases

Import only recent opinions (e.g., last 10 years):

```bash
# Filter by date in the CSV before importing
```

### Strategy 3: Important Courts

Import only Supreme Court and Circuit Court opinions:

```bash
# Filter by court_id in your clusters
# SCOTUS: scotus
# Circuits: ca1, ca2, ca3, ca4, ca5, ca6, ca7, ca8, ca9, ca10, ca11, cadc, cafc
```

---

## Troubleshooting

### Error: "cluster_id not found"

Many opinions will be skipped if their cluster_id doesn't exist in your database. This is expected if you:
- Imported a limited number of clusters
- Used filtered cluster data

**Solution:** This is normal. The script skips these automatically.

### Error: "Database connection lost"

Large imports may timeout. Solutions:
- Reduce batch size: `--batch-size 1000`
- Add retries to the script
- Import in smaller chunks with `--limit`

### Memory Issues

If the script runs out of memory:
- Reduce batch size
- Close other applications
- Run on a machine with more RAM

### Storage Full

If Railway database is full:
- Delete old data
- Upgrade to Pro plan
- Use selective import strategy

---

## Expected Results

After successful import, you should see:

### In Search Results
- Cases showing `Opinions: 1` or `Opinions: 2` in green
- Opinion count indicates text is available

### In Case Detail Page
- Full opinion text displayed
- Multiple opinions shown (lead, concurrence, dissent)
- HTML formatting rendered properly

### Example Response
```json
{
  "id": 403793,
  "case_name": "United States v. Nelson Bell",
  "opinions": [
    {
      "id": 403793,
      "type": "010lead",
      "plain_text": "OPINION\n\nPER CURIAM:\n\nNelson Bell appeals...",
      "html": "<p>OPINION</p><p>PER CURIAM:</p>...",
      "extracted_by_ocr": false
    }
  ]
}
```

---

## Next Steps

After importing opinions:

1. **Test the search** - Verify opinion text displays correctly
2. **Check performance** - Monitor API response times
3. **Add indexes** - Improve search performance (see below)
4. **Import more data** - Citations, parentheticals, etc.

### Performance Optimization

Add PostgreSQL full-text search indexes:

```sql
-- Full-text search on opinion text
CREATE INDEX idx_opinion_plain_text_fts
ON search_opinion
USING gin(to_tsvector('english', plain_text));

-- Index on cluster_id for faster joins
CREATE INDEX idx_opinion_cluster_id
ON search_opinion(cluster_id);
```

---

## Summary

| Step | Command | Purpose |
|------|---------|---------|
| 1 | Download CSV | Get opinion data |
| 2 | Export DATABASE_URL | Connect to Railway |
| 3 | Test import | Verify setup works |
| 4 | Full import | Load production data |
| 5 | Verify | Check results |

**Time Estimate:**
- Download: 30min - 2hrs (depends on connection)
- Test import (1K): ~1 minute
- Small import (100K): ~10-20 minutes
- Medium import (1M): ~2-4 hours
- Full import (12M): ~1-2 days

---

## Questions?

If you encounter issues:
1. Check the script logs for error messages
2. Verify your DATABASE_URL is correct
3. Ensure you have enough storage space
4. Try a smaller `--limit` first

The import script handles errors gracefully and will skip problematic rows while continuing to import valid data.
