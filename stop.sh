#!/bin/bash

# Stop Stock News Monitor

echo "🛑 Stopping Stock News Monitor..."

pkill -f stock_monitor
pkill -f dashboard.py

echo "✅ Stock News Monitor stopped"
