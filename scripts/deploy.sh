#!/bin/bash

# Legal Document Classification System - Deployment Script
# This script deploys the complete AWS infrastructure using CDK

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Legal Document Classification System${NC}"
echo -e "${GREEN}AWS CDK Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Configuration
PROJECT_NAME="legal-document-classifier"
REGION=${AWS_DEFAULT_REGION:-"us-east-1"}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ENVIRONMENT=${ENVIRONMENT:-"dev"}

echo -e "${YELLOW}Configuration:${NC}"
echo "  Project Name: $PROJECT_NAME"
echo "  AWS Account: $ACCOUNT_ID"
echo "  Region: $REGION"
echo "  Environment: $ENVIRONMENT"
echo

# Verify prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI is not installed${NC}"
    exit 1
fi

# Check CDK CLI
if ! command -v cdk &> /dev/null; then
    echo -e "${RED}ERROR: AWS CDK CLI is not installed${NC}"
    echo "Please install: npm install -g aws-cdk"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: Python 3 is not installed${NC}"
    exit 1
fi

# Verify AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}ERROR: AWS credentials not configured${NC}"
    echo "Please run: aws configure"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites verified${NC}"
echo

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Navigate to CDK directory
cd cdk

# Install CDK dependencies
echo -e "${YELLOW}Installing CDK dependencies...${NC}"
pip install -r requirements.txt

# Set CDK context
echo -e "${YELLOW}Setting CDK context...${NC}"
cdk context --set account=$ACCOUNT_ID
cdk context --set region=$REGION
cdk context --set environment=$ENVIRONMENT

# Bootstrap CDK (if not already done)
echo -e "${YELLOW}Bootstrapping CDK environment...${NC}"
cdk bootstrap aws://$ACCOUNT_ID/$REGION

# Synthesize templates
echo -e "${YELLOW}Synthesizing CloudFormation templates...${NC}"
cdk synth

# Ask for confirmation
echo -e "${YELLOW}Ready to deploy the following stacks:${NC}"
echo "  1. $PROJECT_NAME-security"
echo "  2. $PROJECT_NAME-document-processing"
echo "  3. $PROJECT_NAME-agents"
echo "  4. $PROJECT_NAME-api"
echo "  5. $PROJECT_NAME-monitoring"
echo

read -p "Do you want to proceed with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled${NC}"
    exit 0
fi

# Deploy stacks in order
echo -e "${GREEN}Starting deployment...${NC}"

echo -e "${YELLOW}Deploying security stack...${NC}"
cdk deploy $PROJECT_NAME-security --require-approval never

echo -e "${YELLOW}Deploying document processing stack...${NC}"
cdk deploy $PROJECT_NAME-document-processing --require-approval never

echo -e "${YELLOW}Deploying agent stack...${NC}"
cdk deploy $PROJECT_NAME-agents --require-approval never

echo -e "${YELLOW}Deploying API stack...${NC}"
cdk deploy $PROJECT_NAME-api --require-approval never

echo -e "${YELLOW}Deploying monitoring stack...${NC}"
cdk deploy $PROJECT_NAME-monitoring --require-approval never

# Return to project root
cd ..

# Seed regulatory database
echo -e "${YELLOW}Seeding regulatory database...${NC}"
./scripts/seed-regulatory-db.sh

# Generate sample data
echo -e "${YELLOW}Generating sample legal documents...${NC}"
python data/synthetic/generator.py

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"

# Output important information
echo -e "${YELLOW}Important URLs and Information:${NC}"
echo
echo "API Gateway URL:"
aws cloudformation describe-stacks \
    --stack-name $PROJECT_NAME-api \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text || echo "  (Check AWS Console)"

echo
echo "Cognito User Pool ID:"
aws cloudformation describe-stacks \
    --stack-name $PROJECT_NAME-api \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
    --output text || echo "  (Check AWS Console)"

echo
echo "S3 Document Bucket:"
aws cloudformation describe-stacks \
    --stack-name $PROJECT_NAME-document-processing \
    --query 'Stacks[0].Outputs[?OutputKey==`DocumentBucketName`].OutputValue' \
    --output text || echo "  (Check AWS Console)"

echo
echo "CloudWatch Dashboard:"
echo "  https://$REGION.console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards:name=$PROJECT_NAME-dashboard"

echo
echo -e "${GREEN}Next Steps:${NC}"
echo "1. Train and deploy the ML model:"
echo "   python model/training/train_model.py"
echo
echo "2. Run integration tests:"
echo "   ./scripts/integration-test.sh"
echo
echo "3. Create Cognito users for testing:"
echo "   aws cognito-idp admin-create-user --user-pool-id <USER_POOL_ID> --username testuser"
echo
echo "4. Upload test documents to S3 bucket for processing"
echo

echo -e "${GREEN}Deployment complete!${NC}"