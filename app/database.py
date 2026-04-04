import os
import time
import logging

from flask import jsonify

from peewee import DatabaseProxy, Model, OperationalError, InterfaceError
from playhouse.pool import PooledPostgresqlDatabase

db = DatabaseProxy()
logger = logging.getLogger(__name__)

class BaseModel(Model):
    class Meta:
        database = db

class ObservableDatabasePool(PooledPostgresqlDatabase):
    # Override the execute_sql method to hook up logging
    def execute_sql(self, sql, params=None):
        start = time.time()
        error = None

        try:
            return super().execute_sql(sql, params=params)
        except Exception as e:
            error = str(e)
            raise
        finally:
            duration_ms = (time.time() - start) * 1000

            logger.info(
                "db_query",
                extra={
                    "duration_ms": round(duration_ms, 2),
                    "query": sql[:100],  # truncate for safety
                    "error": error,
                }
            )


def init_db(app):
    database = ObservableDatabasePool(
        database=os.environ.get("DATABASE_NAME", "hackathon_db"),
        max_connections=20,
        timeout=5,              # wait max 5 seconds for a free connection
        stale_timeout=300,      # replace idle connection
        host=os.environ.get("DATABASE_HOST", "localhost"),
        port=int(os.environ.get("DATABASE_PORT", 5432)),
        user=os.environ.get("DATABASE_USER", "postgres"),
        password=os.environ.get("DATABASE_PASSWORD", "postgres"),
        options='-c statement_timeout=2000'  # 2 seconds timeout for each statement
    )
    db.initialize(database)

    @app.before_request
    def _db_connect():
        try:
            db.connect(reuse_if_open=True)
        except Exception:
            # TODO: add logging
            pass

    @app.teardown_request
    def _db_close(exec):
        if not db.is_closed():
            db.close()

    @app.errorhandler(OperationalError)
    def handle_db_error(e):
        return jsonify({
            "error": "database_unavailable",
            "message": "Service temporarily degraded"
        }), 503

    @app.route("/ready")
    def db_health():
        try: 
            db.execute_sql("SELECT 1;")
            return jsonify({"status": "healthy"}), 200
        except Exception:
            return jsonify({"status": "database not ready"}), 500
