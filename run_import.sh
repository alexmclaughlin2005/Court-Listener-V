#!/bin/bash
echo "🚀 Starting import with foreign key validation..."
echo ""
echo "Please paste your Railway DATABASE_URL:"
read -r DATABASE_URL
export DATABASE_URL

python3 scripts/import_csv_bulk.py \
  --courts people_db_court-2025-10-31.csv \
  --dockets search_docket-sample.csv \
  --clusters search_opinioncluster-2025-10-31.csv \
  --limit 10000 \
  --batch-size 5000
