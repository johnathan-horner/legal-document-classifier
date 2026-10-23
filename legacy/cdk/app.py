#!/usr/bin/env python3
"""
AWS CDK app for Legal Document Classification and Compliance Risk Scoring System.
"""
import aws_cdk as cdk
from constructs import Construct

from stacks.document_processing_stack import DocumentProcessingStack
from stacks.agent_stack import AgentStack
from stacks.api_stack import ApiStack
from stacks.monitoring_stack import MonitoringStack
from stacks.security_stack import SecurityStack


class LegalClassifierApp(cdk.App):
    """CDK App for the legal document classifier system."""

    def __init__(self):
        super().__init__()

        # Environment configuration
        env = cdk.Environment(
            account=self.node.try_get_context("account"),
            region=self.node.try_get_context("region") or "us-east-1"
        )

        # Project configuration
        project_name = "legal-document-classifier"

        # Security stack (foundational)
        security_stack = SecurityStack(
            self, f"{project_name}-security",
            project_name=project_name,
            env=env
        )

        # Document processing stack (S3, Textract, SageMaker, DynamoDB)
        doc_processing_stack = DocumentProcessingStack(
            self, f"{project_name}-document-processing",
            project_name=project_name,
            kms_key=security_stack.kms_key,
            env=env
        )

        # Agent processing stack (ECS Fargate, SQS, SNS)
        agent_stack = AgentStack(
            self, f"{project_name}-agents",
            project_name=project_name,
            document_bucket=doc_processing_stack.document_bucket,
            dynamo_tables=doc_processing_stack.dynamo_tables,
            sagemaker_endpoint_name=doc_processing_stack.sagemaker_endpoint_name,
            kms_key=security_stack.kms_key,
            env=env
        )

        # API stack (API Gateway, Lambda, Cognito)
        api_stack = ApiStack(
            self, f"{project_name}-api",
            project_name=project_name,
            agent_cluster=agent_stack.ecs_cluster,
            agent_task_definition=agent_stack.task_definition,
            dynamo_tables=doc_processing_stack.dynamo_tables,
            document_bucket=doc_processing_stack.document_bucket,
            kms_key=security_stack.kms_key,
            env=env
        )

        # Monitoring stack (CloudWatch, CloudTrail)
        monitoring_stack = MonitoringStack(
            self, f"{project_name}-monitoring",
            project_name=project_name,
            api_gateway=api_stack.api_gateway,
            ecs_cluster=agent_stack.ecs_cluster,
            sagemaker_endpoint_name=doc_processing_stack.sagemaker_endpoint_name,
            dynamo_tables=doc_processing_stack.dynamo_tables,
            env=env
        )

        # Add dependencies
        doc_processing_stack.add_dependency(security_stack)
        agent_stack.add_dependency(doc_processing_stack)
        api_stack.add_dependency(agent_stack)
        monitoring_stack.add_dependency(api_stack)

        # Add common tags
        cdk.Tags.of(self).add("Project", project_name)
        cdk.Tags.of(self).add("Environment", self.node.try_get_context("environment") or "dev")
        cdk.Tags.of(self).add("ManagedBy", "CDK")


if __name__ == "__main__":
    app = LegalClassifierApp()
    app.synth()