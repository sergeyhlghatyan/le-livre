#!/bin/bash
set -e

echo "=== Setting up Le Livre on AWS EC2 ==="

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "Installing Docker..."
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add current user to docker group
echo "Adding user to docker group..."
sudo usermod -aG docker $USER

# Install Git
echo "Installing Git..."
sudo apt-get install -y git

# Install useful tools
echo "Installing additional tools..."
sudo apt-get install -y htop vim wget curl unzip

# Create application directory
echo "Creating application directory..."
mkdir -p ~/lelivre

echo ""
echo "=== Docker installed successfully ==="
echo ""
echo "IMPORTANT: You must log out and log back in for Docker group changes to take effect."
echo ""
echo "After logging back in, clone your repository to ~/lelivre:"
echo "  cd ~/lelivre"
echo "  git clone <your-repo-url> ."
echo ""
echo "Then create a production .env file from the template:"
echo "  cp .env.production.example .env"
echo "  nano .env  # Edit with your production values"
echo ""
echo "Finally, run the deployment script:"
echo "  ./scripts/deploy.sh"
