#!/usr/bin/env python3
"""
Download opinions CSV directly to Railway volume
Run this on Railway with: railway run python scripts/download_opinions.py
"""
import os
import sys
import requests
from pathlib import Path

# Configuration
DOWNLOAD_URL = "https://storage.courtlistener.com/bulk-data/opinions-2025-10-31.csv.bz2"
OUTPUT_DIR = "/data"
OUTPUT_FILE = "opinions-2025-10-31.csv.bz2"

def download_file(url, output_path, chunk_size=8192):
    """Download file with progress reporting"""
    print(f"Starting download from: {url}")
    print(f"Saving to: {output_path}")

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0

        print(f"Total size: {total_size / (1024**3):.2f} GB")

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    # Progress every 100MB
                    if downloaded % (100 * 1024 * 1024) == 0:
                        progress = (downloaded / total_size * 100) if total_size else 0
                        print(f"Progress: {downloaded / (1024**3):.2f} GB / {total_size / (1024**3):.2f} GB ({progress:.1f}%)")

        print(f"✅ Download complete: {output_path}")
        print(f"File size: {os.path.getsize(output_path) / (1024**3):.2f} GB")
        return True

    except Exception as e:
        print(f"❌ Download failed: {e}")
        # Clean up partial download
        if os.path.exists(output_path):
            os.remove(output_path)
        return False

def main():
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

    # Check if file already exists
    if os.path.exists(output_path):
        print(f"⚠️  File already exists: {output_path}")
        print(f"File size: {os.path.getsize(output_path) / (1024**3):.2f} GB")
        response = input("Do you want to re-download? (y/N): ")
        if response.lower() != 'y':
            print("Skipping download")
            return
        os.remove(output_path)

    success = download_file(DOWNLOAD_URL, output_path)

    if success:
        print("\n✅ Next steps:")
        print(f"1. Extract: railway run python -c \"import bz2, shutil; shutil.copyfileobj(bz2.BZ2File('{output_path}'), open('{OUTPUT_DIR}/opinions-2025-10-31.csv', 'wb'))\"")
        print(f"2. Test import: railway run python scripts/import_csv_bulk.py --opinions /data/opinions-2025-10-31.csv --limit 1000 --batch-size 500")
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
