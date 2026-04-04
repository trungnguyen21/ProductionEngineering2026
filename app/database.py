import logging
import os
import time

from flask import jsonify
from peewee import DatabaseProxy, Model, OperationalError
from playhouse.pool import PooledPostgresqlDatabase

from app.observability.metrics import (
    DB_ERRORS_TOTAL,
    DB_QUERY_DURATION_SECONDS,
    observe_db_pool_state,
)

db = DatabaseProxy()
logger = logging.getLogger(__name__)


class BaseModel(Model):
    class Meta:
        database = db


class ObservableDatabasePool(PooledPostgresqlDatabase):
    def execute_sql(self, sql, params=None):
        start = time.perf_counter()
        operation = (sql or "unknown").strip().split(" ", 1)[0].lower() or "unknown"

        try:
            return super().execute_sql(sql, params=params)
        except Exception as exc:
            DB_ERRORS_TOTAL.labels(operation=operation, error_type=type(exc).__name__).inc()
            logger.exception(
                "db.query.failed",
                extra={"operation": operation, "query_preview": (sql or "")[:120]},
            )
            raise
        finally:
            duration_s = time.perf_counter() - start
            DB_QUERY_DURATION_SECONDS.labels(operation=operation).observe(duration_s)
            observe_db_pool_state(self)

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
        timeout=int(os.environ.get("DATABASE_POOL_TIMEOUT", 5)),
        stale_timeout=int(os.environ.get("DATABASE_STALE_TIMEOUT", 300)),
        host=os.environ.get("DATABASE_HOST", "localhost"),
        port=int(os.environ.get("DATABASE_PORT", 5432)),
        user=os.environ.get("DATABASE_USER", "postgres"),
        password=os.environ.get("DATABASE_PASSWORD", "postgres"),
        options="-c statement_timeout=2000",
    )
    db.initialize(database)

    @app.before_request
    def _db_connect():
        try:
            db.connect(reuse_if_open=True)
            observe_db_pool_state(database)
        except Exception:
            logger.exception("db.connect.failed")

    @app.teardown_request
    def _db_close(_exc):
        if not db.is_closed():
            db.close()
            observe_db_pool_state(database)

    @app.errorhandler(OperationalError)
    def handle_db_error(_e):
        return jsonify({"error": "database_unavailable", "message": "Service temporarily degraded"}), 503
