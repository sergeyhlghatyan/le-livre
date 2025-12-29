# Le Livre - Production Deployment Documentation

## Overview

Le Livre is deployed as a Docker-containerized application on AWS EC2 with the following components:

- **Domain**: lelivre.trunorth.cloud (HTTPS enabled)
- **Instance Type**: EC2 t3.medium (Ubuntu 22.04 LTS)
- **Container Orchestration**: Docker Compose v5.0.0
- **Status**: All services running and healthy

---

## 1. Docker Compose Configuration

### Service Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy               │
│              (Port 80/443, SSL Enabled)              │
└────────────────┬──────────────────────┬──────────────┘
                 │                      │
        ┌────────▼────────┐     ┌───────▼─────────┐
        │   Backend API   │     │     Frontend    │
        │  (Port 8000)    │     │   (Port 3000)   │
        │   FastAPI       │     │   SvelteKit     │
        └────────┬────────┘     └─────────────────┘
                 │
        ┌────────┴──────────┬──────────────────┐
        │                   │                  │
    ┌───▼──┐          ┌──────▼────┐      ┌────▼──┐
    │  PG  │          │   Neo4j   │      │ logs  │
    │  5432│          │   7687    │      │       │
    └──────┘          └───────────┘      └───────┘
```

### Container Specifications

| Service | Image | Container | Port | Network | Restart Policy |
|---------|-------|-----------|------|---------|-----------------|
| PostgreSQL | pgvector/pgvector:pg16 | lelivre-postgres | 5432 | lelivre-net | unless-stopped |
| Neo4j | neo4j:5.15 | lelivre-neo4j | 7687 | lelivre-net | unless-stopped |
| Backend | Local build (Python 3.12) | lelivre-backend | 8000 | lelivre-net | unless-stopped |
| Frontend | Local build (Node 20) | lelivre-frontend | 3000 | lelivre-net | unless-stopped |
| Nginx | Local build (Alpine) | lelivre-nginx | 80/443 | lelivre-net | unless-stopped |

### Health Checks

- **PostgreSQL**: `pg_isready -U lelivre` (10s interval, 5 retries)
- **Neo4j**: `cypher-shell -u neo4j -p <pass> 'RETURN 1'` (10s interval, 5 retries)
- **Backend**: HTTP GET to `http://localhost:8000/` (30s interval, 3 retries, 10s startup)
- **Frontend**: Node HTTP check on port 3000 (30s interval, 3 retries, 10s startup)
- **Nginx**: Health endpoint check on `/health` (30s interval)

### Persistent Volumes

- `postgres_data:/var/lib/postgresql/data` - PostgreSQL persistent data
- `neo4j_data:/data` - Neo4j persistent data
- `neo4j_logs:/logs` - Neo4j logs
- `./nginx/nginx.conf:/etc/nginx/nginx.conf:ro` - Nginx config (read-only)
- `./nginx/ssl:/etc/nginx/ssl:ro` - SSL certificates (read-only)
- `./nginx/logs:/var/log/nginx` - Nginx logs
- `./data/schemas:/docker-entrypoint-initdb.d:ro` - PostgreSQL initialization schemas

---

## 2. Nginx Configuration

### HTTP Server Block (Port 80)

```nginx
server {
    listen 80;
    server_name lelivre.trunorth.cloud;

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Redirect HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}
```

### HTTPS Server Block (Port 443)

```nginx
server {
    listen 443 ssl;
    http2 on;
    server_name lelivre.trunorth.cloud;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript
               application/javascript application/json;
}
```

### Rate Limiting

- **API routes**: 10 req/s (burst: 20)
- **General routes**: 30 req/s (burst: 50)

### Routing Configuration

**Backend Routing:**
```nginx
location /api/ {
    rewrite ^/api/(.*) /$1 break;
    proxy_pass http://backend;
    # Timeouts: 60s for connect/send/read
    # WebSocket support enabled
}
```

**Frontend Routing:**
```nginx
location / {
    proxy_pass http://frontend;
    # WebSocket support enabled for HMR
}
```

---

## 3. SSL/TLS Certificate Setup

### Certificate Details

