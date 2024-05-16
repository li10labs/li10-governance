# Copyright The Cloud Custodian Authors.
# SPDX-License-Identifier: Apache-2.0
"""
Lambda entry point
"""
import boto3
import json
import os

from .sqs_queue_processor import MailerSqsQueueProcessor


def config_setup(config=None, logger=None, secrets=None):
    task_dir = os.environ.get("LAMBDA_TASK_ROOT")
    os.environ["PYTHONPATH"] = "%s:%s" % (task_dir, os.environ.get("PYTHONPATH", ""))
    if not config:
        with open(os.path.join(task_dir, "config.json")) as fh:
            config = json.load(fh)
    if "http_proxy" in config:
        os.environ["http_proxy"] = config["http_proxy"]
    if "https_proxy" in config:
        os.environ["https_proxy"] = config["https_proxy"]

    # overwrite slack token with value from Secrets Manager
    try:
        config["slack_token"]=secrets["MAILER_SLACK_TOKEN"]
        logger.debug("slack token updated")
    except:
        logger.warning("slack token not updated")

    try:
        config["mongodb_uri"]=secrets["MAILER_MONGODB_URI"]
        logger.debug("mongodb_uri updated")
    except:
        logger.warning("mongodb_uri not updated")

    try:
        config["queue_url"]=os.environ["QUEUE_URL"]
        logger.debug("queue url updated")
    except:
        logger.warning("queue url not updated")

    try:
        config["from_address"]=os.environ["FROM_ADDRESS"]
        logger.debug("from_address updated")
    except:
        logger.warning("from_address not updated")

    try:
        config["role"]=os.environ["MAILER_ROLE_ARN"]
        logger.debug("role updated")
    except:
        logger.warning("role not updated")
    try:
        config["mongodb_collection"]=os.environ["MAILER_MONGODB_COLLECTION"]
        logger.debug("mongodb_collection updated")
    except:
        logger.warning("mongodb_collection not updated")

    return config


def start_c7n_mailer(logger, config=None, parallel=False, sqs_trigger_messages=None, secrets=None):
    try:
        session = boto3.Session()
        if not config:
            config = config_setup(logger=logger, secrets=secrets)
        logger.info("c7n_mailer starting...")
        mailer_sqs_queue_processor = MailerSqsQueueProcessor(config, session, logger)
        mailer_sqs_queue_processor.run(parallel, sqs_trigger_messages=sqs_trigger_messages)
    except Exception as e:
        logger.exception("Error starting mailer MailerSqsQueueProcessor(). \n Error: %s \n" % (e))
