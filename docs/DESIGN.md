# Project Lazarus - Resurrection
This is my journey over 24 hours adding everything I can to monitor a simple web app!

See the [Architecture Diagram](ARCHITECTURE.md) for a visual overview of the system.

## 1. Implementing the URL shortener
Using the template Flask + peewee + PostgreSQL:
- Put PostgreSQL onto Docker.
- Written unit tests and integration tests using `pytest`.
- Added swagger for each endpoint since I'm a long FastAPI user :D

## 2. Database connection harnessing
- Noticed we are connecting to the db, query, then close the connection, so I added DB pooling.
- Added timeouts everywhere: query timeout, waiting for connection timeout, stale timeout, etc. - ensure queries do not hang!
- Added a locust file to do load testing, simulating a user flow and other endpoints with weights. 

## 3. Noticed bottleneck
- When I do load testing, the database was overloaded with connection, affecting performance.
- Added Redis caching: simple key-value cache in between the client and the database.

*Why Redis?* Dead simple, very lightweight and very fast! Industry standard.

**Hierarchy structure of the cache**

| Key Pattern | Value Type | Purpose | TTL (Expiry) |
| :--- | :--- | :--- | :--- |
| `redirect:{short_code}` | JSON Object | Maps short codes to original URLs for the `/redirect` endpoint. | 5 minutes |
| `url:{url_id}` | JSON Object | Stores the full metadata for a specific URL (`GET /urls/:id`). | 5 minutes |
| `urls:list:u{user_id}:a{is_active}` | JSON List | Stores the results of filtered URL listings (`GET /urls`). | 1 minute |

## 4. Start adding loggings
- Added level-based logs, with extra information like method, status code, duration, etc.
- Record SQL execution time to detect N+1 queries if any.

## 5. Prometheus + Grafana
- Added Prometheus and Grafana to Docker, exposing `/metrics` endpoint.
- Added metrics recording when logging: HISTOGRAM, COUNTER, etc.
- Configure to record metrics before and after each request, put processing times in buckets.

*Why Prometheus + Grafana?*

Best open-source combo, very effective and free!

*What are some alternatives?*

OpenTelemetry worth mentioning here. An Enterprise solution with metrics, logging, monitoring all in one. Though, with a limited hardware (2-core CPU 2GB RAM), OpenTelemetry is an overkill for this app.

## 6. Added alert rules
- Configure Alertmanager to ping me of abnormalities like high 400+ status code rate, high p95, degraded db, etc.
- Initialize rules, selective events to put alert (high p95 over 5 minutes instead of any occurrences of high latency).
- Added point of contact (Discord Webhook) to notify me.

## 7. CI/CD & Deployment
- Deploy to a DigitalOcean’s droplet.
- Containerized components, dry run local, include `deploy.sh` script.
- Wrote `ci.yml` and `deploy.yml` file.
- First time also containerized NGINX proxy to Docker, did not know this was possible haha.
- Spent so much time on this even though this is not my first rodeo.

## 8. Misc stuffs
- Configure blue-green deployment, chasing that 99.99% uptime -> failed miserably due to lack of Kubernetes, in-place deployment introduced lower downtime :).
- Added Loki + Promtail so I can see logs without SSH into the server.
- Added cadvisor to monitor VPS usage -> turns out I can setup 4 workers on gunicorn instead of just 2.
- Used network bridge to expose only client-facing services (server, grafana) while hiding other services from port discovery, think internal ingress.

*Why Loki + Promtail?*

It did take much longer to setup these 2 instead of adding 5 lines of code for Dozzle, but with built-in functionality within Grafana dashboard, and logging query based on container, I think it was worth it compared to at-the-moment logging snapshot that Dozzle provided.

## 9. Docker Compose Policy:
- Utilized Docker Compose `deploy` to spins up 2 replicas of the web server
- Utilized `unless-stopped` restart policy to restart container on non-zero exits
**Trade off**: 
- Instead of using `on-failure`, I used this to restart the container in *almost* all scenarios (crashes, reboot, or successful exits, etc.) -> suitable for prod servers since it needs high availability
- Compared to `on-failure` with `max-retries`, this policy will restart a container with a specified number of attempts -> we don't want that for our server to be down after like 3 retries
- Downside of `unless-stopped`: infinitely retry when the container failed unless `docker stop`

## 10. Locust load testing:
- Define 2 business-logic endpoints to test: `/urls`, `redirect`
- Define the weights (possibility of the task being run over the other)

## 11. NGINX policy (WIP)