#!/bin/bash
set -e

# Configuration
DOMAIN="${1:-yourdomain.com}"
EMAIL="${2:-admin@yourdomain.com}"

if [ "$DOMAIN" = "yourdomain.com" ]; then
    echo "Usage: ./scripts/setup-ssl.sh <domain> <email>"
    echo "Example: ./scripts/setup-ssl.sh lelivre.example.com admin@example.com"
    exit 1
fi

echo "=== Setting up SSL certificate for $DOMAIN ==="
echo "Email: $EMAIL"
echo ""

# Install certbot
echo "Installing certbot..."
sudo apt-get update
sudo apt-get install -y certbot

# Stop nginx to allow certbot to bind to port 80
echo ""
echo "Stopping nginx..."
docker compose -f docker-compose.prod.yml stop nginx

# Get certificate
echo ""
echo "Requesting SSL certificate from Let's Encrypt..."
echo "This will verify domain ownership via HTTP challenge."
echo ""

sudo certbot certonly --standalone \
  --preferred-challenges http \
  --agree-tos \
  --non-interactive \
  --email $EMAIL \
  -d $DOMAIN -d www.$DOMAIN

# Create SSL directory
echo ""
echo "Setting up SSL certificates for nginx..."
sudo mkdir -p nginx/ssl

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem nginx/ssl/
sudo chmod 644 nginx/ssl/*

# Update nginx.conf to enable HTTPS
echo ""
echo "Updating nginx configuration for HTTPS..."
echo "Please manually edit nginx/nginx.conf:"
echo "1. Uncomment the HTTPS server block"
echo "2. Update server_name to: $DOMAIN www.$DOMAIN"
echo "3. Uncomment the HTTP to HTTPS redirect in the HTTP server block"
echo ""
read -p "Press Enter after you've updated nginx.conf..."

# Restart nginx
echo ""
echo "Starting nginx with SSL..."
docker compose -f docker-compose.prod.yml start nginx

# Verify HTTPS
echo ""
echo "=== SSL Certificate Installed ==="
echo ""
echo "Certificate details:"
sudo certbot certificates
echo ""
echo "Your site should now be available at:"
echo "  https://$DOMAIN"
echo "  https://www.$DOMAIN"
echo ""
echo "Certificate will expire in 90 days."
echo ""
echo "To set up auto-renewal, add this to crontab (sudo crontab -e):"
echo "0 3 1 * * certbot renew --quiet --deploy-hook \"cd $(pwd) && docker compose -f docker-compose.prod.yml restart nginx\""
