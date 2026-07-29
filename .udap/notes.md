# api-test-framework — Agent Notes

## Project Summary
FastAPI API Test Framework on AWS EC2 (Ubuntu 22.04, t3.micro, us-east-1).
Blueprint: fastapi-ec2@1.0.0 (monitoring=none).

## Decisions
- Chose in-memory DB (no RDS) — keeps the framework self-contained; the point is testing, not persistence.
- JWT_SECRET_KEY set via set_pipeline_secret after repo push.
- Ansible uses `lookup('env', 'JWT_SECRET_KEY')` and `no_log: true` to write the .env safely.
- Configure stage passes JWT_SECRET_KEY as env var to ansible-playbook.
- inventory.ini written with printf (not heredoc) to avoid cat/EOF heredoc issues in the pipeline.
- Output name fixed: blueprint had `public_ip`, pipeline needs `instance_ip` — patched infra/outputs.tf.
- Old blueprint ansible/playbook.yml deleted; new ansible/site.yml targets `[api]` host group.
- pytest-md-report used for Markdown output; pytest-html for self-contained HTML.
- Postman generator fetches /openapi.json live from the deployed server.
- Response time thresholds: reads 500ms, writes 1000ms, auth (bcrypt) 2000ms.

## Status
- [ ] validate_project
- [ ] create_repo_and_push
- [ ] set_pipeline_secret JWT_SECRET_KEY
- [ ] deploy
