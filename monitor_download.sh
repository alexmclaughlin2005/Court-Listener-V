#!/bin/bash

# Monitor opinion CSV download progress

API_URL="https://court-listener-v-production.up.railway.app/api/v1/admin/download-status"

echo "📊 Monitoring Opinion CSV Download"
echo "==================================="
echo ""

while true; do
    # Get status
    response=$(curl -s "$API_URL")
    status=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
    progress=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['progress'])" 2>/dev/null)
    message=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['message'])" 2>/dev/null)

    # Clear line and print status
    echo -ne "\r\033[K"

    if [ "$status" = "downloading" ]; then
        echo -ne "⏳ Downloading: ${progress}% | ${message}"
    elif [ "$status" = "extracting" ]; then
        echo -ne "📦 Extracting compressed file..."
    elif [ "$status" = "complete" ]; then
        echo -e "\n✅ Download and extraction complete!"
        echo ""
        echo "Next steps:"
        echo "1. Test import: railway run python scripts/import_csv_bulk.py --opinions /data/opinions-2025-10-31.csv --limit 1000 --batch-size 500"
        break
    elif [ "$status" = "error" ]; then
        echo -e "\n❌ Error: ${message}"
        break
    else
        echo -ne "Status: ${status}"
    fi

    sleep 5
done

echo ""
