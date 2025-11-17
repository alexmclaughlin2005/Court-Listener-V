#!/bin/bash

# Download and Import Opinion Text from CourtListener
# This script downloads opinions CSV to Railway volume and imports it

set -e  # Exit on error

echo "🚀 CourtListener Opinion Text Download & Import"
echo "================================================"
echo ""

# Configuration
OPINION_URL="https://storage.courtlistener.com/bulk-data/opinions-2025-10-31.csv.bz2"
VOLUME_PATH="/data"
COMPRESSED_FILE="opinions-2025-10-31.csv.bz2"
EXTRACTED_FILE="opinions-2025-10-31.csv"

# Step 1: Download to Railway volume
echo "📥 Step 1: Downloading opinion CSV to Railway volume..."
echo "   URL: $OPINION_URL"
echo "   Destination: $VOLUME_PATH/$COMPRESSED_FILE"
echo ""
echo "   ⏱️  This may take 30min - 2 hours depending on connection..."
echo ""

railway run bash -c "cd $VOLUME_PATH && wget -O $COMPRESSED_FILE '$OPINION_URL' && echo '✅ Download complete!' && ls -lh $COMPRESSED_FILE"

if [ $? -ne 0 ]; then
    echo "❌ Download failed!"
    exit 1
fi

echo ""
echo "✅ Download complete!"
echo ""

# Step 2: Extract the file
echo "📦 Step 2: Extracting compressed file..."
echo "   This will decompress the ~12GB file to ~35GB"
echo ""

railway run bash -c "cd $VOLUME_PATH && bunzip2 -v $COMPRESSED_FILE && echo '✅ Extraction complete!' && ls -lh $EXTRACTED_FILE"

if [ $? -ne 0 ]; then
    echo "❌ Extraction failed!"
    exit 1
fi

echo ""
echo "✅ Extraction complete!"
echo ""

# Step 3: Verify file is ready
echo "🔍 Step 3: Verifying file..."
railway run ls -lh $VOLUME_PATH/$EXTRACTED_FILE

echo ""
echo "✅ File ready for import!"
echo ""
echo "================================================"
echo "📊 Next Steps:"
echo ""
echo "1. Test Import (1,000 opinions - ~2 minutes):"
echo "   railway run python scripts/import_csv_bulk.py \\"
echo "       --opinions $VOLUME_PATH/$EXTRACTED_FILE \\"
echo "       --limit 1000 \\"
echo "       --batch-size 500"
echo ""
echo "2. Verify it worked:"
echo "   curl 'https://court-listener-v-production.up.railway.app/api/v1/search/cases?q=United&limit=5'"
echo ""
echo "3. Full Import (100,000 opinions - ~30 minutes):"
echo "   railway run python scripts/import_csv_bulk.py \\"
echo "       --opinions $VOLUME_PATH/$EXTRACTED_FILE \\"
echo "       --limit 100000 \\"
echo "       --batch-size 5000"
echo ""
echo "================================================"
echo ""
echo "🎉 Download and extraction complete!"
echo "   Ready to import opinions!"
