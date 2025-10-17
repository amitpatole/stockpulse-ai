#!/bin/bash
# StockPulse AI - Setup Script
# This script automates the initial setup of StockPulse AI

set -e  # Exit on error

echo "=========================================="
echo "   StockPulse AI - Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    echo -e "${GREEN}✓ Python 3.12 found${NC}"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    PYTHON_CMD="python3"
    echo -e "${YELLOW}⚠ Using Python $PYTHON_VERSION (Python 3.12+ recommended)${NC}"
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.12+${NC}"
    exit 1
fi

# Check pip
echo -e "${BLUE}Checking pip...${NC}"
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo -e "${RED}✗ pip not found. Please install pip${NC}"
    exit 1
fi
echo -e "${GREEN}✓ pip found${NC}"

# Install dependencies
echo ""
echo -e "${BLUE}Installing dependencies...${NC}"
$PYTHON_CMD -m pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Initialize database
echo ""
echo -e "${BLUE}Initializing database with default stocks...${NC}"
$PYTHON_CMD stock_manager.py
echo -e "${GREEN}✓ Database initialized${NC}"

# Make scripts executable
echo ""
echo -e "${BLUE}Making scripts executable...${NC}"
chmod +x run.sh
if [ -f "stop.sh" ]; then
    chmod +x stop.sh
fi
echo -e "${GREEN}✓ Scripts are now executable${NC}"

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}   Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Default stocks added to database:"
echo "  • TSLA  • AAPL  • MSFT  • NVDA  • GOOGL"
echo "  • AMZN  • META  • NFLX  • AMD   • COIN"
echo ""
echo "Next steps:"
echo "  1. Start the system:"
echo "     ${BLUE}./run.sh${NC}"
echo ""
echo "  2. Access the dashboard:"
echo "     ${BLUE}http://localhost:5000${NC}"
echo ""
echo "  3. Add/remove stocks from the 'Manage Stocks' tab"
echo ""
echo "For more information, see README.md"
echo ""
