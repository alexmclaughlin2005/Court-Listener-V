#!/bin/bash

# Script to initialize Railway database
# Usage: ./scripts/init_railway_db.sh

echo "🚀 Initializing Railway database..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm i -g @railway/cli
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway..."
    railway login
fi

# Link to project (if not already linked)
echo "🔗 Linking to Railway project..."
railway link

# Initialize database
echo "📊 Creating database tables..."
railway run python init_db.py

echo "✅ Database initialization complete!"
echo ""
echo "Next steps:"
echo "1. Test API: https://your-app.up.railway.app/health"
echo "2. View API docs: https://your-app.up.railway.app/docs"
echo "3. Set up frontend on Vercel"

