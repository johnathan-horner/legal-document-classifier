# ADR-005: Amazon Bedrock Claude for LLM Reasoning

## Status: Accepted

## Context
We needed an LLM service for clause analysis, regulatory compliance checking, and briefing generation that provides high-quality reasoning while maintaining data privacy and compliance requirements for government legal document processing.

## Decision
We chose Amazon Bedrock with Claude 3 Sonnet for LLM-powered agent reasoning.

## Alternatives Considered
- **Anthropic Claude API**: Direct API access to Claude models
- **OpenAI GPT-4**: Industry standard LLM with broad capabilities
- **AWS SageMaker JumpStart**: Self-hosted open source models
- **Azure OpenAI**: Microsoft's hosted OpenAI service

## Consequences

### Positive
- **AWS IAM Integration**: Native authentication without API key management
- **Data Privacy**: Data stays within AWS environment, never sent to Anthropic directly
- **FedRAMP Eligible**: Meets government compliance requirements
- **Cost Predictability**: AWS billing integration with detailed usage tracking
- **Regional Control**: Data processing stays within specified AWS regions
- **VPC Support**: Private network connectivity for enhanced security

### Negative
- **Model Selection**: Limited to Bedrock-supported models vs direct API access
- **Feature Lag**: New model features may arrive later than direct APIs
- **Vendor Lock-in**: Deeper integration with AWS ecosystem

### Neutral
- **Performance**: Similar latency and quality to direct Anthropic API
- **Cost**: Comparable pricing to direct API calls (~$15/1M tokens)
- **Rate Limits**: Similar throttling behavior with enterprise scaling options

### Security Benefits
- **Encryption**: All data encrypted in transit and at rest with AWS KMS
- **Audit Trail**: CloudTrail logging for all LLM interactions
- **Network Isolation**: VPC endpoints eliminate public internet traffic
- **Access Control**: Granular IAM policies for different agent types

### Model Selection Rationale
- **Claude 3 Sonnet**: Balanced performance and cost for legal analysis
- **Context Length**: 200K tokens handles long legal documents
- **Reasoning Quality**: Excellent performance on complex legal reasoning tasks
- **Safety**: Strong constitutional AI training reduces harmful outputs

### Usage Patterns
- **Clause Analysis**: 5-15K tokens input, 1-2K tokens output per document
- **Regulatory Compliance**: 10-20K tokens input, 2-3K tokens output
- **Briefing Generation**: 15-25K tokens input, 1-3K tokens output
- **Expected Monthly Cost**: $1,200 for 10K documents/month processing