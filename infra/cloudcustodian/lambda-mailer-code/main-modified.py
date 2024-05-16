# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0
import logging
from c7n_mailer import handle

import boto3
import os
import json

if len(logging.getLogger().handlers) > 0:
    print("pre-configured")
    logging.getLogger().setLevel(logging.DEBUG)
else:
    logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger('custodian.mailer')
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.DEBUG, format=log_format)
logging.getLogger('botocore').setLevel(logging.INFO)

secret_arn = os.environ['SECRET_ARN']
print("loading secret: ", secret_arn)

# load once, then reuse cached value until Lambda reloads
sm_client = boto3.client('secretsmanager')
kwargs = {'SecretId': secret_arn}
response = sm_client.get_secret_value(**kwargs)
secrets = json.loads(response['SecretString'])

def dispatch(event, context):
    logger.debug(event)

    if event and "Records" in event:
        batch_item_failures = []
        sqs_batch_response = {}

        return handle.start_c7n_mailer(logger, sqs_trigger_messages=event["Records"], secrets=secrets)

    return handle.start_c7n_mailer(logger, secrets=secrets)
