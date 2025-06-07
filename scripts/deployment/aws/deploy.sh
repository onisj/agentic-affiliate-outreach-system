#!/bin/bash

# AWS deployment script for Affiliate Outreach System

# Exit on error
set -e

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Check AWS CLI installation
if ! command -v aws &> /dev/null; then
    echo "AWS CLI not found. Installing..."
    curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
    sudo installer -pkg AWSCLIV2.pkg -target /
    rm AWSCLIV2.pkg
fi

# Check AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
    exit 1
fi

# Build Docker image
echo "Building Docker image..."
docker build -t affiliate-outreach-system .

# Tag image for ECR
echo "Tagging image for ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker tag affiliate-outreach-system:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/affiliate-outreach-system:latest

# Push to ECR
echo "Pushing to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/affiliate-outreach-system:latest

# Update ECS service
echo "Updating ECS service..."
aws ecs update-service --cluster affiliate-outreach-cluster --service affiliate-outreach-service --force-new-deployment

echo "Deployment completed successfully!" 