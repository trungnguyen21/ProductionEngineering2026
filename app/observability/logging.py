import json
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timezone

from flask import g, request, has_request_context
from app.config import PROBE_PATHS


class JsonFormatter(logging.Formatter):
    """Simple JSON formatter for production-friendly logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key in ("request_id", "method", "path", "status_code", "duration_ms", "remote_addr"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "text").lower()

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    if log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%SZ",
            )
        )
        handler.formatter.converter = time.gmtime

    root_logger.addHandler(handler)

def _is_probe_request() -> bool:
    if not has_request_context():
        return False

    normalized_path = request.path.rstrip("/") or "/"
    normalized_probe_paths = {path.rstrip("/") or "/" for path in PROBE_PATHS}
    return normalized_path in normalized_probe_paths


def setup_request_logging(app) -> None:
    logger = logging.getLogger("app.request")

    @app.before_request
    def log_request_start():
        if not _is_probe_request():
            request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
            g.request_id = request_id
            g.request_log_started_at = time.perf_counter()

    @app.after_request
    def log_request_end(response):
        if not _is_probe_request():
            started_at = getattr(g, "request_log_started_at", None)
            duration_ms = (time.perf_counter() - started_at) * 1000 if started_at else 0.0
            logger.info(
                "request.completed",
                extra={
                    "request_id": g.request_id,
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "remote_addr": request.remote_addr,
                },
            )
            response.headers["X-Request-ID"] = g.request_id

        return response
