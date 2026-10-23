# ADR-002: LangGraph for Multi-Agent Orchestration

## Status: Accepted

## Context
We needed to orchestrate multiple AI agents (classification, clause analysis, regulatory compliance, risk scoring) in a workflow that supports conditional routing, parallel execution, and complex decision trees based on confidence scores and document types.

## Decision
We chose LangGraph to orchestrate our multi-agent pipeline with state management and conditional routing.

## Alternatives Considered
- **Simple Chain**: Sequential execution of agents with basic error handling
- **AWS Step Functions**: AWS-native workflow orchestration
- **Celery**: Distributed task queue with Redis/RabbitMQ
- **Custom DAG**: Home-built directed acyclic graph execution engine

## Consequences

### Positive
- **Conditional Routing**: Easy to route based on classification confidence (<0.5 → senior attorney)
- **Parallel Execution**: Clause analysis and regulatory crossref run simultaneously
- **State Management**: Shared state across agents with automatic serialization
- **Fan-out/Fan-in**: Multiple agents can process in parallel and converge results
- **Visual Debugging**: Graph visualization for complex workflow debugging
- **Python Native**: Integrates seamlessly with existing Python ML stack

### Negative
- **Learning Curve**: New framework with specific patterns and concepts
- **ECS Overhead**: Requires containerized deployment vs simpler Lambda chains
- **Memory Usage**: Stateful execution requires more memory than stateless functions

### Neutral
- **Performance**: Similar to custom orchestration but with built-in optimizations
- **Monitoring**: Requires custom metrics vs AWS Step Functions native monitoring
- **Error Handling**: Good error handling but requires explicit configuration

### Architecture Benefits
- **Scalability**: ECS Fargate auto-scaling based on queue depth
- **Fault Tolerance**: Individual agent failures don't crash entire pipeline
- **Flexibility**: Easy to add new agents or modify routing logic
- **Testing**: Individual agents can be tested in isolation

### Implementation Details
- **State Schema**: Typed state objects with document, predictions, and routing info
- **Node Types**: Transform nodes for agents, conditional nodes for routing
- **Error Handling**: Retry policies and dead letter queues for failed documents
- **Monitoring**: Custom CloudWatch metrics for agent performance and latency