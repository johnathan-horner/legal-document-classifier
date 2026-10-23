# ADR-004: SQS Queues for Attorney Routing

## Status: Accepted

## Context
We needed a system to route processed legal documents to different attorney queues (auto-file, junior attorney, senior attorney) based on risk scores and classification confidence. The system must handle varying workloads and provide visibility into queue status for workload management.

## Decision
We chose Amazon SQS queues for attorney routing with separate queues for each attorney tier.

## Alternatives Considered
- **Database Flag System**: Update document status in DynamoDB and poll for work
- **SNS Fan-out**: Direct notifications to attorney applications
- **EventBridge**: Event-driven routing with pattern matching
- **Step Functions**: Workflow-based task assignment

## Consequences

### Positive
- **Decoupling**: Document processing and attorney review are completely decoupled
- **Reliability**: SQS guarantees message delivery with retry mechanisms
- **Visibility Timeouts**: Automatic message redelivery if attorney doesn't complete review
- **Dead Letter Queues**: Handle failed or problematic document reviews
- **Queue Depth Monitoring**: Real-time visibility into workload across attorney tiers
- **Scalability**: Handles traffic spikes without losing assignments

### Negative
- **Message Duplication**: Potential for duplicate processing (requires idempotency)
- **Polling Overhead**: Attorney applications must poll queues for work
- **Queue Management**: Need to monitor and manage multiple queue configurations

### Neutral
- **Ordering**: FIFO queues available if strict ordering required
- **Retention**: 14-day message retention for unprocessed items
- **Security**: Standard AWS IAM and encryption capabilities

### Queue Architecture
- **Auto-file Queue**: Low-risk documents for automated processing
- **Junior Attorney Queue**: Medium-risk documents requiring basic review
- **Senior Attorney Queue**: High-risk documents requiring expert analysis
- **Priority Queue**: Critical documents requiring immediate attention

### Implementation Details
- **Message Format**: JSON with document ID, risk score, classification, and attorney briefing
- **Visibility Timeout**: 2 hours for document review completion
- **Max Receive Count**: 3 attempts before sending to dead letter queue
- **Priority Handling**: Separate high-priority queue for urgent documents

### Monitoring and Alerts
- **Queue Depth**: CloudWatch alarms for backlog management
- **Processing Time**: Track time from queue to completion
- **Error Rates**: Monitor dead letter queue activity
- **Attorney Utilization**: Track queue consumption patterns by attorney tier