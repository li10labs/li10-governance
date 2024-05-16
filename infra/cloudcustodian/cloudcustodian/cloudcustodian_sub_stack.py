from aws_cdk import (
    Stack,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    CfnCondition,
    Fn,
    Stack
)

from constructs import Construct
from cloudcustodian import common

class CloudcustodianSubStack(Stack):

    def add_region_condition(self, role: iam.Role):
        cdk_child_role = role.node.default_child

        if not self.regionCondition:
            self.regionCondition = CfnCondition(self,
                id="region_condition",
                expression=Fn.condition_equals( Stack.of(self).region, "us-east-1"))

        cdk_child_role.cfn_options.condition = self.regionCondition

    def __init__(self, scope: Construct, construct_id: str, bus_arn: str, central_role_arn: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.regionCondition = None

        central_role = iam.Role.from_role_arn(self, "central_governance_role", central_role_arn)

        bus = events.EventBus.from_event_bus_arn(self, id="central_bus", event_bus_arn=bus_arn)


        _rule = events.Rule(self,
            id="rule",
            description="catch local events to be forwarded to the central governance",
            event_pattern=events.EventPattern(
                detail=common.event_pattern_detail,
                detail_type=events.Match.any_of(
                    events.Match.equals_ignore_case("AWS API Call via CloudTrail"),
                    events.Match.equals_ignore_case("AWS Health Event")
                ),
            )
        ).add_target(targets.EventBus(bus))

        inline_policies = {
            'tagging_policies': iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        sid="sagemaker",
                        effect=iam.Effect.ALLOW,
                        actions=["sagemaker:ListTags", "sagemaker:AddTags", "sagemaker:List*", "sagemaker:Describe*"],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="ec2",
                        effect=iam.Effect.ALLOW,
                        actions=["ec2:CreateTags", "ec2:Describe*","ec2:RevokeSecurityGroupIngress"],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="s3",
                        effect=iam.Effect.ALLOW,
                        actions=["s3:ListBucket", "s3:TagResource", "s3:PutJobTagging",
                            "s3:GetBucketTagging", "s3:GetLifecycleConfiguration",
                            "s3:GetBucketNotification", "s3:GetBucketLogging",
                            "s3:GetBucketWebsite", "s3:GetBucketVersioning", "s3:GetReplicationConfiguration",
                            "s3:GetBucketAcl", "s3:GetBucketPolicy", "s3:GetBucketLocation",
                            "s3:PutBucketTagging" ],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="lambda",
                        effect=iam.Effect.ALLOW,
                        actions=["lambda:GetFunction","lambda:TagResource", "lambda:ListTags"],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="rds",
                        effect=iam.Effect.ALLOW,
                        actions=["rds:AddTagsToResource", "rds:ListTagsForResource", "rds:Describe*" ],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="resourcegroup",
                        effect=iam.Effect.ALLOW,
                        actions=["tag:TagResources","tag:GetResources"],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="notify",
                        effect=iam.Effect.ALLOW,
                        actions=["iam:ListAccountAliases", "sqs:sendmessage"],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="elbv2",
                        effect=iam.Effect.ALLOW,
                        actions=['elasticloadbalancing:DescribeTargetGroups', 'elasticloadbalancing:AddTags', 'elasticloadbalancing:DescribeListeners', 'elasticloadbalancing:DescribeLoadBalancers', 'elasticloadbalancing:DescribeLoadBalancerAttributes', 'elasticloadbalancing:DescribeTags', 'elasticloadbalancing:DescribeTargetHealth'],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="glue",
                        effect=iam.Effect.ALLOW,
                        actions=['glue:GetTags', 'glue:TagResource', 'glue:GetJobs'],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="aoss",
                        effect=iam.Effect.ALLOW,
                        actions=['glue:GetTags', 'glue:TagResource', 'glue:GetJobs'],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="dynamo",
                        effect=iam.Effect.ALLOW,
                        actions=["dynamodb:DescribeTable","dynamodb:ListTables","dynamodb:ListGlobalTables","dynamodb:TagResource", "dynamodb:ListTagsOfResource"],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="health",
                        effect=iam.Effect.ALLOW,
                        actions=['aoss:ListTagsForResource', 'aoss:TagResource', 'aoss:ListCollections'],
                        resources=["*"]
                    ),
                ]
            )
        }

        role = iam.Role(self,
                 id="remote_scan_role",
                 description="role used by cloud custodian",
                 role_name=common.target_governance_role_name,
                 inline_policies=inline_policies,
                #  managed_policies=iam.ManagedPolicy.
                 assumed_by=central_role,
        )
        self.add_region_condition(role)

        security_level_1_inline_policies = {
            'governance_level_1_policy': iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        sid="ec2Tag",
                        effect=iam.Effect.ALLOW,
                        actions=["ec2:CreateTags", "ec2:Describe*"],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="notify",
                        effect=iam.Effect.ALLOW,
                        actions=["iam:ListAccountAliases", "sqs:sendmessage"],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="acm",
                        effect=iam.Effect.ALLOW,
                        actions=["acm:List*", "acm:Describe*", "acm:ListTagsForCertificate", "acm:AddTagsToCertificate"],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="s3",
                        effect=iam.Effect.ALLOW,
                        actions=["s3:List*", "s3:Describe*", "s3:GetBucket*"],
                        resources=["arn:aws:s3:::*"]
                    ),
                    iam.PolicyStatement(
                        sid="tag",
                        effect=iam.Effect.ALLOW,
                        actions=['tag:TagResources', 'tag:GetResources'],
                        resources=["*"]
                    ),
                    iam.PolicyStatement(
                        sid="health",
                        effect=iam.Effect.ALLOW,
                        actions=['health:DescribeEvents'],
                        resources=["*"]
                    ),
                ]
            )
        }

        security_level_1_role = iam.Role(self,
                 id="security_level_1_role",
                 description="role used by cloud custodian for low risk actions",
                 role_name=common.target_governance_security_level_1_role,
                 inline_policies=security_level_1_inline_policies,
                 assumed_by=central_role,
        )

        self.add_region_condition(security_level_1_role)
