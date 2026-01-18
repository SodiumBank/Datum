# Datum Dev Quickstart

## Run everything (Docker)
docker compose up --build

- API: http://localhost:8000/health
- Web: http://localhost:3000
- Ops: http://localhost:3001

## API auth (placeholder)
POST /auth/login with body:
{ "user_id": "u1", "role": "OPS" }

Use returned token as:
Authorization: Bearer <token>

## Jira + Agents
- Import Jira tickets from `jira/datum_jira_import.csv`
- One branch per ticket
- Use `.cursorrules` + `.cursor/rules.md` as agent guardrails
- Agent CI runs builder/verifier/red-team workflows on PRs
