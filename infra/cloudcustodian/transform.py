#!/usr/bin/env python3
# Copyright Li10
# SPDX-License-Identifier: Apache-2.0
import argparse
import logging
import os
import json
import yaml
import c7n.policy
from c7n.config import Config


def setup_logging(log_level):
    """
    Configure logging level.
    """
    if log_level:
        logging.basicConfig(level=log_level)
    return logging.getLogger(__name__)


def parse_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="Combine Cloud Custodian policy files.")
    parser.add_argument("--policy-dir", default="../../policies/event-based", help="Path to directory containing policy files")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")
    return parser.parse_args()


def load_policy_file(policy_file, vars):
    """
    Load policy file with given variables.
    """
    config = Config.empty()
    return c7n.policy.load(options=config, path=policy_file, validate=True, vars=vars)

def merge_policies(policy_files, vars):
    """
    Merge policies from multiple files into one.
    """
    combined_policies = []
    for policy_file in policy_files:
        policy = load_policy_file(policy_file, vars)
        renamed_filters_actions = f"filters_actions_{os.path.splitext(os.path.basename(policy_file))[0]}"
        for p in policy:
            if 'vars' in p.data:
                p.data['vars'][renamed_filters_actions] = p.data['vars'].pop('filters_actions', {})
        combined_policies.extend(policy)
    return combined_policies



def transform(policy_dir, vars, log_level=None):
    """
    Combine policy files, rename anchors, and output JSON policies.
    """
    logging = setup_logging(log_level)

    policy_files = [os.path.join(policy_dir, f) for f in os.listdir(policy_dir) if os.path.isfile(os.path.join(policy_dir, f))]
    if not policy_files:
        logging.error("No policy files found in the directory.")
        return

    combined_policies = merge_policies(policy_files, vars)
    json_policies = json.dumps(
        {'execution-options': {},
         'policies': [p.data for p in combined_policies]}, indent=2)

    logging.debug("Combined policies:")
    print(json_policies)

if __name__ == "__main__":
    args = parse_arguments()

    external_policy_vars = {
        "NOTIFY_EMAIL": "groupmail@test.com",
        "NOTIFY_SLACK": "slack://#alerts",
        "INSTANT_SQS_QUEUE": "https://sqs.us-east-1.amazonaws.com/123456789123/CloudcustodianStackMailer-mailerqueue723rw-X9WSmXGNE3cb",
        "MEMBER_ROLE": "arn:aws:iam::{account_id}:role/governance_tagging_role",
        "MONGODB": "mongodb://"
    }

    transform(args.policy_dir, external_policy_vars, log_level=args.log_level)
