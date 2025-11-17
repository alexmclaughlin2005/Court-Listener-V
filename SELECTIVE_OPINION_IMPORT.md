# Selective Opinion Import Guide

This guide shows how to import only the opinions for cases you have in your database, dramatically reducing storage requirements from ~50GB to ~1-2GB.

## Why Selective Import?

Your database has ~13,194 opinion clusters. The full opinions CSV has millions of opinions. By filtering to only opinions that match your clusters, you can reduce the dataset by 90-95%.

**Storage comparison:**
- Full import: ~50GB extracted CSV
- Selective import: ~1-2GB (only opinions for your 13K clusters)

---

## Process Overview

1. **Download CSV locally** - Download the full CSV to your Mac
2. **Get DATABASE_URL** - Get your Railway database connection string
3. **Filter opinions** - Run script to filter by cluster_id
4. **Import to Railway** - Import filtered CSV directly to database

**Total time:** 1-3 hours (mostly download time)

---

## Step 1: Download Opinions CSV to Your Mac

Download the compressed CSV file to your local machine:

```bash
cd ~/Downloads
wget https://storage.courtlistener.com/bulk-data/opinions-2025-10-31.csv.bz2
```

**File size:** ~46GB compressed
**Time:** 30-60 minutes (depends on internet speed)

### Monitor Download Progress

```bash
# In another terminal
watch -n 5 'ls -lh ~/Downloads/opinions-2025-10-31.csv.bz2'
```

---

## Step 2: Extract the CSV

```bash
cd ~/Downloads
bunzip2 opinions-2025-10-31.csv.bz2
```

This creates `opinions-2025-10-31.csv` (~100-120GB uncompressed)

**Time:** 5-10 minutes

---

## Step 3: Get Your Database URL

```bash
railway variables | grep DATABASE_PUBLIC_URL
```

Copy the full PostgreSQL connection string (starts with `postgresql://`)

Example:
```
postgresql://postgres:PASSWORD@switchback.proxy.rlwy.net:49807/railway
```

Export it:
```bash
export DATABASE_URL="postgresql://postgres:PASSWORD@switchback.proxy.rlwy.net:49807/railway"
```

---

## Step 4: Filter Opinions by Your Clusters

Run the filter script:

```bash
cd "/Users/alexmclaughlin/Desktop/Cursor Projects/Court Listener V@"

python3 scripts/filter_opinions_by_clusters.py \
    --input ~/Downloads/opinions-2025-10-31.csv \
    --output ~/Downloads/opinions-filtered.csv
```

**What this does:**
1. Connects to your Railway database
2. Gets all cluster IDs (should be ~13,194)
3. Reads the full opinions CSV
4. Keeps only opinions with matching cluster_id
5. Writes filtered CSV

**Expected output:**
```
2025-11-17 15:00:00 - INFO - Connecting to database...
2025-11-17 15:00:01 - INFO - Loading cluster IDs from database...
2025-11-17 15:00:02 - INFO - Found 13194 clusters in database
2025-11-17 15:00:03 - INFO - Reading opinions from: /Users/.../opinions-2025-10-31.csv
2025-11-17 15:00:04 - INFO - Writing filtered opinions to: /Users/.../opinions-filtered.csv
2025-11-17 15:00:05 - INFO - Input file size: 103.45 GB
2025-11-17 15:05:00 - INFO - Processed 100,000 rows | Kept: 1,245 | Skipped: 98,755 | Output size: 0.03 GB
2025-11-17 15:10:00 - INFO - Processed 200,000 rows | Kept: 2,512 | Skipped: 197,488 | Output size: 0.06 GB
...
2025-11-17 16:30:00 - INFO - ✅ Filtering complete!
2025-11-17 16:30:00 - INFO - Total rows processed: 12,345,678
2025-11-17 16:30:00 - INFO - Opinions kept: 15,234
2025-11-17 16:30:00 - INFO - Opinions skipped: 12,330,444
2025-11-17 16:30:00 - INFO - Input size: 103.45 GB
2025-11-17 16:30:00 - INFO - Output size: 1.23 GB
2025-11-17 16:30:00 - INFO - Size reduction: 98.8%
```

**Time:** 30-60 minutes (processing 12M+ rows)

---

## Step 5: Import Filtered Opinions to Railway

Now import the much smaller filtered CSV directly to your Railway database:

```bash
python3 scripts/import_csv_bulk.py \
    --opinions ~/Downloads/opinions-filtered.csv \
    --batch-size 5000
```

**Time:** 5-15 minutes (depending on filtered size)

