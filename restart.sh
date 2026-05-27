#!/bin/bash
cd /mnt/nvme/leaf

# Kill existing backend
pkill -9 -f "uvicorn app.main:app" 2>/dev/null && echo "Backend stopped" || echo "Backend not running"

# Kill existing frontend  
pkill -9 -f "vite.*leaf/frontend" 2>/dev/null && echo "Frontend stopped" || echo "Frontend not running"
fuser -k 8001/tcp 2>/dev/null
fuser -k 3001/tcp 2>/dev/null

sleep 2

# Start backend
cd /mnt/nvme/leaf/backend
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 > /mnt/nvme/leaf/server.log 2>&1 &
echo "Backend started (PID: $!)"

# Start frontend
cd /mnt/nvme/leaf/frontend
nohup npm run dev -- --host > /mnt/nvme/leaf/frontend.log 2>&1 &
echo "Frontend started (PID: $!)"

sleep 3
echo ""
echo "=== Status ==="
ss -tlnp | grep -E '8001|3001|3000' || echo "No services detected"
