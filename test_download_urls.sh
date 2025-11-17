#!/bin/bash

echo "🔍 Testing CourtListener Download URLs for search_opinion"
echo ""

# Test various URL patterns
URLS=(
    "https://com-courtlistener-storage.s3.amazonaws.com/bulk-data/search_opinion-2025-10-31.csv.bz2"
    "https://com-courtlistener-storage.s3-us-west-2.amazonaws.com/bulk-data/search_opinion-2025-10-31.csv.bz2"
    "https://storage.courtlistener.com/bulk-data/search_opinion-2025-10-31.csv.bz2"
    "https://www.courtlistener.com/api/bulk-data/opinions/search_opinion-2025-10-31.csv.bz2"
)

for URL in "${URLS[@]}"; do
    echo "Testing: $URL"
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -I "$URL" 2>/dev/null)
    
    if [ "$STATUS" = "200" ]; then
        echo "✅ FOUND! Status: $STATUS"
        SIZE=$(curl -sI "$URL" | grep -i content-length | awk '{print $2}' | tr -d '\r')
        SIZE_GB=$(echo "scale=2; $SIZE / 1073741824" | bc)
        echo "   Size: ${SIZE_GB} GB"
        echo ""
        echo "📥 Download command:"
        echo "   wget '$URL'"
        echo ""
        exit 0
    else
        echo "   Status: $STATUS"
    fi
    echo ""
done

echo "❌ None of the tested URLs worked."
echo ""
echo "💡 Next steps:"
echo "1. Check where you downloaded your other CSV files from:"
ls -lh search_opinioncluster-2025-10-31.csv search_opinionscited-2025-10-31.csv 2>/dev/null | head -2
echo ""
echo "2. If you used CourtListener's website, log in and check your download history"
echo "3. Or email info@free.law to request the download link"