- **Location**: `/etc/nginx/ssl/` (inside nginx container)
- **Certificate**: `fullchain.pem` (3,619 bytes)
- **Private Key**: `privkey.pem` (1,704 bytes)
- **Authority**: Let's Encrypt
- **Domain**: lelivre.trunorth.cloud

### Current Status

- **Status**: Active and enforcing HTTPS
- **HTTP → HTTPS redirect**: Enabled
- **TLS Version**: 1.2 and 1.3 only
- **HSTS**: 1 year max-age with includeSubDomains

### Auto-Renewal Setup

Crontab entry for automatic renewal:
```bash
0 3 1 * * certbot renew --quiet --deploy-hook "cd ~/lelivre && docker compose -f docker-compose.prod.yml restart nginx"
```

---

## 4. Environment Variables

### Required Configuration Variables

See `.env.production.example` for a complete template with all required variables.

**Critical variables:**
- `OPENAI_API_KEY` - Required for embeddings and chat functionality
- `POSTGRES_PASSWORD` - Must be changed from default
- `NEO4J_PASSWORD` - Must be changed from default
- `JWT_SECRET_KEY` - Generate with `openssl rand -hex 32`
- `ENVIRONMENT` - Set to "production" in production

### Development vs. Production Differences

**Development (.env):**
```bash
VITE_API_BASE_URL=http://localhost:8000
ENVIRONMENT=development
```

**Production (.env):**
```bash
VITE_API_BASE_URL=/api
ENVIRONMENT=production
```

---

## 5. Dockerfile Configurations

### Backend Dockerfile

**Location**: `backend/Dockerfile`

**Key Features:**
- Python 3.12 slim base image
- Non-root user for security (UID 1000)
- Health check included
- Global package installation (no virtual environment needed)
- Current image size: 849 MB

### Frontend Dockerfile

**Location**: `frontend/Dockerfile`

**Key Features:**
- Multi-stage build (builder + production)
- Node 20 Alpine base
- Non-root user for security (UID 1000)
- Health check included
- Current image size: 428 MB (optimized)

### Nginx Dockerfile

**Location**: `nginx/Dockerfile`

**Key Features:**
- Nginx Alpine base
- Minimal configuration
- Health check included
- Current image size: 81.2 MB

---

## 6. Database Schemas

### PostgreSQL Schema

**Main Table**: `provision_embeddings`
- Stores provision text with vector embeddings (1536 dimensions)
- Unique constraint on (provision_id, year)
- Indexes for vector similarity search and hierarchical queries

**Additional Tables**:
- `definition_usages` - Tracks definition references between provisions
- `users` - User authentication and authorization

**Schema Files**: `data/schemas/pgvector.sql`, `data/schemas/users.sql`

### Neo4j Schema

**Node Types**:
- `Section` - Represents USC sections
- `Provision` - Represents individual provisions

**Relationship Types**:
- `PARENT_OF` - Hierarchical structure
- `REFERENCES` - Cross-references between provisions
- `CONTAINS` - Section containment
- `AMENDED_FROM` - Temporal changes (Phase 0)
- `USES_DEFINITION` - Definition usage (Phase 0)
- `SEMANTICALLY_SIMILAR` - AI-discovered similarity (Phase 0)

**Schema File**: `data/schemas/neo4j.cypher`

---

## 7. Deployment Scripts

All scripts located in `scripts/` directory:

### 1. setup-ec2.sh
Initial EC2 instance setup - installs Docker, Git, and configures system

### 2. deploy.sh
Application deployment and updates - builds containers and starts services

### 3. init-databases.sh
One-time database initialization - creates schemas and provides admin user instructions

### 4. setup-ssl.sh
HTTPS certificate setup with Let's Encrypt - usage: `./scripts/setup-ssl.sh domain email`

### 5. health-check.sh
System health monitoring - checks containers, databases, disk space, and logs

### 6. backup.sh
Database backup automation - backs up both PostgreSQL and Neo4j with 7-day retention

---

## 8. System Information

### EC2 Instance

- **OS**: Ubuntu 22.04 LTS (Linux kernel 6.8.0-1040-aws)
- **Instance Type**: t3.medium
- **Docker**: 29.1.3
- **Docker Compose**: 5.0.0
- **Architecture**: x86_64

### Docker Images

