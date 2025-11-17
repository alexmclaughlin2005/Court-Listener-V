#!/bin/bash

echo "🔍 CourtListener Opinion Text Download Guide"
echo ""
echo "The search_opinion CSV file contains the actual opinion text content."
echo "This is separate from search_opinioncluster (which you already have)."
echo ""
echo "📦 File Details:"
echo "   Name: search_opinion-2025-10-31.csv"
echo "   Size: ~30-50 GB (uncompressed)"
echo "   Contains: plain_text, html, and other opinion fields"
echo ""
echo "🌐 Download Options:"
echo ""
echo "Option 1: AWS S3 Direct Download (Fastest)"
echo "   URL Pattern: https://com-courtlistener-storage.s3.amazonaws.com/bulk-data/opinions/search_opinion-YYYY-MM-DD.csv.bz2"
echo ""
echo "Option 2: CourtListener Website (Requires Account)"
echo "   1. Visit: https://www.courtlistener.com/api/bulk-data/"
echo "   2. Sign in or create account"
echo "   3. Download search_opinion file"
echo ""
echo "📥 Attempting AWS S3 download..."
echo ""

# Try different date formats
DATES=("2025-10-31" "2024-12-31" "2024-11-30")

for DATE in "${DATES[@]}"; do
    URL="https://com-courtlistener-storage.s3.amazonaws.com/bulk-data/opinions/search_opinion-${DATE}.csv.bz2"
    echo "Checking: $URL"
    
    # Check if URL exists
    if curl -I -s "$URL" | grep -q "200 OK"; then
        echo "✅ Found: $URL"
        echo ""
        echo "To download (WARNING: ~10-20GB compressed):"
        echo "  wget '$URL'"
        echo ""
        echo "To download and extract:"
        echo "  wget '$URL' && bunzip2 search_opinion-${DATE}.csv.bz2"
        exit 0
    fi
done

echo "❌ Could not find recent opinion file on S3"
echo ""
echo "🔧 Manual Steps:"
echo "1. Check CourtListener's website: https://www.courtlistener.com/api/bulk-data/"
echo "2. Or try this AWS S3 bucket browser:"
echo "   https://com-courtlistener-storage.s3.amazonaws.com/bulk-data/opinions/"
echo ""
echo "3. Once you have the download URL, run:"
echo "   wget <URL>"
echo "   bunzip2 search_opinion-*.csv.bz2"
