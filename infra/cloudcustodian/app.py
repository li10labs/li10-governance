#!/usr/bin/env python3
# Copyright Li10
# SPDX-License-Identifier: Apache-2.0
import os
import aws_cdk as cdk
from cloudcustodian.cloudcustodian_stack import CloudcustodianStack
from cloudcustodian.cloudcustodian_sub_stack import CloudcustodianSubStack
from cloudcustodian.cloudcustodian_mailer import CloudcustodianStackMailer

import cloudcustodian.common as common

app = cdk.App()

tags = {
    # "git.commit": os.environ["SHA"],
    # "git.job_id": os.environ["JOB"]
    }


main_stack = CloudcustodianStack(
    app,
    "CloudcustodianStack",
    env=cdk.Environment(account=common.main_stack_account_settings["account"], region=common.main_stack_account_settings["region"]),
    tags=tags)

CloudcustodianStackMailer(
    app,
    "CloudcustodianStackMailer",
    env=cdk.Environment(account=common.main_stack_account_settings["account"], region=common.main_stack_account_settings["region"]),
    org_id=main_stack.org_id,
    secret_arn=main_stack.secret_arn)

for account in common.subStackTargets:
    for region in common.subStackTargets[account]:
        CloudcustodianSubStack(
            app,
            f"CloudcustodianSubStack-{account}-{region}",
            env=cdk.Environment(account=account, region=region),
            bus_arn=main_stack.bus_arn,
            central_role_arn=main_stack.role_arn)

cdk.Tags.of(app).add("git.repo_url", os.environ["GIT"])

app.synth()
