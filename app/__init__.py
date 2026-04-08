import logging
import os
import socket

import peewee

from dotenv import load_dotenv
from flask import Flask, jsonify
from flasgger import Swagger
from prometheus_flask_exporter import PrometheusMetrics

from app.database import init_db, ensure_tables
from app.observability.logging import configure_logging, setup_request_logging
from app.observability.metrics import setup_http_metrics
from app.routes import register_routes
from app.services.services import limiter

logger = logging.getLogger(__name__)

def create_app():
    load_dotenv()
    configure_logging()

    app = Flask(__name__)
    Swagger(app)
    metrics_enabled = os.environ.get("METRICS_ENABLED", "true").lower() == "true"
    if metrics_enabled:
        PrometheusMetrics(app)
        setup_http_metrics(app)

    setup_request_logging(app)
    init_db(app)

    # One-time schema bootstrap on app startup.
    ensure_tables()

    # Initialize rate limiter with Redis (falls back to in-memory)
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    app.config["RATELIMIT_ENABLED"] = False
    app.config["RATELIMIT_STORAGE_URI"] = redis_url
    app.config["RATELIMIT_STRATEGY"] = "fixed-window"
    limiter.init_app(app)

    register_routes(app)

    @app.route("/health")
    def health():
        return jsonify("Server is running"), 200
    
    @app.route("/container")
    def get_container_id():
        return jsonify(f"Container ID: {socket.gethostname()}"), 200

    @app.route("/ready")
    def ready():
        from app.database import db
        from app.services.cache import get_redis
        
        db_ok = True
        redis_ok = True
        
        try:
            # Use a simple query to verify connectivity
            with db.connection_context():
                db.execute_sql("SELECT 1;")
        except Exception as e:
            logger.warning("health_check.db_failed: %s", e)
            db_ok = False

        try:
            r = get_redis()
            if r is None:
                redis_ok = False
            else:
                r.ping()
        except Exception as e:
            logger.warning("health_check.redis_failed: %s", e)
            redis_ok = False
        
        status = "ok" if (db_ok and redis_ok) else "degraded"
        code = 200 if db_ok else 503
        return jsonify(status=status, db=db_ok, redis=redis_ok), code

    # ── Global JSON error handlers ──────────────────────────────────────────

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(error="bad_request", message=str(e.description)), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="not_found", message=str(e.description)), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify(error="method_not_allowed", message=str(e.description)), 405

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify(error="unprocessable_entity", message=str(e.description)), 422

    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify(error="rate_limit_exceeded", message="Too many requests, please slow down"), 429

    @app.errorhandler(500)
    def internal_error(e):
        logger.exception("Unhandled internal error")
        return jsonify(error="internal_server_error", message="An unexpected error occurred"), 500

    @app.errorhandler(peewee.DoesNotExist)
    def peewee_not_found(e):
        return jsonify(error="not_found", message=str(e)), 404

    @app.errorhandler(peewee.IntegrityError)
    def peewee_conflict(e):
        return jsonify(error="conflict", message="Resource already exists or constraint violated"), 409

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        logger.exception("Unhandled exception: %s", e)
        return jsonify(error="internal_server_error", message="An unexpected error occurred"), 500

    return app
