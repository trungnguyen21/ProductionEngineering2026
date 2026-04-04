import time
import random
import logging

from functools import wraps

from peewee import OperationalError, InterfaceError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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
                except RETRYABLE_ERRORS as e:
                    # force reconnect (important for pooled connections)
                    from app.database import db
                    db.close()
                    db.connect(reuse_if_open=True)

                    if attempt == max_retries - 1:
                        logger.error(f"All {max_retries} retries exhausted for {fn.__name__}: {e}")
                        raise

                    delay = base_delay * (2 ** attempt)
                    jitter = random.uniform(0, delay * 0.2)
                    logger.warning(
                        f"Retry {attempt + 1}/{max_retries} for {fn.__name__} "
                        f"after {delay + jitter:.3f}s: {e}"
                    )
                    time.sleep(delay + jitter)
        return wrapper
    return decorator