# Python REST API on AWS EC2

A FastAPI service running behind nginx on a dedicated Ubuntu EC2 instance, deployed by a fully rendered CI/CD pipeline with Terraform-managed infrastructure.

## What you inherit

- EC2 + Elastic IP + security group as Terraform under `infra/`
- Ansible configuration: venv, systemd unit, nginx reverse proxy
- CloudWatch CPU alarm (module group `monitoring`)
- Health-checked verify stage

## What the Build Agent tailors

- Your API routes under `app/`
- Instance size (`instance_type`), region
- Monitoring on/off via the `monitoring` module group

## Deploy behaviour

The pipeline provisions infrastructure with Terraform (state lives in the
platform-managed bucket, keyed by project), configures the server, and verifies
`/health` before the run goes green. Destroy tears down everything the template
created — the repository and its configuration survive for redeploys.
