"""
Document Processing Stack - S3, Textract, SageMaker, DynamoDB
"""
import aws_cdk as cdk
from aws_cdk import (
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_sagemaker as sagemaker,
    aws_iam as iam,
    aws_kms as kms,
    aws_s3_notifications as s3_notifications,
    aws_lambda as lambda_,
)
from constructs import Construct
from typing import Dict


class DocumentProcessingStack(cdk.Stack):
    """Stack for document processing infrastructure."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        project_name: str,
        kms_key: kms.Key,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.project_name = project_name
        self.kms_key = kms_key

        # Create S3 buckets
        self.document_bucket = self._create_document_bucket()
        self.model_artifacts_bucket = self._create_model_artifacts_bucket()

        # Create DynamoDB tables
        self.dynamo_tables = self._create_dynamo_tables()

        # Create SageMaker endpoint
        self.sagemaker_endpoint_name = self._create_sagemaker_endpoint()

        # Create IAM roles
        self.textract_role = self._create_textract_role()
        self.sagemaker_role = self._create_sagemaker_role()

    def _create_document_bucket(self) -> s3.Bucket:
        """Create S3 bucket for document storage."""
        bucket = s3.Bucket(
            self, "DocumentBucket",
            bucket_name=f"{self.project_name}-documents-{self.account}",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="archive-old-documents",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.STANDARD_IA,
                            transition_after=cdk.Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=cdk.Duration.days(90)
                        )
                    ]
                )
            ],
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True
        )

        # Add bucket policy for secure access
        bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="DenyUnSecureCommunications",
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=["s3:*"],
                resources=[bucket.bucket_arn, bucket.arn_for_objects("*")],
                conditions={
                    "Bool": {
                        "aws:SecureTransport": "false"
                    }
                }
            )
        )

        # Output bucket name
        cdk.CfnOutput(
            self, "DocumentBucketName",
            value=bucket.bucket_name,
            description="S3 bucket for document storage"
        )

        return bucket

    def _create_model_artifacts_bucket(self) -> s3.Bucket:
        """Create S3 bucket for model artifacts."""
        bucket = s3.Bucket(
            self, "ModelArtifactsBucket",
            bucket_name=f"{self.project_name}-model-artifacts-{self.account}",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="cleanup-old-models",
                    enabled=True,
                    expiration=cdk.Duration.days(365)  # Keep models for 1 year
                )
            ],
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True
        )

        return bucket

    def _create_dynamo_tables(self) -> Dict[str, dynamodb.Table]:
        """Create DynamoDB tables for the application."""
        tables = {}

        # Documents table
        tables['documents'] = dynamodb.Table(
            self, "DocumentsTable",
            table_name=f"{self.project_name}-documents",
            partition_key=dynamodb.Attribute(
                name="document_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=True,
            removal_policy=cdk.RemovalPolicy.RETAIN,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )

        # Attorney queue table
        tables['attorney_queue'] = dynamodb.Table(
            self, "AttorneyQueueTable",
            table_name=f"{self.project_name}-attorney-queue",
            partition_key=dynamodb.Attribute(
                name="queue_level",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="priority_score",
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=True,
            removal_policy=cdk.RemovalPolicy.RETAIN
        )

        # Add GSI for timestamp-based queries
        tables['attorney_queue'].add_global_secondary_index(
            index_name="timestamp-index",
            partition_key=dynamodb.Attribute(
                name="queue_level",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Regulatory requirements table
        tables['regulatory_requirements'] = dynamodb.Table(
            self, "RegulatoryRequirementsTable",
            table_name=f"{self.project_name}-regulatory-requirements",
            partition_key=dynamodb.Attribute(
                name="jurisdiction",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="regulation_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=True,
            removal_policy=cdk.RemovalPolicy.RETAIN
        )

        # Add GSI for category-based lookups
        tables['regulatory_requirements'].add_global_secondary_index(
            index_name="category-index",
            partition_key=dynamodb.Attribute(
                name="category",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="jurisdiction",
                type=dynamodb.AttributeType.STRING
            )
        )

        # Feedback table
        tables['feedback'] = dynamodb.Table(
            self, "FeedbackTable",
            table_name=f"{self.project_name}-feedback",
            partition_key=dynamodb.Attribute(
                name="document_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="feedback_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            point_in_time_recovery=True,
            removal_policy=cdk.RemovalPolicy.RETAIN
        )

        # Output table names
        for name, table in tables.items():
            cdk.CfnOutput(
                self, f"{name.title()}TableName",
                value=table.table_name,
                description=f"DynamoDB table name for {name}"
            )

        return tables

    def _create_sagemaker_endpoint(self) -> str:
        """Create SageMaker endpoint for model inference."""
        endpoint_name = f"{self.project_name}-classifier-endpoint"

        # Create SageMaker execution role
        sagemaker_role = iam.Role(
            self, "SageMakerExecutionRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess")
            ]
        )

        # Grant access to model artifacts bucket
        self.model_artifacts_bucket.grant_read(sagemaker_role)

        # Grant KMS permissions
        self.kms_key.grant_encrypt_decrypt(sagemaker_role)

        # Note: In practice, you would create the model, endpoint config, and endpoint
        # For this example, we're defining the endpoint name that will be created
        # during model training/deployment

        cdk.CfnOutput(
            self, "SageMakerEndpointName",
            value=endpoint_name,
            description="SageMaker endpoint for document classification"
        )

        return endpoint_name

    def _create_textract_role(self) -> iam.Role:
        """Create IAM role for Textract access."""
        role = iam.Role(
            self, "TextractRole",
            assumed_by=iam.ServicePrincipal("textract.amazonaws.com"),
            inline_policies={
                "TextractS3Access": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:GetObjectVersion"
                            ],
                            resources=[self.document_bucket.arn_for_objects("*")]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "kms:Decrypt",
                                "kms:GenerateDataKey"
                            ],
                            resources=[self.kms_key.key_arn]
                        )
                    ]
                )
            }
        )

        return role

    def _create_sagemaker_role(self) -> iam.Role:
        """Create IAM role for SageMaker access."""
        role = iam.Role(
            self, "SageMakerRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess")
            ],
            inline_policies={
                "SageMakerS3Access": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "s3:ListBucket"
                            ],
                            resources=[
                                self.model_artifacts_bucket.bucket_arn,
                                self.model_artifacts_bucket.arn_for_objects("*")
                            ]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "kms:Decrypt",
                                "kms:GenerateDataKey",
                                "kms:DescribeKey"
                            ],
                            resources=[self.kms_key.key_arn]
                        )
                    ]
                )
            }
        )

        return role