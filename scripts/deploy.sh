#!/bin/bash
set -e

echo "=== Deploying Le Livre to Production ==="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create .env from .env.production.example:"
    echo "  cp .env.production.example .env"
    echo "  nano .env  # Edit with your production values"
    exit 1
fi

# Validate critical environment variables
echo "Validating environment variables..."
if ! grep -q "^POSTGRES_PASSWORD=" .env || grep -q "CHANGE-ME" .env; then
    echo "Error: Please update passwords and secrets in .env file!"
    exit 1
fi

# Pull latest code (if using git)
if [ -d ".git" ]; then
    echo "Pulling latest code from git..."
    git pull origin main || echo "Warning: Could not pull from git. Continuing with local files..."
fi

# Stop existing containers
echo "Stopping existing containers..."
docker compose -f docker-compose.prod.yml down || true

# Build and start containers
echo "Building and starting containers..."
docker compose -f docker-compose.prod.yml up -d --build

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
echo "This may take a minute..."
sleep 30

# Check service status
echo ""
echo "=== Service Status ==="
docker compose -f docker-compose.prod.yml ps

echo ""
echo "=== Container Health ==="
docker ps --format "table {{.Names}}\t{{.Status}}"

# Get public IP if on EC2
if command -v curl &> /dev/null; then
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")
    echo ""
    echo "=== Deployment Complete ==="
    echo "Application should be available at: http://$PUBLIC_IP"
    echo ""
    echo "Next steps:"
    echo "1. Run ./scripts/init-databases.sh to initialize databases (first time only)"
    echo "2. Test the application by visiting http://$PUBLIC_IP"
    echo "3. Set up SSL with ./scripts/setup-ssl.sh (if you have a domain)"
else
    echo ""
    echo "=== Deployment Complete ==="
    echo "Next steps:"
    echo "1. Run ./scripts/init-databases.sh to initialize databases (first time only)"
    echo "2. Test the application"
    echo "3. Set up SSL with ./scripts/setup-ssl.sh (if you have a domain)"
fi
