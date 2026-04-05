# Production Engineering Hackathon Project

A minimal Flask-based web service for URL shortener, featuring PostgreSQL persistence, observability, and caching. Designed for reliability, performance, and maintainability.

## Tech Stack

- Python (Flask)
- Peewee ORM
- PostgreSQL
- Prometheus (metrics)
- Grafana (monitoring dashboard)
- Redis (caching)
- Docker & Docker Compose
- cAdvisor (system metrics)

## Main Components

- **app/**: 
  - **models/**: Database models (User, Event, URL)
  - **routes/**: API endpoints (users, events, urls)
  - **services/**: Business logic, caching
  - **observability/**: Logging and metrics
  - **database.py**: DB connection and base model
- **artifacts/**: Misc files
- **tests/**: Unit and integration tests
- **prometheus.yml**: Prometheus config
- **prometheus-rules.yml**: Alerting rules
- **Dockerfile / docker-compose.yml**: Containerization

## API Endpoints

### Users

- `GET    /users` — List all users
- `GET    /users/<id>` — Get user by ID
- `POST   /users` — Create user
- `PUT    /users/<id>` — Update user
- `DELETE /users/<id>` — Delete user

### Events

- `GET    /events` — List all events
- `GET    /events/<id>` — Get event by ID
- `POST   /events` — Create event
- `PUT    /events/<id>` — Update event
- `DELETE /events/<id>` — Delete event

### URLs

- `GET    /urls` — List all URLs
- `GET    /urls/<id>` — Get URL by ID
- `POST   /urls` — Create URL
- `PUT    /urls/<id>` — Update URL
- `DELETE /urls/<id>` — Delete URL

### Health

- `GET    /health` — Health check

## Logging

- Centralized logging via `app/observability/logging.py`
- Logs requests, errors, and key events

## Monitoring

- Prometheus scrapes application and cAdvisor metrics
- Grafana dashboard for SRE signals and system resources
- Custom metrics via `app/observability/metrics.py`

## Caching

- Redis-based caching for user, event, and URL lookups
- Implemented in `app/services/cache.py`

## Quick Start

1. Install [Docker](https://www.docker.com/)
2. Run `cp .env.example .env` to create your .env file
- See this [guide](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) for getting your Discord Webhook URL
2. Run `docker compose up -d` to run in detached mode
3. See your app in `http://localhost:8000`

## Testing

- All tests in `tests/` (unit and integration)
- Run with `pytest`