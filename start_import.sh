#!/bin/bash
# Startup script to begin importing CourtListener data in chunks

set -e  # Exit on error

echo "========================================"
echo "CourtListener Data Import - Startup"
echo "========================================"
echo ""

# Set database URL
export DATABASE_URL="postgresql://postgres:GUYuYYTmYWGmUlcadtojoLWmhKFlHPJE@switchback.proxy.rlwy.net:49807/railway"

# Check if CSV files exist
echo "📋 Checking for required CSV files..."
MISSING_FILES=0

if [ ! -f "dockets-2025-10-31.csv" ]; then
    echo "❌ dockets-2025-10-31.csv not found"
    MISSING_FILES=1
fi

if [ ! -f "opinion-clusters-2025-10-31.csv" ]; then
    echo "❌ opinion-clusters-2025-10-31.csv not found"
    MISSING_FILES=1
fi

if [ ! -f "citations-2025-10-31.csv" ]; then
    echo "❌ citations-2025-10-31.csv not found"
    MISSING_FILES=1
fi

if [ $MISSING_FILES -eq 1 ]; then
    echo ""
    echo "⚠️  Some CSV files are missing. Checking for .bz2 files..."
    if [ -f "dockets-2025-10-31.csv.bz2" ] || [ -f "opinion-clusters-2025-10-31.csv.bz2" ] || [ -f "citations-2025-10-31.csv.bz2" ]; then
        echo "Found compressed files. Extracting..."
        [ -f "dockets-2025-10-31.csv.bz2" ] && bunzip2 -k dockets-2025-10-31.csv.bz2 &
        [ -f "opinion-clusters-2025-10-31.csv.bz2" ] && bunzip2 -k opinion-clusters-2025-10-31.csv.bz2 &
        [ -f "citations-2025-10-31.csv.bz2" ] && bunzip2 -k citations-2025-10-31.csv.bz2 &
        wait
        echo "✓ Extraction complete"
    else
        echo "❌ No CSV or .bz2 files found. Please download them first."
        exit 1
    fi
fi

echo "✓ All CSV files ready"
echo ""

# Check database connection
echo "🔌 Testing database connection..."
if ! psql "$DATABASE_URL" -c "SELECT 1" > /dev/null 2>&1; then
    echo "❌ Cannot connect to database"
    exit 1
fi
echo "✓ Database connection successful"
echo ""

# Show current database status
echo "📊 Current database status:"
psql "$DATABASE_URL" -c "
SELECT
  (SELECT COUNT(*) FROM search_docket) as dockets,
  (SELECT COUNT(*) FROM search_opinioncluster) as clusters,
  (SELECT COUNT(*) FROM search_opinion) as opinions,
  (SELECT COUNT(*) FROM search_opinionscited) as citations
" 2>/dev/null || echo "  (Unable to query - tables may not exist yet)"
echo ""

# Ask user what to do
echo "========================================"
echo "Import Options:"
echo "========================================"
echo "1. Import 100k dockets"
echo "2. Import 100k clusters"
echo "3. Import 100k citations"
echo "4. Import all (dockets → clusters → citations)"
echo "5. Check import progress status"
echo "6. Custom chunk size"
echo ""
read -p "Choose an option (1-6): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Importing 100,000 dockets..."
        python3 scripts/import_csv_resumable.py --dockets dockets-2025-10-31.csv --chunk-size 100000
        ;;
    2)
        echo ""
        echo "🚀 Importing 100,000 clusters..."
        python3 scripts/import_csv_resumable.py --clusters opinion-clusters-2025-10-31.csv --chunk-size 100000
        ;;
    3)
        echo ""
        echo "🚀 Importing 100,000 citations..."
        python3 scripts/import_csv_resumable.py --citations citations-2025-10-31.csv --chunk-size 100000
        ;;
    4)
        echo ""
        echo "🚀 Importing all tables with 100k chunks..."
        echo ""

        # Import dockets
        echo "=== 1/3: Importing dockets ==="
        for i in {1..5}; do
            echo "Batch $i of 5..."
            python3 scripts/import_csv_resumable.py --dockets dockets-2025-10-31.csv --chunk-size 100000
        done

        echo ""
        echo "=== 2/3: Importing clusters ==="
        for i in {1..5}; do
            echo "Batch $i of 5..."
            python3 scripts/import_csv_resumable.py --clusters opinion-clusters-2025-10-31.csv --chunk-size 100000
        done

        echo ""
        echo "=== 3/3: Importing citations ==="
        for i in {1..5}; do
            echo "Batch $i of 5..."
            python3 scripts/import_csv_resumable.py --citations citations-2025-10-31.csv --chunk-size 100000
        done
        ;;
    5)
        echo ""
        echo "📊 Import progress status:"
        python3 scripts/import_csv_resumable.py --status
        ;;
    6)
        echo ""
        read -p "Enter chunk size (e.g., 50000, 200000): " chunk_size
        echo ""
        echo "What to import?"
        echo "1. Dockets"
        echo "2. Clusters"
        echo "3. Citations"
        read -p "Choose (1-3): " import_choice

        case $import_choice in
            1)
                python3 scripts/import_csv_resumable.py --dockets dockets-2025-10-31.csv --chunk-size $chunk_size
                ;;
            2)
                python3 scripts/import_csv_resumable.py --clusters opinion-clusters-2025-10-31.csv --chunk-size $chunk_size
                ;;
            3)
                python3 scripts/import_csv_resumable.py --citations citations-2025-10-31.csv --chunk-size $chunk_size
                ;;
            *)
                echo "Invalid choice"
                exit 1
                ;;
        esac
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "✅ Import task complete!"
echo "========================================"
echo ""
echo "To continue importing, run this script again:"
echo "  ./start_import.sh"
echo ""
echo "To check progress:"
echo "  python3 scripts/import_csv_resumable.py --status"
echo ""
