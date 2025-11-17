#!/bin/bash

# Import CourtListener CSV data to Railway Database
# Run this locally with your CSV files

echo "🚀 CourtListener CSV Import to Railway"
echo ""

# Get DATABASE_URL from Railway
echo "📋 Step 1: Get your Railway DATABASE_URL"
echo "   1. Go to: https://railway.app/project/your-project"
echo "   2. Click on your Postgres database"
echo "   3. Go to 'Connect' tab"
echo "   4. Copy the 'DATABASE_URL' (PostgreSQL Connection URL)"
echo ""
echo "Paste your DATABASE_URL here:"
read -r DATABASE_URL

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL is required"
    exit 1
fi

export DATABASE_URL

echo ""
echo "✅ DATABASE_URL set"
echo ""

# Check if psycopg2 is installed
echo "📦 Checking Python dependencies..."
python3 -c "import psycopg2" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing psycopg2..."
    pip3 install psycopg2-binary
fi

echo ""
echo "🎯 Import Options:"
echo "   1. Test (10,000 records)"
echo "   2. Small (100,000 records)"
echo "   3. Medium (1,000,000 records)"
echo "   4. Large (10,000,000 records)"
echo "   5. Full (all records - WARNING: will take days)"
echo "   6. Custom"
echo ""
echo "Choose an option (1-6):"
read -r OPTION

case $OPTION in
    1)
        LIMIT=10000
        ;;
    2)
        LIMIT=100000
        ;;
    3)
        LIMIT=1000000
        ;;
    4)
        LIMIT=10000000
        ;;
    5)
        LIMIT=""
        ;;
    6)
        echo "Enter custom limit:"
        read -r LIMIT
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "📊 Starting import..."
echo "   Limit: ${LIMIT:-unlimited}"
echo ""

# Run import
if [ -z "$LIMIT" ]; then
    python3 scripts/import_csv_bulk.py \
        --courts people_db_court-2025-10-31.csv \
        --dockets search_docket-2025-10-31.csv \
        --clusters search_opinioncluster-2025-10-31.csv \
        --batch-size 5000
else
    python3 scripts/import_csv_bulk.py \
        --courts people_db_court-2025-10-31.csv \
        --dockets search_docket-sample.csv \
        --clusters search_opinioncluster-2025-10-31.csv \
        --limit $LIMIT \
        --batch-size 5000
fi

echo ""
echo "✅ Import complete!"
echo ""
echo "📍 Check your data:"
echo "   curl https://court-listener-v-production.up.railway.app/api/v1/import/status"
