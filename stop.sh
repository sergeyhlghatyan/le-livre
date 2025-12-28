#!/bin/bash

# Le Livre - Stop Backend and Frontend
echo "🛑 Stopping Le Livre services..."

# Kill uvicorn
pkill -f "uvicorn app.main:app" && echo "✅ Backend stopped"

# Kill vite
pkill -f "vite dev" && echo "✅ Frontend stopped"

echo ""
echo "All services stopped."
