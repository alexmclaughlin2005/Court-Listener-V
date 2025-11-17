# Opinion Import Commands - Quick Reference

## Prerequisites
- ✅ Railway CLI installed: `npm install -g @railway/cli`
- ✅ Railway volume created and mounted at `/data`
- ✅ Linked to your project: `railway link`

---

## 🚀 **Full Automated Process**

Run this single command to download and extract:

```bash
cd "/Users/alexmclaughlin/Desktop/Cursor Projects/Court Listener V@"
./download_and_import_opinions.sh
```

This will:
1. Download opinions-2025-10-31.csv.bz2 to Railway volume (~12GB, 30min-2hrs)
2. Extract to opinions-2025-10-31.csv (~35GB, 5-10 minutes)
3. Show you the next commands to run

---

## 📥 **Manual Step-by-Step** (if script fails)

### Step 1: Download
```bash
railway run bash -c "cd /data && wget -O opinions-2025-10-31.csv.bz2 'https://storage.courtlistener.com/bulk-data/opinions-2025-10-31.csv.bz2'"
```

### Step 2: Extract
```bash
railway run bash -c "cd /data && bunzip2 opinions-2025-10-31.csv.bz2"
```

### Step 3: Verify
```bash
railway run ls -lh /data/
```

---

## 🧪 **Test Import** (Do this first!)

Import first 1,000 opinions to test:

```bash
railway run python scripts/import_csv_bulk.py \
    --opinions /data/opinions-2025-10-31.csv \
    --limit 1000 \
    --batch-size 500
```

**Expected output:**
```
2025-11-17 15:00:00 - INFO - Importing opinions from /data/opinions-2025-10-31.csv
2025-11-17 15:00:05 - INFO - Loading valid cluster IDs from database...
2025-11-17 15:00:10 - INFO - Found 13194 valid clusters
2025-11-17 15:01:15 - INFO - ✓ Imported 500 opinions (skipped 45)
2025-11-17 15:02:20 - INFO - ✓ Imported 1000 opinions (skipped 92)
2025-11-17 15:02:25 - INFO - ✅ Imported 1000 opinions total (skipped 92)
```

---

## ✅ **Verify Test Import Worked**

Check if opinions have text:

```bash
curl -s "https://court-listener-v-production.up.railway.app/api/v1/search/cases?q=United&limit=10" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Cases with opinions: {sum(1 for r in d[\"results\"] if r[\"opinion_count\"] > 0)}')"
```

Check a specific case:

```bash
curl -s "https://court-listener-v-production.up.railway.app/api/v1/search/cases/403793" | python3 -m json.tool | grep -A3 "plain_text"
```

If you see actual text (not null), it worked! 🎉

---

## 🚀 **Production Import Options**

Once test works, choose your import size:

### Small (10,000 opinions - ~10 minutes)
```bash
railway run python scripts/import_csv_bulk.py \
    --opinions /data/opinions-2025-10-31.csv \
    --limit 10000 \
    --batch-size 5000
```

### Medium (100,000 opinions - ~30-40 minutes)
```bash
railway run python scripts/import_csv_bulk.py \
    --opinions /data/opinions-2025-10-31.csv \
    --limit 100000 \
    --batch-size 5000
```

### Large (1,000,000 opinions - ~5-6 hours)
```bash
railway run python scripts/import_csv_bulk.py \
    --opinions /data/opinions-2025-10-31.csv \
    --limit 1000000 \
    --batch-size 10000
```

---

## 📊 **Monitor Import Progress**

The script logs progress every batch:

```
✓ Imported 5000 opinions (skipped 234)
✓ Imported 10000 opinions (skipped 456)
✓ Imported 15000 opinions (skipped 678)
...
```

**Skipped opinions** are normal - they're opinions whose cluster_id doesn't exist in your database.

---

## 🧹 **Cleanup After Import**

Once import is complete, free up space by deleting the CSV:

```bash
railway run rm /data/opinions-2025-10-31.csv
```

This frees up ~35GB on your Railway volume.

---

## 🔧 **Troubleshooting**

### Download is slow
- Railway's download speed depends on datacenter location
- Alternative: Download locally, then upload to volume (more complex)

### Import fails with memory error
- Reduce batch size: `--batch-size 1000`
- Import in smaller chunks: multiple runs with `--limit`

### Many opinions skipped
- Normal! Only opinions matching your imported clusters will be kept
- You have ~13K clusters, CSV has millions of opinions
- Expected skip rate: 80-90%

### Database runs out of space
- Check Railway database usage in dashboard
- Free tier: 500MB limit
- Reduce import limit or upgrade plan

---

## 📈 **Storage Estimates**

| Opinions Imported | Database Size | Railway Tier |
|------------------|---------------|--------------|
| 1,000 | ~5 MB | Free ✅ |
| 10,000 | ~50 MB | Free ✅ |
| 100,000 | ~150-200 MB | Free ✅ |
| 1,000,000 | ~1.5-2 GB | Pro required |

---

## 🎯 **Recommended Strategy**

1. ✅ **Test**: Import 1,000 opinions
2. ✅ **Verify**: Check frontend displays text
3. ✅ **Small**: Import 10,000 opinions
4. ✅ **Monitor**: Check database size
5. ✅ **Scale**: Import more based on storage

---

## ⏱️ **Time Estimates**

- Download: 30min - 2 hours (12GB)
- Extract: 5-10 minutes (to 35GB)
- Test import (1K): 2-3 minutes
- Small import (10K): 10-15 minutes
- Medium import (100K): 30-45 minutes
- **Total (with testing)**: 1-3 hours

---

## 🆘 **Need Help?**

If something goes wrong:
1. Check Railway logs for error messages
2. Verify DATABASE_URL is accessible
3. Ensure volume is mounted at `/data`
4. Check database storage isn't full

Good luck! 🚀
