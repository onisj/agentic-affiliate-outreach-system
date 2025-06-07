#!/bin/bash

# Monitoring stack startup script for Affiliate Outreach System

# Exit on error
set -e

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Please install Docker first."
    exit 1
fi

# Check Docker Compose installation
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Start monitoring stack
echo "Starting monitoring stack..."
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Configure Prometheus
echo "Configuring Prometheus..."
curl -X POST http://localhost:9090/-/reload

# Setup Grafana dashboards
echo "Setting up Grafana dashboards..."
./scripts/monitoring/grafana/setup.sh

echo "Monitoring stack started successfully!"
echo "Prometheus: http://localhost:9090"
echo "Grafana: http://localhost:3000"
echo "Alertmanager: http://localhost:9093" 