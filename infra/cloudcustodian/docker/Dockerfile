FROM --platform=linux/amd64 amazonlinux:2023

RUN dnf update expat --releasever 2023.4.20240401 -y
RUN dnf update rpm --releasever 2023.4.20240319 -y

RUN yum upgrade
RUN yum update

RUN yum install -y python pip aws-cli
RUN python --version && pip --version && aws --version

USER 1000
WORKDIR /governance
RUN python -m venv .venv && source .venv/bin/activate && pip install c7n c7n-org && pip list

RUN sed -i 's/logging.getLogger(\x27botocore\x27).setLevel(logging.ERROR)/logging.getLogger("botocore").setLevel(logging.INFO)/g' .venv/lib/python3.9/site-packages/c7n_org/cli.py
RUN sed -i 's/logging.getLogger(\x27s3transfer\x27).setLevel(logging.WARNING)/logging.getLogger("s3transfer").setLevel(logging.INFO)/g' .venv/lib/python3.9/site-packages/c7n_org/cli.py
RUN sed -i 's/logging.getLogger(\x27custodian.s3\x27).setLevel(logging.ERROR)/logging.getLogger("custodian.s3").setLevel(logging.INFO)/g' .venv/lib/python3.9/site-packages/c7n_org/cli.py

RUN source .venv/bin/activate && custodian version
RUN aws --version

COPY --chown=1000 ./policies/schedule-based/ /governance/policy/
COPY --chown=1000 ./infra/cloudcustodian/docker/entrypoint.sh /governance/entrypoint.sh
RUN chmod +x /governance/entrypoint.sh

ENTRYPOINT ["/governance/entrypoint.sh"]