| Image | Tag | Size |
|-------|-----|------|
| lelivre-backend | latest | 849 MB |
| lelivre-frontend | latest | 428 MB |
| lelivre-nginx | latest | 81.2 MB |
| pgvector/pgvector | pg16 | 723 MB |
| neo4j | 5.15 | 799 MB |

---

## 9. Security Configuration

### Security Headers (Nginx)

```nginx
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
```

### Best Practices

- SSL certificates stored in nginx/ssl/ (gitignored)
- All containers run as non-root users
- Environment variables separated from code
- Rate limiting enabled on all endpoints
- Database passwords required to be changed from defaults
- JWT secrets must be generated uniquely

---

## 10. Local Development Setup

### Development Files

- `docker-compose.yml` - Local development databases only
- `start.sh` - Starts backend (uvicorn) and frontend (Vite) with auto-reload
- `stop.sh` - Stops development servers

### Development URLs

- Frontend: http://localhost:5174
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432
- Neo4j Browser: http://localhost:7474

---

## 11. Deployment Checklist

### Pre-Deployment Security

- [ ] Change all default passwords in `.env`
- [ ] Generate new JWT secret with `openssl rand -hex 32`
- [ ] Set ENVIRONMENT=production
- [ ] Verify OPENAI_API_KEY is valid
- [ ] Review nginx.conf for correct domain name

### Deployment Steps

1. [ ] Clone repository to EC2
2. [ ] Create `.env` from `.env.production.example`
3. [ ] Update `.env` with production values
4. [ ] Run `./scripts/deploy.sh`
5. [ ] Run `./scripts/init-databases.sh` (first time only)
6. [ ] Create admin user
7. [ ] Configure DNS records (A record pointing to EC2 IP)
8. [ ] Run `./scripts/setup-ssl.sh domain email`
9. [ ] Verify nginx HTTPS configuration
10. [ ] Run `./scripts/health-check.sh`
11. [ ] Test HTTPS access
12. [ ] Set up backup automation in crontab

### Maintenance

- Daily backups (automated via crontab)
- Weekly health checks
- Monthly certificate renewal verification
- Monitor disk space (30GB allocation)
- Review logs for errors

---

## 12. Cost Estimates (AWS)

### Current Setup

- EC2 t3.medium: ~$30/month
- EBS 30GB (gp2): ~$3/month
- Data transfer: ~$1-5/month
- **Total**: ~$35-40/month

### For Higher Traffic

- EC2 t3.large: ~$60/month
- RDS PostgreSQL: ~$30/month
- Application Load Balancer: ~$16/month
- **Total**: ~$106+/month

---

## 13. Access Information

- **Public URL**: https://lelivre.trunorth.cloud
- **EC2 IP**: 3.88.211.81
- **SSH Access**: `ssh -i ~/dev/ocean/pem/legail-key.pem ubuntu@3.88.211.81`
- **Neo4j Browser**: Not exposed externally (internal Docker network only)
- **PostgreSQL**: Not exposed externally (internal Docker network only)

---

## 14. Troubleshooting

### Container Won't Start

```bash
# Check container logs
docker compose -f docker-compose.prod.yml logs --tail=50 <service-name>

# Restart specific service
docker compose -f docker-compose.prod.yml restart <service-name>

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build <service-name>
```

### SSL Certificate Issues

```bash
# Verify certificate files exist
ls -l nginx/ssl/

# Test certificate manually
openssl s_client -connect lelivre.trunorth.cloud:443

# Renew certificate manually
sudo certbot renew
```

### Database Connection Issues

```bash
# Check PostgreSQL
docker exec lelivre-postgres pg_isready -U lelivre

# Check Neo4j
docker exec lelivre-neo4j cypher-shell -u neo4j -p <password> 'RETURN 1'
```

### Out of Disk Space

```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -af --volumes

# Check Docker disk usage
docker system df
```

---

## 15. References

- **Docker Compose**: `docker-compose.prod.yml`
- **Nginx Config**: `nginx/nginx.conf`
- **PostgreSQL Schema**: `data/schemas/pgvector.sql`
- **Neo4j Schema**: `data/schemas/neo4j.cypher`
- **Deployment Scripts**: `scripts/`
- **Environment Template**: `.env.production.example`
- **Project Documentation**: `CLAUDE.md`
- **Deployment Issues**: `DEPLOYMENT_ISSUES.md`
