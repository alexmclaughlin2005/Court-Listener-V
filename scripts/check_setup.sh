#!/bin/bash

# Check if local setup is ready
# This script verifies all prerequisites are met

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Checking setup..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js: $NODE_VERSION${NC}"
else
    echo -e "${RED}✗ Node.js not found${NC}"
    exit 1
fi

# Check PostgreSQL
if command -v psql &> /dev/null; then
    if pg_isready -q; then
        echo -e "${GREEN}✓ PostgreSQL is running${NC}"
    else
        echo -e "${YELLOW}⚠ PostgreSQL is installed but not running${NC}"
    fi
else
    echo -e "${YELLOW}⚠ PostgreSQL not found (optional for local dev)${NC}"
fi

# Check backend
if [ -d "backend" ]; then
    if [ -d "backend/venv" ]; then
        echo -e "${GREEN}✓ Backend virtual environment exists${NC}"
    else
        echo -e "${YELLOW}⚠ Backend virtual environment not found${NC}"
    fi
    
    if [ -f "backend/.env" ]; then
        echo -e "${GREEN}✓ Backend .env file exists${NC}"
    else
        echo -e "${YELLOW}⚠ Backend .env file not found${NC}"
    fi
else
    echo -e "${RED}✗ Backend directory not found${NC}"
fi

# Check frontend
if [ -d "frontend" ]; then
    if [ -d "frontend/node_modules" ]; then
        echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend dependencies not installed${NC}"
    fi
    
    if [ -f "frontend/.env.local" ]; then
        echo -e "${GREEN}✓ Frontend .env.local file exists${NC}"
    else
        echo -e "${YELLOW}⚠ Frontend .env.local file not found${NC}"
    fi
else
    echo -e "${RED}✗ Frontend directory not found${NC}"
fi

# Check CSV files
CSV_COUNT=$(find . -maxdepth 1 -name "*.csv" -type f | wc -l)
if [ $CSV_COUNT -gt 0 ]; then
    echo -e "${GREEN}✓ Found $CSV_COUNT CSV file(s)${NC}"
else
    echo -e "${YELLOW}⚠ No CSV files found in project root${NC}"
fi

echo ""
echo -e "${GREEN}✅ Setup check complete!${NC}"

