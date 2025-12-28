#!/bin/bash

# Le Livre - Start Backend and Frontend
# This script starts both services and displays their logs

echo "🚀 Starting Le Livre..."
echo ""

# Colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Create log directory
mkdir -p logs

# Start Backend
echo -e "${BLUE}[Backend]${NC} Starting on http://localhost:8000"
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 2

# Start Frontend
echo -e "${GREEN}[Frontend]${NC} Starting on http://localhost:5174"
cd frontend
npm run dev -- --host 0.0.0.0 --port 5174 > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 3

echo ""
echo "✅ Services started!"
echo "   Backend PID: $BACKEND_PID"
echo "   Frontend PID: $FRONTEND_PID"
echo ""
echo "📋 Logs:"
echo "   Backend:  logs/backend.log"
echo "   Frontend: logs/frontend.log"
echo ""
echo "Press Ctrl+C to stop tailing logs (services will keep running)"
echo "To stop services: kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Tail both logs
tail -f logs/backend.log logs/frontend.log
