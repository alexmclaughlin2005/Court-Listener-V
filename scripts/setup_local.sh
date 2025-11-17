#!/bin/bash

# Local Development Setup Script
# This script sets up the local development environment

set -e

echo "🚀 Setting up CourtListener Case Law Browser locally..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if PostgreSQL is running
echo -e "${YELLOW}Checking PostgreSQL...${NC}"
if command -v pg_isready &> /dev/null; then
    if pg_isready -q; then
        echo -e "${GREEN}✓ PostgreSQL is running${NC}"
    else
        echo -e "${YELLOW}⚠ PostgreSQL is not running. Starting...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew services start postgresql@15 || brew services start postgresql
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo systemctl start postgresql
        fi
    fi
else
    echo -e "${YELLOW}⚠ PostgreSQL not found. Please install PostgreSQL 15+${NC}"
    echo "  macOS: brew install postgresql@15"
    echo "  Linux: sudo apt install postgresql-15"
    exit 1
fi

# Create database if it doesn't exist
echo -e "${YELLOW}Creating database...${NC}"
createdb courtlistener 2>/dev/null || echo "Database already exists or error occurred"

# Setup backend
echo -e "${YELLOW}Setting up backend...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -q -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    cat > .env << EOF
DATABASE_URL=postgresql://localhost:5432/courtlistener
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
ENVIRONMENT=development
EOF
    echo -e "${GREEN}✓ Created .env file${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
python init_db.py

echo -e "${GREEN}✓ Backend setup complete!${NC}"

# Setup frontend
echo -e "${YELLOW}Setting up frontend...${NC}"
cd ../frontend

# Install dependencies
if [ ! -d "node_modules" ]; then
    npm install
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "VITE_API_URL=http://localhost:8000" > .env.local
    echo -e "${GREEN}✓ Created .env.local file${NC}"
else
    echo -e "${GREEN}✓ .env.local file already exists${NC}"
fi

echo -e "${GREEN}✓ Frontend setup complete!${NC}"

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "To start the application:"
echo "  Backend:  cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  Frontend: cd frontend && npm run dev"
echo ""
echo "Backend will be at: http://localhost:8000"
echo "Frontend will be at: http://localhost:3000"

