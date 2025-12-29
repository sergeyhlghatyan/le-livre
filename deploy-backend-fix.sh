#!/bin/bash
set -e

echo "Deploying backend fix to EC2..."

# SSH to EC2 and deploy
ssh ubuntu@3.88.211.81 << 'REMOTE'
    cd ~/lelivre
    
    # Pull latest changes
    git pull origin main
    
    # Restart backend container
    docker-compose -f docker-compose.prod.yml restart backend
    
    echo "Backend restarted successfully!"
    
    # Wait a few seconds for backend to start
    sleep 5
    
    # Check backend status
    docker-compose -f docker-compose.prod.yml logs --tail=20 backend
REMOTE

echo ""
echo "Deployment complete!"
echo "Testing the fixed endpoint..."

# Test the endpoint
curl -s "https://lelivre.trunorth.cloud/api/provisions/provision/%2Fus%2Fusc%2Ft18%2Fs922%2Fa%2F1/2024" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'✅ Success! Got provision: {data.get(\"provision_id\", \"N/A\")}')" || echo "❌ Still failing"
