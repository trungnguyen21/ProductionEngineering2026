# Deployment & Rollback

This guide documents the in-place deployment process for the ProductionEngineering2026 application.

## Prerequisites
- Docker and Docker Compose
- A `.env` file in the project root

## Manual Deployment
To deploy the latest code from the current branch:

```bash
./deploy/deploy.sh
```

### Steps
1. **Update**: Pulls the latest code for the active branch.
2. **Build**: Runs `docker compose up -d --build`.
3. **Verify**: Polls `http://localhost:8000/ready` until success or timeout (60s).

## Rollback
If the health check fails, the script will:
1. Log the recent container output.
2. Stop the faulty deployment (`docker compose down`).
3. Exit with an error code.

To manually rollback:
1. Revert the problematic commit: `git revert HEAD`
2. Run the deploy script: `./deploy/deploy.sh`

## Verification
- Status: `curl http://localhost:8000/health`
- Readiness: `curl http://localhost:8000/ready`
- Logs: `docker compose logs -f`
