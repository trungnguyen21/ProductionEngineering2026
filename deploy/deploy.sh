#!/usr/bin/env bash
# deploy.sh — In-place deployment orchestrator
# Run from the repo root: ./deploy/deploy.sh
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$DEPLOY_DIR")"

# ── Helpers ──────────────────────────────────────────────────────────
log()  { echo "[deploy] $(date '+%H:%M:%S') $*"; }
die()  { log "ERROR: $*"; exit 1; }

# ── Main ─────────────────────────────────────────────────────────────
log "Starting in-place deployment ..."

# 1. Pull latest code
cd "$REPO_DIR"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" == "HEAD" ]]; then
    log "Detached HEAD state detected. Fetching origin and resetting to HEAD to clear local changes..."
    git fetch origin
    git reset --hard HEAD
else
    log "Pulling latest code for branch: ${CURRENT_BRANCH} ..."
    git pull origin "$CURRENT_BRANCH"
fi

# 2. Build & start the application (in-place)
log "Building and starting application containers ..."
docker compose up -d --build

log "Deployment complete."
