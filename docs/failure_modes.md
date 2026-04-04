# Failure Modes Manual

This document describes what happens when each component breaks, how the app responds, and how to verify recovery.

---

## 1. Database Goes Down

**Scenario:** `docker stop hackathon_db`

| Layer | What Happens |
|-------|-------------|
| Flask request hits a DB call | `retry_db` retries 3× with exponential backoff (50ms → 100ms → 200ms) |
| All retries exhausted | `OperationalError` propagates to Flask's global error handler |
| HTTP response | `503 Service Unavailable` + `{"error": "database_unavailable", "message": "Service temporarily degraded"}` |
| `/health` endpoint | Returns `{"status": "degraded", "db": false}` + 503 |
| `/ready` endpoint | Returns `{"status": "database not ready"}` + 500 |
| Docker healthcheck | Fails after 3 retries → container marked **unhealthy** |

**Verify:**
```bash
docker stop hackathon_db
curl http://localhost:8000/health      # → 503 degraded
curl -X GET http://localhost:8000/users # → 503 JSON error
docker start hackathon_db
curl http://localhost:8000/health      # → 200 ok (once DB is ready)
```

---

## 2. App Process / Container Crashes

**Scenario:** `docker kill hackathon_web` or app throws unhandled exception

| Trigger | What Happens |
|---------|-------------|
| Container killed/crashes | Docker detects exit → `restart: unless-stopped` kicks in |
| Restart time | Typically < 5 seconds |
| DB dependency | App waits for `db` healthcheck to pass before accepting traffic |
| New requests during restart | Connection refused (brief gap while restarting) |

**Verify:**
```bash
docker kill hackathon_web
docker ps   # watch STATUS — container restarts automatically
curl http://localhost:8000/health  # succeeds once restarted
```

---

## 3. Bad Input / Malformed Requests

**Scenario:** Client sends wrong types, missing fields, or invalid JSON

| Bad Input | HTTP Status | JSON Response |
|-----------|-------------|---------------|
| Missing required field (`url_id`, `event_type`, etc.) | `400` | `{"error": "bad_request", ...}` |
| Non-existent user/URL ID | `404` | `{"error": "not_found", ...}` |
| Duplicate username/email | `409` | `{"error": "conflict", ...}` |
| Wrong HTTP method (e.g. DELETE on read-only route) | `405` | `{"error": "method_not_allowed", ...}` |
| Completely unknown crash | `500` | `{"error": "internal_server_error", "message": "An unexpected error occurred"}` |

No HTML error pages are ever returned — all responses are JSON.

**Verify:**
```bash
# Missing field
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"event_type": "click"}'
# → 400 {"error": "bad_request", ...}

# Non-existent resource
curl http://localhost:8000/users/99999
# → 404 {"error": "not_found", ...}

# Wrong method
curl -X DELETE http://localhost:8000/users
# → 405 {"error": "method_not_allowed", ...}
```

---

## 4. Slow Database (Statement Timeout)

**Scenario:** DB is up but queries take too long (lock contention, heavy load)

| Layer | What Happens |
|-------|-------------|
| PostgreSQL `statement_timeout=2000ms` | DB kills the query after 2 seconds |
| Flask receives `QueryCanceledError` | Treated as a retryable DB error by `retry_db` |
| After 3 retries | Returns `503` to client |
| `db_query` log entries | Each query logs `duration_ms` for observability |

**Simulate:**
```sql
-- In psql, lock a table manually to cause timeouts
BEGIN; LOCK TABLE users IN ACCESS EXCLUSIVE MODE;
-- then send requests — they'll timeout after 2s
```

---

## 5. Connection Pool Exhaustion

**Scenario:** Too many concurrent requests, pool of 20 connections fills up

| Layer | What Happens |
|-------|-------------|
| `PooledPostgresqlDatabase(max_connections=20, timeout=5)` | Waits up to 5s for a free connection |
| Timeout exceeded | `OperationalError` raised |
| `retry_db` + error handler | Retries then returns `503` |

**Simulate:**
```bash
# Hammer with 50 concurrent requests
ab -n 500 -c 50 http://localhost:8000/users
```

---

## Recovery Checklist

- [ ] DB restarted → wait for `/ready` to return 200 before sending traffic
- [ ] App restarted → watch `docker ps` for `healthy` status
- [ ] After incident → check logs: `docker logs hackathon_web --tail 100`
