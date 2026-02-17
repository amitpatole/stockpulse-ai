#!/bin/bash

# TickerPulse AI v3.0 - Stop Script

echo "Stopping TickerPulse AI..."

pkill -f "python.*app.py" 2>/dev/null && echo "  Backend stopped" || echo "  Backend was not running"
pkill -f "python.*backend.app" 2>/dev/null || true
pkill -f "next-server" 2>/dev/null && echo "  Frontend stopped" || echo "  Frontend was not running"
pkill -f "stock_monitor" 2>/dev/null || true
pkill -f "node.*next" 2>/dev/null || true

echo ""
echo "TickerPulse AI stopped."
