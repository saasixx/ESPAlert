#!/bin/bash
# ESPAlert Production Deployment Script for DigitalOcean

set -e

echo "🛡️  ESPAlert: Starting production deployment..."

# 1. Update system
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Docker & Docker Compose if not present
if ! [ -x "$(command -v docker)" ]; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# 3. Install Nginx & Certbot for SSL
if ! [ -x "$(command -v nginx)" ]; then
    echo "🌐 Installing Nginx and Certbot..."
    sudo apt-get install -y nginx certbot python3-certbot-nginx
fi

# 4. Setup Project Directory
PROJECT_DIR="/home/$USER/espalert"
mkdir -p $PROJECT_DIR

# 5. Configure Firewall (UFW)
echo "🔥 Configuring Firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# 6. Setup SSL with Certbot
# Note: Requires domain to be pointing to this IP
echo "SSL SETUP: Ensure espalert.es points to this IP before proceeding."
# sudo certbot --nginx -d espalert.es -d www.espalert.es --non-interactive --agree-tos -m admin@espalert.es

# 7. Start the Stack
echo "🚀 Starting Docker Stack..."
cd $PROJECT_DIR
docker compose -f docker-compose.prod.yml up -d --build

echo "✅ Deployment complete! Check logs with: docker compose -f docker-compose.prod.yml logs -f"
