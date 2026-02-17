#!/bin/bash

# TickerPulse AI v3.0 - Startup Script
# Starts backend (Flask) and frontend (Next.js)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  TickerPulse AI v3.0 - Starting..."
echo "========================================"

# Kill any existing instances
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true
pkill -f "stock_monitor" 2>/dev/null || true

sleep 1

# Create logs directory
mkdir -p logs

# ----------------------------------------
# Start Backend (Flask API)
# ----------------------------------------
echo ""
echo "[1/2] Starting Flask backend..."

if [ ! -f backend/app.py ]; then
    echo "ERROR: backend/app.py not found!"
    exit 1
fi

cd "$SCRIPT_DIR"
nohup python3 -m backend.app > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"
echo "  API: http://localhost:5000"
echo "  Logs: logs/backend.log"

# Wait for backend to start
sleep 3

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "  WARNING: Backend may have failed to start. Check logs/backend.log"
fi

# ----------------------------------------
# Start Frontend (Next.js)
# ----------------------------------------
echo ""
echo "[2/2] Starting Next.js frontend..."

if [ -d frontend ] && [ -f frontend/package.json ]; then
    cd "$SCRIPT_DIR/frontend"

    # Install dependencies if needed
    if [ ! -d node_modules ]; then
        echo "  Installing frontend dependencies..."
        npm install --silent
    fi

    # Build if no .next directory
    if [ ! -d .next ]; then
        echo "  Building frontend (first run)..."
        npm run build
    fi

    nohup npm run start > "$SCRIPT_DIR/logs/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo "  Frontend PID: $FRONTEND_PID"
    echo "  Dashboard: http://localhost:3000"
    echo "  Logs: logs/frontend.log"
else
    echo "  Frontend not found. Using legacy dashboard at http://localhost:5000/legacy"
    FRONTEND_PID="N/A"
fi

cd "$SCRIPT_DIR"

# ----------------------------------------
# Summary
# ----------------------------------------
echo ""
echo "========================================"
echo "  TickerPulse AI v3.0 is running!"
echo "========================================"
echo ""
echo "  Backend API:  http://localhost:5000"
echo "  Health check: http://localhost:5000/api/health"
echo "  SSE stream:   http://localhost:5000/api/stream"
if [ "$FRONTEND_PID" != "N/A" ]; then
echo "  Dashboard:    http://localhost:3000"
else
echo "  Dashboard:    http://localhost:5000/legacy (legacy mode)"
fi
echo ""
echo "  Backend PID:  $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo ""
echo "  To stop: ./stop.sh"
echo "  To view logs: tail -f logs/backend.log logs/frontend.log"
echo ""
