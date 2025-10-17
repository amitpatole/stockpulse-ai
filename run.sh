#!/bin/bash

# Stock News Monitor - Startup Script
# This script runs both the monitor and dashboard as background processes

echo "🚀 Starting Enhanced Stock News Monitor..."

# Kill any existing instances
pkill -f stock_monitor
pkill -f dashboard.py

# Start the enhanced stock monitor in background
echo "📊 Starting news monitoring service (Enhanced with 10+ sources)..."
nohup /usr/bin/python3.12 stock_monitor_enhanced.py > monitor.log 2>&1 &
MONITOR_PID=$!
echo "Monitor started with PID: $MONITOR_PID"

# Give it a moment to initialize
sleep 2

# Start the dashboard in background
echo "🌐 Starting web dashboard..."
nohup /usr/bin/python3.12 dashboard.py > dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "Dashboard started with PID: $DASHBOARD_PID"

echo ""
echo "✅ Enhanced Stock News Monitor is now running!"
echo ""
echo "📊 Monitor PID: $MONITOR_PID (logs: monitor.log)"
echo "🌐 Dashboard PID: $DASHBOARD_PID (logs: dashboard.log)"
echo ""
echo "📰 Data Sources: Google News, Yahoo Finance, Seeking Alpha,"
echo "                MarketWatch, Benzinga, Finviz, Reddit,"
echo "                StockTwits, Twitter/X, Trump Posts/Truth Social"
echo ""
echo "🌐 Access the dashboard at: http://localhost:5000"
echo ""
echo "To stop the monitor, run: ./stop.sh"
echo "To view logs, run: tail -f monitor.log dashboard.log"
echo ""
