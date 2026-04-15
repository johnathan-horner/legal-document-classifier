#!/bin/bash

# Seed Regulatory Database Script
# Populates DynamoDB with regulatory requirements data

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Seeding Regulatory Database${NC}"
echo -e "${GREEN}========================================${NC}"

PROJECT_NAME="legal-document-classifier"
TABLE_NAME="$PROJECT_NAME-regulatory-requirements"
REGION=${AWS_DEFAULT_REGION:-"us-east-1"}

# Check if table exists
if ! aws dynamodb describe-table --table-name $TABLE_NAME --region $REGION &> /dev/null; then
    echo -e "${RED}ERROR: DynamoDB table $TABLE_NAME not found${NC}"
    echo "Please deploy the infrastructure first: ./scripts/deploy.sh"
    exit 1
fi

echo -e "${YELLOW}Seeding regulatory requirements data...${NC}"

# Function to put item in DynamoDB
put_regulation() {
    local jurisdiction=$1
    local regulation_id=$2
    local category=$3
    local title=$4
    local description=$5
    local requirements=$6

    aws dynamodb put-item \
        --table-name $TABLE_NAME \
        --region $REGION \
        --item "{
            \"jurisdiction\": {\"S\": \"$jurisdiction\"},
            \"regulation_id\": {\"S\": \"$regulation_id\"},
            \"category\": {\"S\": \"$category\"},
            \"title\": {\"S\": \"$title\"},
            \"description\": {\"S\": \"$description\"},
            \"requirements\": {\"S\": \"$requirements\"},
            \"created_at\": {\"S\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"},
            \"active\": {\"BOOL\": true}
        }" > /dev/null

    echo "  Added: $jurisdiction - $regulation_id"
}

# Federal Regulations
echo -e "${YELLOW}Adding Federal regulations...${NC}"

put_regulation "Federal" "SOX-404" "financial" \
    "Sarbanes-Oxley Section 404 - Internal Controls" \
    "Requires management assessment of internal control over financial reporting" \
    "Annual assessment of internal controls, auditor attestation, management certification"

put_regulation "Federal" "GDPR" "privacy" \
    "General Data Protection Regulation" \
    "EU regulation on data protection and privacy for individuals within the EU" \
    "Data processing consent, right to erasure, privacy by design, data protection officer"

put_regulation "Federal" "CCPA" "privacy" \
    "California Consumer Privacy Act" \
    "California state statute intended to enhance privacy rights and consumer protection" \
    "Consumer right to know, delete, opt-out of sale, non-discrimination"

put_regulation "Federal" "HIPAA" "healthcare" \
    "Health Insurance Portability and Accountability Act" \
    "Federal law protecting sensitive patient health information" \
    "PHI safeguards, breach notification, business associate agreements, patient rights"

put_regulation "Federal" "SOX-302" "financial" \
    "Sarbanes-Oxley Section 302 - Corporate Responsibility" \
    "Requires CEO and CFO certification of financial reports" \
    "Quarterly certifications, internal control disclosure, material changes reporting"

# Delaware Regulations
echo -e "${YELLOW}Adding Delaware regulations...${NC}"

put_regulation "Delaware" "DGCL-141" "corporate" \
    "Delaware General Corporation Law Section 141" \
    "Board of directors powers and duties" \
    "Board meetings, director duties, committee authorization, unanimous consent"

put_regulation "Delaware" "DGCL-220" "corporate" \
    "Delaware General Corporation Law Section 220" \
    "Stockholder inspection rights" \
    "Books and records inspection, proper purpose requirement, scope limitations"

put_regulation "Delaware" "DGCL-271" "corporate" \
    "Delaware General Corporation Law Section 271" \
    "Sale of assets requiring stockholder approval" \
    "Majority stockholder approval for substantial asset sales, appraisal rights"

# New York Regulations
echo -e "${YELLOW}Adding New York regulations...${NC}"

put_regulation "New York" "NYBCL-717" "corporate" \
    "New York Business Corporation Law Section 717" \
    "Duty of directors and basis of liability" \
    "Business judgment rule, duty of care, duty of loyalty, indemnification"

put_regulation "New York" "SHIELD-Act" "privacy" \
    "New York SHIELD Act" \
    "Stop Hacks and Improve Electronic Data Security Act" \
    "Data breach notification, reasonable security measures, private information protection"

