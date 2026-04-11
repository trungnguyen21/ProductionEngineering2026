import logging
import os
import time

from flask import jsonify
from flask import has_request_context, request
from peewee import DatabaseProxy, Model, OperationalError
from playhouse.pool import PooledPostgresqlDatabase

from app.observability.metrics import (
    DB_ERRORS_TOTAL,
    DB_QUERY_DURATION_SECONDS,
    observe_db_pool_state,
)
from app.services.circuit_breaker import CircuitBreaker
from app.config import PROBE_PATHS

logger = logging.getLogger(__name__)
db = DatabaseProxy()
db_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=10
)


def _is_probe_request() -> bool:
    if not has_request_context():
        return False

    normalized_path = request.path.rstrip("/") or "/"
    normalized_probe_paths = {path.rstrip("/") or "/" for path in PROBE_PATHS}
    return normalized_path in normalized_probe_paths


class BaseModel(Model):
    class Meta:
        database = db


class ObservableDatabasePool(PooledPostgresqlDatabase):
    def execute_sql(self, sql, params=None):
        if not db_breaker.can_execute():
            raise OperationalError("Circuit breaker open")
        start = time.perf_counter()
        operation = (sql or "unknown").strip().split(" ", 1)[0].lower() or "unknown"

        try:
            result = super().execute_sql(sql, params=params)
            db_breaker.record_success()
            return result
        except Exception as exc:
            if isinstance(exc, OperationalError):
                db_breaker.record_failure()
            DB_ERRORS_TOTAL.labels(operation=operation, error_type=type(exc).__name__).inc()
            if not _is_probe_request():
                logger.exception(
                    "db.query.failed",
                    extra={"operation": operation, "query_preview": (sql or "")[:120]},
                )
            raise
        finally:
            duration_s = time.perf_counter() - start
            DB_QUERY_DURATION_SECONDS.labels(operation=operation).observe(duration_s)
            observe_db_pool_state(self)

            if not _is_probe_request():
                logger.info(
                    "db.query.completed",
                    extra={
                        "operation": operation,
                        "duration_ms": round(duration_s * 1000, 2),
                    },
                )


def init_db(app):
    database = ObservableDatabasePool(
        database=os.environ.get("DATABASE_NAME", "hackathon_db"),
        max_connections=int(os.environ.get("DATABASE_MAX_CONNECTIONS", 20)),
        timeout=int(os.environ.get("DATABASE_POOL_TIMEOUT", 2)),
        stale_timeout=int(os.environ.get("DATABASE_STALE_TIMEOUT", 300)),
        host=os.environ.get("DATABASE_HOST", "localhost"),
        port=int(os.environ.get("DATABASE_PORT", 5432)),
        user=os.environ.get("DATABASE_USER", "postgres"),
        password=os.environ.get("DATABASE_PASSWORD", "postgres"),
        options="-c statement_timeout=2000",
        connect_timeout=int(os.environ.get("DATABASE_CONNECT_TIMEOUT", 2)),
        keepalives=1,
        keepalives_idle=2,
        keepalives_interval=2,
        keepalives_count=2,
        tcp_user_timeout=2000,
    )
    db.initialize(database)

    @app.teardown_request
    def _db_close(_exc):
        try:
            if not db.is_closed():
                db.close()
        except Exception:
            logger.warning("db.close.failed")
        finally:
            observe_db_pool_state(database)

    @app.errorhandler(OperationalError)
    def handle_db_error(_e):
        return jsonify({"error": "database_unavailable", "message": "Service temporarily degraded"}), 503


def check_db_connection() -> bool:
    """Active database connectivity check for readiness endpoints."""
    try:
        with db.connection_context():
            db.execute_sql("SELECT 1;")
        return True
    except Exception as exc:
        logger.warning("db.ping.failed", extra={"error_type": type(exc).__name__})
        return False

def ensure_tables():
    """Create core tables in dependency order if they do not exist."""
    from app.models.user import User
    from app.models.url import Url
    from app.models.event import Event

    with db.connection_context():
        db.create_tables([User, Url, Event], safe=True)
