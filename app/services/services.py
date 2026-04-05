import logging
import random
import time
from functools import wraps

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from peewee import InterfaceError, OperationalError

from app.observability.metrics import (
    DB_RETRIES_EXHAUSTED_TOTAL,
    DB_RETRY_ATTEMPTS_TOTAL,
    DB_RETRY_BACKOFF_SECONDS,
)

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

RETRYABLE_ERRORS = (OperationalError, InterfaceError, ConnectionError)

def retry_db(max_retries=3, base_delay=0.05):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return fn(*args, **kwargs)
                except RETRYABLE_ERRORS as exc:
                    from app.database import db

                    db.close()
                    db.connect(reuse_if_open=True)

                    error_type = type(exc).__name__
                    DB_RETRY_ATTEMPTS_TOTAL.labels(function_name=fn.__name__, error_type=error_type).inc()

                    if attempt == max_retries - 1:
                        DB_RETRIES_EXHAUSTED_TOTAL.labels(
                            function_name=fn.__name__,
                            error_type=error_type,
                        ).inc()
                        logger.error(
                            "db.retry.exhausted",
                            extra={
                                "function_name": fn.__name__,
                                "max_retries": max_retries,
                                "error_type": error_type,
                            },
                        )
                        raise

                    delay = base_delay * (2**attempt)
                    jitter = random.uniform(0, delay * 0.2)
                    sleep_for = delay + jitter
                    DB_RETRY_BACKOFF_SECONDS.labels(function_name=fn.__name__).observe(sleep_for)

                    logger.warning(
                        "db.retry.scheduled",
                        extra={
                            "function_name": fn.__name__,
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "backoff_seconds": round(sleep_for, 4),
                            "error_type": error_type,
                        },
                    )
                    time.sleep(sleep_for)

        return wrapper

    return decorator
