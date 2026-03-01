#!/bin/bash
# scripts/deploy.sh
# Quickly updates and deploys the entire stack via Docker Compose

set -e

echo "=> Fetching latest master branch..."
git fetch origin main
git pull origin main

echo "=> Ensuring environment setup..."
if [ ! -f .env ]; then
  echo "ERROR: Please create a .env file containing the required environment variables (e.g. DATABASE_URL, etc.)."
  exit 1
fi

echo "=> Building and starting all services (Detached)..."
# Pull latest dependencies if any remote containers exist, build local code
docker compose up -d --build

echo "=> Cleaning up unused Docker images..."
docker image prune -a -f

echo "=> Deployment completed successfully!"
