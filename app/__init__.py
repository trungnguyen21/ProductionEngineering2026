import logging
import os

import peewee

from dotenv import load_dotenv
from flask import Flask, jsonify
from flasgger import Swagger

from app.database import init_db
from app.routes import register_routes
from app.services.services import limiter

logger = logging.getLogger(__name__)

def create_app():
    load_dotenv()

    app = Flask(__name__)
    Swagger(app)
    init_db(app)

    # Initialize rate limiter with Redis (falls back to in-memory)
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    app.config["RATELIMIT_ENABLED"] = False
    app.config["RATELIMIT_STORAGE_URI"] = redis_url
    app.config["RATELIMIT_STRATEGY"] = "fixed-window"
    limiter.init_app(app)

    register_routes(app)

    @app.route("/health")
    def health():
        from app.database import db
        db_ok = True
        try:
            db.execute_sql("SELECT 1;")
        except Exception:
            db_ok = False
        status = "ok" if db_ok else "degraded"
        code = 200 if db_ok else 503
        return jsonify(status=status, db=db_ok), code

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