put_regulation "New York" "NYFIL-500" "financial" \
    "New York Department of Financial Services Cybersecurity Regulation" \
    "Cybersecurity requirements for financial services companies" \
    "CISO appointment, penetration testing, incident response, third-party oversight"

# California Regulations
echo -e "${YELLOW}Adding California regulations...${NC}"

put_regulation "California" "CCPA-1798.100" "privacy" \
    "California Consumer Privacy Act Section 1798.100" \
    "Consumer right to know about personal information collection" \
    "Disclosure of categories and sources, business purposes, sharing practices"

put_regulation "California" "CCPA-1798.105" "privacy" \
    "California Consumer Privacy Act Section 1798.105" \
    "Consumer right to delete personal information" \
    "Deletion upon request, exceptions for legal compliance, service provider obligations"

put_regulation "California" "SB-1001" "privacy" \
    "California Bot Disclosure Law" \
    "Requirements for automated online accounts" \
    "Bot identification disclosure, clear and conspicuous notice"

# Texas Regulations
echo -e "${YELLOW}Adding Texas regulations...${NC}"

put_regulation "Texas" "TBOC-21.401" "corporate" \
    "Texas Business Organizations Code Section 21.401" \
    "Standard of conduct for directors" \
    "Good faith standard, business judgment rule, conflicts of interest"

put_regulation "Texas" "TIPA" "privacy" \
    "Texas Identity Theft Enforcement and Protection Act" \
    "Personal identifying information protection requirements" \
    "Breach notification, disposal requirements, identity theft prevention"

# Florida Regulations
echo -e "${YELLOW}Adding Florida regulations...${NC}"

put_regulation "Florida" "FSBCA-607.0830" "corporate" \
    "Florida Business Corporation Act Section 607.0830" \
    "General standards of conduct for directors" \
    "Fiduciary duties, business judgment protection, conflict transactions"

put_regulation "Florida" "FPIPL" "privacy" \
    "Florida Personal Information Protection Act" \
    "Personal information security and breach notification" \
    "Security measures, breach notification timeline, consumer notification"

# Contract-specific regulations
echo -e "${YELLOW}Adding contract regulations...${NC}"

put_regulation "Federal" "UCC-2-302" "contract" \
    "Uniform Commercial Code Section 2-302" \
    "Unconscionable contracts or clauses" \
    "Court may refuse enforcement of unconscionable contracts or clauses"

put_regulation "Federal" "NLRA-Section-8" "employment" \
    "National Labor Relations Act Section 8" \
    "Unfair labor practices by employers" \
    "Non-compete restrictions, employee rights protection, union activity"

put_regulation "Federal" "FLSA-Section-7" "employment" \
    "Fair Labor Standards Act Section 7" \
    "Maximum hours and overtime compensation" \
    "40-hour work week, overtime pay requirements, exemption criteria"

# Penalty and liability regulations
echo -e "${YELLOW}Adding penalty and liability regulations...${NC}"

put_regulation "Federal" "15USC-78u-4" "financial" \
    "Private Securities Litigation Reform Act" \
    "Safe harbor for forward-looking statements" \
    "Cautionary language requirements, materiality standards, damages limitations"

put_regulation "Federal" "USC-1681n" "privacy" \
    "Fair Credit Reporting Act - Civil Liability" \
    "Willful noncompliance penalties under FCRA" \
    "Statutory damages range, punitive damages, attorney fees"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Regulatory database seeded successfully!${NC}"
echo -e "${GREEN}========================================${NC}"

# Count total regulations
TOTAL=$(aws dynamodb scan --table-name $TABLE_NAME --region $REGION --select "COUNT" --query "Count" --output text)
echo -e "${YELLOW}Total regulations in database: $TOTAL${NC}"

echo
echo -e "${YELLOW}Sample query - Delaware corporate regulations:${NC}"
aws dynamodb query \
    --table-name $TABLE_NAME \
    --region $REGION \
    --key-condition-expression "jurisdiction = :jurisdiction" \
    --filter-expression "category = :category" \
    --expression-attribute-values '{
        ":jurisdiction": {"S": "Delaware"},
        ":category": {"S": "corporate"}
    }' \
    --projection-expression "regulation_id, title" \
    --output table

echo
echo -e "${GREEN}Database seeding complete!${NC}"