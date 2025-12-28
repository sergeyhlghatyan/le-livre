# Le Livre - Docker & AWS EC2 Deployment Guide

This guide walks you through deploying Le Livre to AWS EC2 with Docker.

## What Was Created

### Phase 1: Configuration Files ✅
- `frontend/src/lib/api.ts` - API URL now parameterized via environment variables
- `frontend/.env` - Development environment (uses `http://localhost:8000`)
- `frontend/.env.production` - Production environment (uses `/api` proxy)
- `frontend/vite.config.ts` - Added proxy configuration for `/api` route
- `backend/app/config.py` - Removed hardcoded passwords, made CORS configurable
- `.env` - Updated with all required variables
- `.env.production.example` - Template for production deployment

### Phase 2: Docker Configuration ✅
**Backend:**
- `backend/Dockerfile` - Multi-stage Python build (production-optimized)
- `backend/.dockerignore` - Excludes unnecessary files from build

**Frontend:**
- `frontend/Dockerfile` - Multi-stage Node build with SvelteKit
- `frontend/.dockerignore` - Excludes node_modules and build artifacts

**Nginx:**
- `nginx/Dockerfile` - Alpine-based reverse proxy
- `nginx/nginx.conf` - Complete configuration with:
  - API routing (`/api/*` → backend)
  - Frontend routing (`/*` → frontend)
  - Rate limiting
  - Health check endpoint
  - SSL support (commented, ready to enable)

### Phase 3: Docker Compose ✅
- `docker-compose.prod.yml` - Orchestrates all 5 services:
  - PostgreSQL (with pgvector)
  - Neo4j (with APOC plugin)
  - Backend API (FastAPI)
  - Frontend (SvelteKit)
  - Nginx (reverse proxy)

### Phase 4: Deployment Scripts ✅
All scripts are in `scripts/` directory and executable:

1. **setup-ec2.sh** - Initial EC2 instance setup
   - Installs Docker, Git, and tools
   - Creates application directory
   - Prepares system for deployment

2. **deploy.sh** - Application deployment
   - Validates environment configuration
   - Builds and starts Docker containers
   - Shows deployment status

3. **init-databases.sh** - Database initialization
   - Runs PostgreSQL schemas (pgvector, users)
   - Runs Neo4j schema
   - Shows how to create admin user

4. **setup-ssl.sh** - HTTPS configuration
   - Uses Let's Encrypt (certbot)
   - Configures SSL certificates
   - Sets up auto-renewal

5. **health-check.sh** - System monitoring
   - Container status checks
   - Application health checks
   - Database connectivity
   - Resource usage

6. **backup.sh** - Database backups
   - Backs up PostgreSQL and Neo4j
   - Compresses backups
   - Cleans up old backups (7 day retention)

---

## Deployment Steps

### 1. Launch AWS EC2 Instance

**Instance Requirements:**
- Type: `t3.medium` or larger
- OS: Ubuntu 22.04 LTS
- Storage: 30 GB EBS (General Purpose SSD)
- Security Group:
  - Port 80 (HTTP)
  - Port 443 (HTTPS)
  - Port 22 (SSH) - from your IP only

**Optional but Recommended:**
- Allocate Elastic IP for static public IP

### 2. Initial EC2 Setup

SSH into your instance and run the setup script:

```bash
# SSH to your instance
ssh ubuntu@<your-ec2-ip>

# Download setup script
curl -O https://raw.githubusercontent.com/your-repo/main/scripts/setup-ec2.sh
chmod +x setup-ec2.sh

# Run setup
./setup-ec2.sh

# Log out and back in for Docker group changes
exit
ssh ubuntu@<your-ec2-ip>
```

### 3. Clone Repository and Configure

```bash
# Navigate to application directory
cd ~/lelivre

# Clone your repository
git clone <your-repo-url> .

# Create production environment file
cp .env.production.example .env

# Edit with your production values
nano .env
```

**Critical values to change in `.env`:**
```bash
# Generate secure passwords (use openssl rand -base64 32)
POSTGRES_PASSWORD=<secure-password>
NEO4J_PASSWORD=<secure-password>

# Generate JWT secret (use openssl rand -hex 32)
JWT_SECRET_KEY=<64-character-hex-string>

# Add your OpenAI API key
OPENAI_API_KEY=sk-...

# Update CORS origins with your domain
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Set environment to production
ENVIRONMENT=production
```

### 4. Deploy Application

```bash
# Make deploy script executable (if not already)
chmod +x scripts/deploy.sh

# Run deployment
./scripts/deploy.sh
```

This will:
- Build all Docker images
- Start all containers
- Show service status

### 5. Initialize Databases

**First time only:**

```bash
# Run database initialization
./scripts/init-databases.sh
```

**Create admin user:**

```bash
# Use Python to hash password and create user
docker exec lelivre-backend python << 'EOF'
import bcrypt
import psycopg
from app.config import get_settings

settings = get_settings()
hashed_pw = bcrypt.hashpw(b"your_secure_password", bcrypt.gensalt()).decode()

conn = psycopg.connect(
    host=settings.postgres_host,
    port=settings.postgres_port,
    dbname=settings.postgres_db,
    user=settings.postgres_user,
    password=settings.postgres_password
)
cur = conn.cursor()
cur.execute(
    "INSERT INTO users (email, hashed_password, is_superuser) VALUES (%s, %s, %s)",
    ("admin@lelivre.com", hashed_pw, True)
)
conn.commit()
print("Admin user created!")
EOF
```

