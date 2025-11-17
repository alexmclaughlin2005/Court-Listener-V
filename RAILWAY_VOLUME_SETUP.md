# Railway Volume Setup for Opinion CSV Download

## Step 1: Create Railway Volume

1. Go to your Railway project: https://railway.app
2. Click on your backend service
3. Go to **"Settings"** tab
4. Scroll to **"Volumes"** section
5. Click **"+ New Volume"**
6. Configure:
   - **Mount Path**: `/data`
   - **Size**: 50 GB (for opinion CSV + extraction space)
7. Click **"Add Volume"**

**The service will redeploy with the volume mounted.**

---

## Step 2: Find the Opinion CSV Download URL

The file you need is `search_opinion-2025-10-31.csv` (or latest date).

### Option A: Check CourtListener's Bulk Data Page

Since you already have other CSVs from 2025-10-31, you likely got them from:
- https://www.courtlistener.com/api/bulk-data/

**Check where you originally downloaded:**
```bash
# Look at your download history or the source you used for:
# - search_opinioncluster-2025-10-31.csv
# - search_opinionscited-2025-10-31.csv
```

The `search_opinion` file should be in the same location.

### Option B: Try Direct S3 URLs

Based on your existing files, try these patterns:

```bash
# Pattern 1: Main bulk data bucket
https://com-courtlistener-storage.s3.amazonaws.com/bulk-data/search_opinion-2025-10-31.csv.bz2

# Pattern 2: US-West-2 region
https://com-courtlistener-storage.s3-us-west-2.amazonaws.com/bulk-data/search_opinion-2025-10-31.csv.bz2

# Pattern 3: Opinions subfolder
https://com-courtlistener-storage.s3.amazonaws.com/bulk-data/opinions/search_opinion-2025-10-31.csv.bz2
```

### Option C: Contact CourtListener

If URLs don't work, email them:
- **Email**: info@free.law
- **Subject**: "Bulk Data Access - search_opinion CSV"
- **Message**: Request the download link for search_opinion-2025-10-31.csv

---

## Step 3: Download to Railway Volume

Once you have the volume mounted and the URL, we'll use Railway's CLI to download directly to the volume.

### Method 1: Using Railway Run (Recommended)

```bash
# Install Railway CLI (if not installed)
npm install -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Download directly to volume
railway run bash -c "cd /data && wget -O search_opinion-2025-10-31.csv.bz2 'YOUR_DOWNLOAD_URL' && bunzip2 search_opinion-2025-10-31.csv.bz2"
```

### Method 2: Using Custom Script

Create a download script in your backend:

**backend/app/utils/download_opinions.py:**
```python
import requests
import os
from tqdm import tqdm

def download_file(url, destination):
    """Download large file with progress bar"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))

    with open(destination, 'wb') as f:
        with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))

if __name__ == "__main__":
    URL = "YOUR_DOWNLOAD_URL"
    DEST = "/data/search_opinion-2025-10-31.csv.bz2"

    print(f"Downloading to {DEST}...")
    download_file(URL, DEST)
    print("Download complete!")

    print("Extracting...")
    os.system(f"bunzip2 {DEST}")
    print("Extraction complete!")
```

Then run on Railway:
```bash
railway run python backend/app/utils/download_opinions.py
```

---

## Step 4: Verify Download

Check if file downloaded successfully:

```bash
railway run ls -lh /data/
```

You should see:
```
-rw-r--r-- 1 root root 30G Nov 17 12:00 search_opinion-2025-10-31.csv
```

---

## Step 5: Import from Volume

Update your import command to use the volume path:

```bash
# Set DATABASE_URL (get from Railway)
export DATABASE_URL="postgresql://..."

# Run import from Railway volume
railway run python scripts/import_csv_bulk.py \
    --opinions /data/search_opinion-2025-10-31.csv \
    --limit 100000 \
    --batch-size 5000
```

---

## Storage Considerations

**Railway Volume Pricing:**
- **Free tier**: 100 GB included
- **Pro tier**: 100 GB included, $0.25/GB/month after

**File Sizes:**
- Compressed (.bz2): ~10-15 GB
- Uncompressed (.csv): ~30-50 GB
- Total needed: ~50 GB (during extraction)

**After Import:**
You can delete the CSV from the volume to free up space:
```bash
railway run rm /data/search_opinion-2025-10-31.csv
```

---

## Timeline Estimate

| Step | Time |
|------|------|
| Create volume | 2-5 minutes |
| Find download URL | 5-30 minutes |
| Download (~15GB) | 30min - 2hrs |
| Extract (~30GB) | 10-30 minutes |
| Import (100K) | 20-40 minutes |
| **Total** | **1-4 hours** |

---

## Alternative: Download Locally First

If Railway download is slow, you can download locally then upload:

```bash
# Download locally
wget 'YOUR_URL' -O search_opinion-2025-10-31.csv.bz2
bunzip2 search_opinion-2025-10-31.csv.bz2

# Upload to Railway volume (requires additional setup)
# Or run import locally, connecting to Railway DB
export DATABASE_URL="postgresql://..."
python3 scripts/import_csv_bulk.py \
    --opinions search_opinion-2025-10-31.csv \
    --limit 100000
```

---

## Next Steps

1. ✅ Create Railway volume (50 GB)
2. 🔍 Find download URL (check your original download source)
3. 📥 Download to volume using Railway CLI
4. ✅ Run import script
5. 🎉 Verify opinions display on frontend!

Let me know when you have the volume set up and I'll help with the download command!
