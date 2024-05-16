from aws_cdk import (
    Size,
    Stack,
    # aws_ec2 as ec2,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
    custom_resources,
    aws_secretsmanager as secretsmanager,
    SecretValue,
    aws_ecr as ecr,
    aws_ecs as ecs,
    aws_logs as logs,
    aws_ec2 as ec2,
    aws_ecs_patterns as ecs_patterns,
    aws_applicationautoscaling as aascaling
)

from constructs import Construct

from cloudcustodian import common

class CloudcustodianStack(Stack):


    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # TODO remove hardcoded vpc id
        vpc = ec2.Vpc.from_lookup(self,
            id="vpc",
            # is_default=True,
            vpc_id="vpc-0de496dd67345739e",
            
            region=self.region)

        # TODO fix email subjet
        # TODO automate jinja template validation in pipeline
        # TODO process the policies so that they have variables from the ecs task definition
        # TODO tag resources Team, Git hash etc...
        # TODO pipeline to use less permissions
        # TODO pass vars to policies?
        # TODO add resource policy to SES
        # TODO enforce PR review

        inline_policies = {
            'tagging_policies': iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        sid="assumeRemoteGovernanceRole",
                        effect=iam.Effect.ALLOW,
                        actions=["sts:AssumeRole"],
                        resources=[f"arn:aws:iam::*:role/{common.target_governance_role_name}",
                                   f"arn:aws:iam::*:role/{common.target_governance_security_level_1_role}"]
                    ),
                    iam.PolicyStatement(
                        sid="lambdaExecution",
                        effect=iam.Effect.ALLOW,
                        actions=["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
                        resources=["*"]
                    ),
                ]
            )
        }

        role = iam.Role(self,
                 id="central_governance_role",
                 description="role used by the governance lambda",
                 role_name=common.central_governance_role_name,
                 inline_policies=inline_policies,
                 assumed_by= iam.CompositePrincipal(
                     iam.ServicePrincipal("lambda.amazonaws.com"),
                     iam.ServicePrincipal("ecs-tasks.amazonaws.com"))
        )

        # to be accessed by sub stacks
        self.role_arn = role.role_arn

        cloud_custodian_lambda = _lambda.Function(self, "cloud_custodian_tagger",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="main.run",
            code=_lambda.Code.from_asset("lambda-code"),
            timeout=Duration.seconds(30),
            role=role
            )

        bus = events.EventBus(
            self, 
            id="cloud-custodian-bus",
            event_bus_name="cloud-custodian-bus"
        )

        # to be accessed by the substack
        self.bus_arn = bus.event_bus_arn

        self.org_id = custom_resources.AwsCustomResource(self, "DescribeOrganizationCustomResource",
            install_latest_aws_sdk=True,
            on_update=custom_resources.AwsSdkCall(
                service='organizations',
                action= 'describeOrganization',
                physical_resource_id= custom_resources.PhysicalResourceId.of('Organization')
                ),
            policy=custom_resources.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(resources=["*"], actions=["organizations:DescribeOrganization"], effect=iam.Effect.ALLOW)
            ])).get_response_field("Organization.Id")

        bus_policy = {
                "Sid": "AllowAllAccountsFromOrganizationToPutEvents",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "events:PutEvents",
                "Resource": bus.event_bus_arn,
                "Condition": {
                    "StringEquals": {
                        "aws:PrincipalOrgID": self.org_id
                    }
                }
            }

        bus.add_to_resource_policy(iam.PolicyStatement.from_json(bus_policy))

        _cross_account_rule = events.Rule(self,
            id="cross_account_rule",
            description="catch remote cloudtrail events from other account to be analyzed by Cloud Custodian",
            event_pattern=events.EventPattern(
                detail=common.event_pattern_detail,
                detail_type=events.Match.equals_ignore_case("AWS API Call via CloudTrail"),
            ),
            event_bus=bus
        ).add_target(targets.LambdaFunction(handler=cloud_custodian_lambda))

        # add secret TODO move to mailer stack?
        secret = secretsmanager.Secret(self, "governance",
            description="store configuration and secrets for Cloud Custodian"
        )
        self.secret_arn = secret.secret_arn

        # container
        repo = ecr.Repository(self, id="ecr-repo",
            image_scan_on_push=True,
            repository_name="governance",
            )


        ecs_role = iam.Role(self,
            id="central_governance_role_ecs",
            description="role used by the governance ecs",
            role_name=f"{common.central_governance_role_name}_ecs",
            managed_policies=[iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")],
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )

        task_def = ecs.FargateTaskDefinition(self, id="ecs-td",
            runtime_platform=ecs.RuntimePlatform(
                operating_system_family=ecs.OperatingSystemFamily.LINUX, 
                cpu_architecture=ecs.CpuArchitecture.X86_64),
            cpu=256, memory_limit_mib=512,
            task_role=role,
            execution_role=ecs_role)

        task_def.add_container(
            id="td-container",
            image=ecs.ContainerImage.from_registry(repo.repository_uri),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="governance",
                log_retention=logs.RetentionDays.ONE_MONTH
        ))

        cluster = ecs.Cluster(self, "FargateCPCluster",
            vpc=vpc,
            enable_fargate_capacity_providers=True
        )

        ecs_patterns.ScheduledFargateTask(self,
            id="scheduled_task",
            cluster=cluster,
            schedule=aascaling.Schedule.expression("rate(1 day)"),
            scheduled_fargate_task_definition_options=ecs_patterns.ScheduledFargateTaskDefinitionOptions(
                task_definition=task_def),
            rule_name="daily_scan"
        )