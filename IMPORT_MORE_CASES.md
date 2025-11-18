# Import More Cases - Quick Start Guide

## Current Status
- **Dockets**: 100,014
- **Clusters**: 36,642
- **Opinions**: 36,642
- **Citations**: 41,295
- **Parentheticals**: 6,006,011

---

## Step 1: Download Required Files

```bash
# Download from CourtListener bulk data storage
wget https://storage.courtlistener.com/bulk-data/dockets-2025-10-31.csv.bz2
wget https://storage.courtlistener.com/bulk-data/opinion-clusters-2025-10-31.csv.bz2
wget https://storage.courtlistener.com/bulk-data/citations-2025-10-31.csv.bz2

# Decompress (this will take a while)
bunzip2 dockets-2025-10-31.csv.bz2
bunzip2 opinion-clusters-2025-10-31.csv.bz2
bunzip2 citations-2025-10-31.csv.bz2
```

**Note**: We're skipping opinions CSV (50GB) - you'll fetch those via API instead.

---

## Step 2: Import Data in Chunks

The new script automatically tracks progress and resumes from where it left off.

### Import 100k dockets at a time:
```bash
export DATABASE_URL="postgresql://postgres:GUYuYYTmYWGmUlcadtojoLWmhKFlHPJE@switchback.proxy.rlwy.net:49807/railway"

# Run this multiple times - it automatically resumes
python3 scripts/import_csv_resumable.py \
  --dockets dockets-2025-10-31.csv \
  --chunk-size 100000
```

### Import 100k clusters at a time:
```bash
python3 scripts/import_csv_resumable.py \
  --clusters opinion-clusters-2025-10-31.csv \
  --chunk-size 100000
```

### Import citations:
```bash
python3 scripts/import_csv_resumable.py \
  --citations citations-2025-10-31.csv \
  --chunk-size 100000
```

---

## Step 3: Check Progress

```bash
python3 scripts/import_csv_resumable.py --status
```

This shows:
- How many rows imported
- How many rows skipped
- Last row processed
- Status (in_progress, completed, error)

---

## Step 4: Fetch Opinion Text via API

After importing clusters, use the API to fetch opinion text for the cluster IDs you've imported:

```bash
# You'll create this script separately
python3 scripts/fetch_opinions_api.py
```

---

## Quick Loop to Import 500k Records

```bash
export DATABASE_URL="postgresql://..."

# Import 500k dockets (5 runs × 100k)
for i in {1..5}; do
  echo "===== Importing dockets batch $i of 5 ====="
  python3 scripts/import_csv_resumable.py \
    --dockets dockets-2025-10-31.csv \
    --chunk-size 100000
done

# Import 500k clusters (5 runs × 100k)
for i in {1..5}; do
  echo "===== Importing clusters batch $i of 5 ====="
  python3 scripts/import_csv_resumable.py \
    --clusters opinion-clusters-2025-10-31.csv \
    --chunk-size 100000
done

# Check final status
python3 scripts/import_csv_resumable.py --status
```

---

## Key Features of the New Script

✅ **Resumable** - Interrupted? Just run again, it continues from where it stopped
✅ **Progress Tracking** - Check status anytime with `--status`
✅ **Chunked** - Import 100k records at a time (configurable)
✅ **Foreign Key Validation** - Automatically skips records with invalid references
✅ **Duplicate Safe** - Uses `ON CONFLICT DO NOTHING` to skip duplicates
✅ **No Opinions CSV** - Opinions will be fetched via API to avoid 50GB download

---

## Import Order (Important!)

Must follow this sequence due to foreign key constraints:

1. ✅ Courts (already done)
2. → Dockets
3. → Clusters
4. → ~~Opinions~~ (skip CSV, use API)
5. → Citations
6. → Parentheticals

---

## Troubleshooting

### Import got stuck?
Just run the same command again - it will resume automatically.

### Want to import everything at once?
```bash
python3 scripts/import_csv_resumable.py --all --chunk-size 200000
```

### How long will this take?
- 100k dockets: ~30-60 minutes
- 100k clusters: ~20-40 minutes
- 100k citations: ~10-20 minutes

**Total for 1M records: ~10-20 hours** (can run overnight)

---

## After Import

Check your database:
```bash
psql $DATABASE_URL -c "
SELECT
  (SELECT COUNT(*) FROM search_docket) as dockets,
  (SELECT COUNT(*) FROM search_opinioncluster) as clusters,
  (SELECT COUNT(*) FROM search_opinion) as opinions,
  (SELECT COUNT(*) FROM search_opinionscited) as citations;
"
```

Next step: Create API batch script to fetch opinion text for your imported clusters!