### 6. Configure Domain (Optional)

**DNS Setup:**

In your domain registrar, create:
```
Type: A
Name: @ (or lelivre)
Value: <your-ec2-elastic-ip>
TTL: 300

Type: CNAME
Name: www
Value: lelivre.yourdomain.com
TTL: 300
```

Wait for DNS propagation (5-30 minutes).

### 7. Set Up HTTPS (Optional but Recommended)

```bash
# Run SSL setup script with your domain
./scripts/setup-ssl.sh lelivre.yourdomain.com admin@yourdomain.com

# Follow the prompts to update nginx.conf
# Then the script will restart nginx with SSL
```

**After SSL setup:**
1. Edit `nginx/nginx.conf`
2. Uncomment the HTTPS server block
3. Update `server_name` with your domain
4. Uncomment the HTTP to HTTPS redirect
5. Restart nginx: `docker compose -f docker-compose.prod.yml restart nginx`

**Set up auto-renewal:**

```bash
# Add to crontab
sudo crontab -e

# Add this line:
0 3 1 * * certbot renew --quiet --deploy-hook "cd /home/ubuntu/lelivre && docker compose -f docker-compose.prod.yml restart nginx"
```

### 8. Verify Deployment

```bash
# Run health check
./scripts/health-check.sh

# Check logs
docker compose -f docker-compose.prod.yml logs -f

# Test the application
curl http://<your-ec2-ip>/health
```

Visit your application:
- HTTP: `http://<your-ec2-ip>`
- HTTPS (if configured): `https://yourdomain.com`

---

## Maintenance

### Daily Backups

Set up automatic daily backups:

```bash
# Add to crontab
crontab -e

# Add this line (runs at 3 AM daily):
0 3 * * * cd /home/ubuntu/lelivre && ./scripts/backup.sh >> /var/log/lelivre-backup.log 2>&1
```

Manual backup:
```bash
./scripts/backup.sh
```

Backups are stored in `~/backups/` by default.

### Monitoring

Run regular health checks:
```bash
./scripts/health-check.sh
```

Check application logs:
```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

### Updates

To deploy code updates:

```bash
# Pull latest code
git pull origin main

# Redeploy (rebuilds containers)
./scripts/deploy.sh
```

### Restart Services

```bash
# Restart all services
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.prod.yml restart frontend
docker compose -f docker-compose.prod.yml restart nginx
```

### Stop Services

```bash
# Stop all services
docker compose -f docker-compose.prod.yml down

# Stop and remove volumes (⚠️ deletes data)
docker compose -f docker-compose.prod.yml down -v
```

---

## Troubleshooting

### Container Won't Start

Check logs:
```bash
docker compose -f docker-compose.prod.yml logs <service-name>
```

Rebuild container:
```bash
docker compose -f docker-compose.prod.yml up -d --build <service-name>
```

### Database Connection Issues

Check database health:
```bash
# PostgreSQL
docker exec lelivre-postgres pg_isready -U lelivre

# Neo4j
docker exec lelivre-neo4j cypher-shell -u neo4j -p <password> "RETURN 1"
```

### Frontend Not Accessible

Check nginx logs:
```bash
docker compose -f docker-compose.prod.yml logs nginx
```

Verify nginx config:
```bash
docker exec lelivre-nginx nginx -t
```

### SSL Certificate Issues

Check certificate status:
```bash
sudo certbot certificates
```

Manually renew:
```bash
sudo certbot renew
```

### Out of Disk Space

Check disk usage:
```bash
df -h
docker system df
```

Clean up Docker:
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes (⚠️ be careful)
docker volume prune

# Full cleanup (⚠️ removes everything not in use)
docker system prune -a --volumes
```

---

## Cost Estimates (AWS)

**Monthly costs:**
- EC2 t3.medium: ~$30/month
- EBS 30GB: ~$3/month
- Data transfer: ~$1-5/month
- **Total: ~$35-40/month**

**For higher traffic:**
- EC2 t3.large: ~$60/month
- Application Load Balancer: ~$16/month
- RDS for PostgreSQL: ~$30/month

---

## Security Checklist

- [ ] Changed all default passwords in `.env`
- [ ] Generated secure JWT secret
- [ ] Updated CORS origins to production domain
- [ ] Configured SSL/HTTPS
- [ ] Restricted SSH access to your IP only
- [ ] Set up automatic backups
- [ ] Enabled SSL auto-renewal
- [ ] Verified health checks pass
- [ ] Tested login with admin account

---

## Architecture Overview

```
Internet
    ↓
Domain (yourdomain.com)
    ↓
AWS EC2 Instance
    ↓
Nginx (Port 80/443)
    ├── /api/* → Backend (Port 8000)
    └── /* → Frontend (Port 3000)
         ↓
    PostgreSQL (Port 5432)
    Neo4j (Port 7687)
```

All services run in Docker containers on a single EC2 instance, orchestrated by Docker Compose.

---

## Support

For issues or questions:
1. Check logs: `./scripts/health-check.sh`
2. Review troubleshooting section above
3. Check GitHub issues: [your-repo-url/issues]
