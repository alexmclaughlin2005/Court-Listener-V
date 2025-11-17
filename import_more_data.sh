#!/bin/bash
echo "📊 Importing more data to improve cluster coverage..."
echo ""

export DATABASE_URL="postgresql://postgres:GUYuYYTmYWGmUlcadtojoLWmhKFlHPJE@switchback.proxy.rlwy.net:49807/railway"

# Import 100K dockets from the full file
echo "🔄 Importing 100,000 dockets (this will take ~5 minutes)..."
python3 scripts/import_csv_bulk.py \
  --dockets search_docket-2025-10-31.csv \
  --limit 100000 \
  --batch-size 5000

echo ""
echo "🔄 Now importing clusters that match the new dockets..."
python3 scripts/import_csv_bulk.py \
  --clusters search_opinioncluster-2025-10-31.csv \
  --limit 100000 \
  --batch-size 5000

echo ""
echo "✅ Import complete!"
