#!/usr/bin/env bash
# deploy.sh — Blue-green deployment orchestrator
# Run from the repo root: ./deploy/deploy.sh
set -euo pipefail

DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$DEPLOY_DIR")"
STATE_FILE="$DEPLOY_DIR/.active_slot"
UPSTREAM_CONF="$DEPLOY_DIR/upstream.conf"

BLUE_PORT=8001
GREEN_PORT=8002
BLUE_CONTAINER=hackathon_web_blue
GREEN_CONTAINER=hackathon_web_green
HEALTH_RETRIES=20
HEALTH_INTERVAL=3

# ── Helpers ──────────────────────────────────────────────────────────
log()  { echo "[deploy] $(date '+%H:%M:%S') $*"; }
die()  { log "ERROR: $*"; exit 1; }

get_active_slot() {
    if [[ -f "$STATE_FILE" ]]; then
        cat "$STATE_FILE"
    else
        echo "none"
    fi
}

health_check() {
    local port=$1
    local attempt=1
    log "Health-checking localhost:${port}/ready ..."
    while (( attempt <= HEALTH_RETRIES )); do
        if curl -sf "http://localhost:${port}/ready" > /dev/null 2>&1; then
            log "Health check passed (attempt ${attempt}/${HEALTH_RETRIES})"
            return 0
        fi
        log "Attempt ${attempt}/${HEALTH_RETRIES} failed, retrying in ${HEALTH_INTERVAL}s ..."
        sleep "$HEALTH_INTERVAL"
        (( attempt++ ))
    done
    return 1
}

swap_upstream() {
    local container=$1
    cat > "$UPSTREAM_CONF" <<EOF
upstream app_backend {
    server ${container}:8000;
}
EOF
    log "Upstream swapped to ${container}"
}

reload_nginx() {
    docker exec nginx_proxy nginx -s reload
    log "Nginx reloaded"
}

# ── Main ─────────────────────────────────────────────────────────────
log "Starting deployment ..."

# 1. Pull latest code
cd "$REPO_DIR"
log "Pulling latest code ..."
git pull --ff-only origin main

# 2. Ensure shared infra is running
log "Starting shared infrastructure ..."
docker compose -f deploy/docker-compose.infra.yml up -d

# 3. Determine target slot
ACTIVE=$(get_active_slot)
if [[ "$ACTIVE" == "blue" ]]; then
    TARGET="green"
    TARGET_PORT=$GREEN_PORT
    TARGET_CONTAINER=$GREEN_CONTAINER
    OLD_COMPOSE="deploy/docker-compose.blue.yml"
else
    TARGET="blue"
    TARGET_PORT=$BLUE_PORT
    TARGET_CONTAINER=$BLUE_CONTAINER
    OLD_COMPOSE="deploy/docker-compose.green.yml"
fi
TARGET_COMPOSE="deploy/docker-compose.${TARGET}.yml"
log "Active slot: ${ACTIVE} → deploying to: ${TARGET}"

# 4. Build & start the target slot
log "Building and starting ${TARGET} slot ..."
docker compose -f "$TARGET_COMPOSE" up -d --build

# 5. Health check
if ! health_check "$TARGET_PORT"; then
    log "Health check FAILED — rolling back"
    docker compose -f "$TARGET_COMPOSE" down
    die "Deployment aborted. Previous slot (${ACTIVE}) is still live."
fi

# 6. Swap Nginx upstream & reload
swap_upstream "$TARGET_CONTAINER"
reload_nginx

# 7. Tear down old slot (if any)
if [[ "$ACTIVE" != "none" ]]; then
    log "Tearing down old ${ACTIVE} slot ..."
    docker compose -f "$OLD_COMPOSE" down
fi

# 8. Persist active slot
echo "$TARGET" > "$STATE_FILE"
log "Deployment complete — active slot: ${TARGET}"
