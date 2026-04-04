# Deployment Guide

This guide walks you through deploying the app and monitoring stack securely on a VPS using Docker Compose with Nginx as the only public entrypoint.

## Prerequisites

- Docker and Docker Compose installed
- Git installed
- A VPS (Ubuntu recommended)

## 1. Clone the Repository

```
git clone <your-repo-url>
cd ProductionEngineering2026
```

## 2. Configure Environment

- Copy `.env.example` to `.env` and edit as needed:

```
cp .env.example .env
nano .env
```

- Set strong passwords for DB and Redis in `.env`.

## 3. Build and Start Services

- Use the hardened override for secure deployment:

```
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d --build
```

- Option A (no custom domain): set Grafana subpath URL in `.env`:

```
GF_SERVER_ROOT_URL=http://<your-vps-ip>:8080/grafana/
```

- This will:
  - Start all services
  - Only expose Nginx on port 8080
  - All other services are internal-only

## 4. Access the Application

- App: `http://<your-vps-ip>/`
- Grafana: `http://<your-vps-ip>/grafana/`

## 5. (Optional) Seed the Database

- If you need to load initial data, use a one-off container or connect to Postgres:

```
docker compose exec db psql -U <db_user> -d <db_name>
```

## 6. Logs and Monitoring

- View logs for any service:

```
docker compose logs -f nginx
```

- Grafana dashboards are available at `/grafana/` (default user: admin, password: admin unless changed)

## 7. Security Notes

- Only port 80 is open to the public
- Prometheus, cAdvisor, Redis, and Postgres are not accessible from outside
- Change all default passwords before going live
- For HTTPS, set up a reverse proxy (e.g., Caddy or Nginx with Certbot) in front of Docker or use a cloud load balancer

## 8. Stopping and Updating

- Stop all services:

```
docker compose down
```

- Pull updates and rebuild:

```
git pull
# Then repeat step 3
```

---

For troubleshooting or advanced configuration, see the README or ask your platform administrator.
