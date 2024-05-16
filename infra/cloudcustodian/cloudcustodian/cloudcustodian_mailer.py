from aws_cdk import (
    Stack,
    aws_sqs as sqs,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
    aws_lambda_event_sources as event_sources,
    aws_ses as ses
)

from constructs import Construct

from cloudcustodian import common

class CloudcustodianStackMailer(Stack):

    def __init__(self, scope: Construct, construct_id: str, org_id: str, secret_arn: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ses_identity = ses.EmailIdentity(self, "ses_email_notification", identity=ses.Identity.email(common.from_address))

        inline_policies = {
            'read_sqs': iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        sid="sqs",
                        effect=iam.Effect.ALLOW,
                        actions=["sqs:ReceiveMessage"],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="secret",
                        effect=iam.Effect.ALLOW,
                        actions=["secretsmanager:GetSecretValue"],
                        resources=[secret_arn]
                    ),
                    iam.PolicyStatement(
                        sid="ses",
                        effect=iam.Effect.ALLOW,
                        actions=["ses:SendRawEmail"],
                        resources=[ses_identity.email_identity_arn]
                    )
                ]
            )
        }

        role = iam.Role(self,
            id="cloud_custodian_mailer_lambda",
            description="give permissions to the cloud custodian lambda to send notifications",
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")],
            inline_policies=inline_policies,
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )
        
        queue = sqs.Queue(self, "mailer_queue", enforce_ssl=True)

        queue.add_to_resource_policy(iam.PolicyStatement(
            actions=["sqs:*"],
            effect=iam.Effect.ALLOW,
            resources=["*"],
            principals=[role] ))

        queue.add_to_resource_policy(iam.PolicyStatement(
            actions=["sqs:*"],
            effect=iam.Effect.ALLOW,
            resources=["*"],
            principals=[iam.AnyPrincipal()],
            conditions={
                "StringEquals": {
                "aws:PrincipalOrgID": org_id
                }
            }
        ))

        mailer_lambda = _lambda.Function(self,
            id="mailer_lambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="main.dispatch",
            code=_lambda.Code.from_asset("lambda-mailer-code"),
            timeout=Duration.seconds(30),
            role=role,
            environment={
                "SECRET_ARN": secret_arn,
                "QUEUE_URL": queue.queue_url,
                "FROM_ADDRESS": common.from_address,
                "MAILER_ROLE_ARN":role.role_arn
                }
            )

        mailer_lambda.add_event_source(event_sources.SqsEventSource(queue))