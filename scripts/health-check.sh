#!/bin/bash

echo "=== Le Livre Health Check ==="
echo "Timestamp: $(date)"
echo ""

# Check if containers are running
echo "=== Container Status ==="
docker compose -f docker-compose.prod.yml ps
echo ""

# Check container health
echo "=== Container Health Details ==="
docker ps --filter "name=lelivre-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Check application health endpoint
echo "=== Application Health Endpoint ==="
if curl -f http://localhost/health 2>/dev/null; then
    echo "✓ Health endpoint responding"
else
    echo "✗ Health endpoint failed"
fi
echo ""

# Check backend API
echo "=== Backend API Check ==="
if docker exec lelivre-backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/').read()" 2>/dev/null; then
    echo "✓ Backend API responding"
else
    echo "✗ Backend API failed"
fi
echo ""

# Check frontend
echo "=== Frontend Check ==="
if docker exec lelivre-frontend node -e "require('http').get('http://localhost:3000/', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})" 2>/dev/null; then
    echo "✓ Frontend responding"
else
    echo "✗ Frontend failed"
fi
echo ""

# Check database connections
echo "=== Database Checks ==="
if docker exec lelivre-postgres pg_isready -U lelivre 2>/dev/null; then
    echo "✓ PostgreSQL ready"
else
    echo "✗ PostgreSQL not ready"
fi

if docker exec lelivre-neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-lelivre123}" "RETURN 1" 2>/dev/null | grep -q "1"; then
    echo "✓ Neo4j ready"
else
    echo "✗ Neo4j not ready"
fi
echo ""

# Check disk usage
echo "=== Disk Usage ==="
df -h / | grep -v Filesystem
echo ""

# Check Docker disk usage
echo "=== Docker Disk Usage ==="
docker system df
echo ""

# Check Docker volumes
echo "=== Docker Volumes ==="
docker volume ls --filter "name=lelivre"
echo ""

# Check recent logs for errors
echo "=== Recent Backend Errors (last 10 lines) ==="
docker compose -f docker-compose.prod.yml logs --tail=10 backend | grep -i error || echo "No recent errors"
echo ""

# Memory usage
echo "=== Memory Usage ==="
free -h
echo ""

# Container resource usage
echo "=== Container Resource Usage ==="
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
echo ""

echo "=== Health Check Complete ==="
