main_stack_account_settings = {
    "account": "123123456789",
    "region": "us-east-1"
}

subStackTargets = {
   "123456789123" : ["us-east-1", "eu-west-1"], # dev
}

event_pattern_detail = {
    "$or": [
    {
      "eventSource": ["sagemaker.amazonaws.com"],
      "eventName": ["CreateModel", "CreateEndpointConfig", "CreateEndpoint", "CreateTrainingJob", "CreateNotebookInstance", "CreateTransformJob"]
    },
    {
      "eventSource": ["ec2.amazonaws.com"],
      "eventName": ["RunInstances", "CreateSnapshot", "CreateVolume","AuthorizeSecurityGroupIngress","CreateSecurityGroup"],
      "errorCode": [{ "exists": False }]
    },
    {
      "eventScopeCode": ["ACCOUNT_SPECIFIC", "PUBLIC"]
    },
    {
      "eventSource": ["s3.amazonaws.com"],
      "eventName": ["CreateBucket"]
    },
    {
      "eventSource": ["rds.amazonaws.com"],
      "eventName": ["CreateDBInstance", "CreateDBCluster", "CreateDBSubnetGroup"]
    },
    {
      "eventSource": ["lambda.amazonaws.com"],
      "eventName": ["CreateFunction20150331"]
    },
    {
      "eventSource": ["elasticloadbalancing.amazonaws.com"],
      "eventName": ["CreateLoadBalancer", "CreateTargetGroup"]
    },
    {
      "eventSource": ["glue.amazonaws.com"],
      "eventName": ["CreateJob"]
    },
    {
      "eventSource": ["aoss.amazonaws.com"],
      "eventName": ["CreateCollection"]
    },
    {
      "eventSource": ["dynamodb.amazonaws.com"],
      "eventName": ["CreateTable"]
    }
    ]
}


central_governance_role_name = "central_governance_role"
target_governance_role_name = "governance_tagging_role"
from_address = "groumail@test.com"

target_governance_security_level_1_role = "governance_security_level_1_role"