**Expected output:**
```
2025-11-17 16:35:00 - INFO - Importing opinions from /Users/.../opinions-filtered.csv
2025-11-17 16:35:01 - INFO - Loading valid cluster IDs from database...
2025-11-17 16:35:02 - INFO - Found 13194 valid clusters
2025-11-17 16:36:00 - INFO - ✓ Imported 5000 opinions (skipped 0)
2025-11-17 16:37:00 - INFO - ✓ Imported 10000 opinions (skipped 0)
2025-11-17 16:38:00 - INFO - ✓ Imported 15234 opinions (skipped 0)
2025-11-17 16:38:05 - INFO - ✅ Imported 15234 opinions total (skipped 0)
```

---

## Step 6: Verify Import Worked

### Check via API

```bash
curl -s "https://court-listener-v-production.up.railway.app/api/v1/search/cases?q=United&limit=10" \
  | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Cases with opinions: {sum(1 for r in d[\"results\"] if r[\"opinion_count\"] > 0)}')"
```

Should show: `Cases with opinions: 10` (or similar)

### Check Specific Case

```bash
curl -s "https://court-listener-v-production.up.railway.app/api/v1/search/cases/403793" \
  | python3 -m json.tool \
  | grep -A3 "plain_text"
```

Should show actual opinion text (not null).

### Check Frontend

1. Visit: https://court-listener-v.vercel.app
2. Search for "United States"
3. Click a case with "Opinions: 1" badge
4. Verify you can see full opinion text

---

## Cleanup

After successful import, you can delete the local files to free up space:

```bash
rm ~/Downloads/opinions-2025-10-31.csv
rm ~/Downloads/opinions-filtered.csv
```

This frees up ~104GB on your Mac.

---

## Storage Requirements

| Step | Storage Needed | Duration |
|------|----------------|----------|
| Download compressed | 46 GB | 30-60 min |
| Extract full CSV | 104 GB | 5-10 min |
| Create filtered CSV | 1-2 GB | 30-60 min |
| Import to Railway | 0 GB (direct import) | 5-15 min |

**Peak storage:** ~150GB on your Mac during filtering
**Railway database:** ~1-2GB for opinions
**Total time:** 1-3 hours

---

## Troubleshooting

### "No clusters found in database"

Check your DATABASE_URL is correct:
```bash
echo $DATABASE_URL
```

Should be the PUBLIC URL from Railway, not the internal URL.

### "No matching opinions found"

This could mean:
- Cluster IDs in CSV don't match database format
- Database has no clusters loaded
- CSV format has changed

Verify clusters exist:
```bash
curl "https://court-listener-v-production.up.railway.app/api/v1/import/status"
```

### Download is slow

The file is 46GB, so download time depends on your internet speed:
- 100 Mbps: ~1 hour
- 50 Mbps: ~2 hours
- 25 Mbps: ~4 hours

Consider downloading overnight if slow.

### Not enough disk space

You need ~150GB free during the process. Check:
```bash
df -h ~
```

If tight on space, you can:
1. Delete compressed file after extraction
2. Delete full CSV after filtering
3. Use an external drive

---

## Why This Approach?

### ✅ Advantages

1. **Much smaller dataset** - 98%+ size reduction
2. **Faster imports** - Only relevant data
3. **Lower costs** - Fits in Railway free tier database
4. **Better performance** - Less data to search through

### ⚠️ Limitations

1. **Takes time** - 1-3 hours total
2. **Requires local space** - 150GB during process
3. **One-time process** - Need to repeat for updates

### 🔄 Alternative: API Integration

If you don't want to deal with downloads, consider the [API approach](OPINION_DOWNLOAD_OPTIONS.md) which fetches opinions on-demand from CourtListener.

---

## Summary

```bash
# 1. Download
wget https://storage.courtlistener.com/bulk-data/opinions-2025-10-31.csv.bz2

# 2. Extract
bunzip2 opinions-2025-10-31.csv.bz2

# 3. Get database URL
export DATABASE_URL="$(railway variables | grep DATABASE_PUBLIC_URL | cut -d'│' -f2 | xargs)"

# 4. Filter
python3 scripts/filter_opinions_by_clusters.py \
    --input ~/Downloads/opinions-2025-10-31.csv \
    --output ~/Downloads/opinions-filtered.csv

# 5. Import
python3 scripts/import_csv_bulk.py \
    --opinions ~/Downloads/opinions-filtered.csv \
    --batch-size 5000

# 6. Verify
curl "https://court-listener-v-production.up.railway.app/api/v1/search/cases?q=United&limit=5"
```

Good luck! 🚀
