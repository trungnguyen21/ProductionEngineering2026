import time
import logging

logger = logging.getLogger(__name__)

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=10):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.warning("db.circuit_breaker.half_open")
                return True
            return False
        return True

    def record_success(self):
        if self.state != "CLOSED":
            logger.info("db.circuit_breaker.closed")
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            if self.state != "OPEN":
                logger.warning("db.circuit_breaker.open")
            self.state = "OPEN"