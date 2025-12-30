# Deployment Reference

## Infrastructure
- EC2: 3.88.211.81, 30GB EBS, Ubuntu 22.04
- Domain: lelivre.trunorth.cloud (HTTPS via Let's Encrypt)
- Services: 5 Docker containers (backend, frontend, nginx, postgres, neo4j)

## Deployment Commands
```bash
git pull origin main
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

## Disk Management
```bash
# Check disk usage
df -h /

# Clean Docker artifacts
docker system prune -af && docker builder prune -af

# Expand filesystem after EBS resize
sudo growpart /dev/xvda 1 && sudo resize2fs /dev/xvda1
```

## Common Issues
1. **Out of disk space** → Run `docker system prune -af`
2. **Frontend build fails** → Copy node_modules from builder (see frontend/Dockerfile)
3. **Services unhealthy** → Check logs: `docker logs <container>`
4. **CORS errors** → Verify `allow_origins=["*"]` in backend/app/main.py

## Service Endpoints
- Health: http://localhost/health
- API: https://lelivre.trunorth.cloud/api/
- Frontend: https://lelivre.trunorth.cloud/

## Monitoring
```bash
docker ps -a
docker logs lelivre-backend --tail 50
curl http://localhost/health
```

## SSH Access
```bash
ssh -i ~/dev/ocean/pem/legail-key.pem ubuntu@3.88.211.81
```

## Recent Deployment Notes
- Expanded EBS volume from 8GB to 30GB (Dec 2024)
- Fixed CORS to allow all origins
- Optimized frontend build to copy node_modules instead of reinstalling
- All critical navigation and auth bugs resolved
