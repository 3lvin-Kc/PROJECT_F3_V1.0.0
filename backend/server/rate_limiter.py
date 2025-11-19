import time
from collections import defaultdict
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter to control API calls to Gemini.
    
    Implements a token bucket algorithm to prevent quota exhaustion.
    """

    def __init__(
        self,
        requests_per_minute: int = 10,
        requests_per_hour: int = 100,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests allowed per minute
            requests_per_hour: Max requests allowed per hour
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # Track requests per client IP
        self.minute_requests = defaultdict(list)  # IP -> [timestamp, timestamp, ...]
        self.hour_requests = defaultdict(list)

    def is_allowed(self, client_id: str) -> Tuple[bool, str]:
        """
        Check if a request is allowed for the given client.

        Args:
            client_id: Client identifier (IP address or user ID)

        Returns:
            Tuple of (allowed: bool, message: str)
        """
        current_time = time.time()

        # Clean up old requests (older than 1 hour)
        self._cleanup_old_requests(client_id, current_time)

        # Check minute limit
        minute_count = len(self.minute_requests[client_id])
        if minute_count >= self.requests_per_minute:
            return False, f"Rate limit exceeded: {minute_count}/{self.requests_per_minute} requests per minute"

        # Check hour limit
        hour_count = len(self.hour_requests[client_id])
        if hour_count >= self.requests_per_hour:
            return False, f"Rate limit exceeded: {hour_count}/{self.requests_per_hour} requests per hour"

        # Request is allowed, record it
        self.minute_requests[client_id].append(current_time)
        self.hour_requests[client_id].append(current_time)

        remaining_minute = self.requests_per_minute - minute_count - 1
        remaining_hour = self.requests_per_hour - hour_count - 1

        logger.info(
            f"Request allowed for {client_id}. "
            f"Remaining: {remaining_minute}/min, {remaining_hour}/hour"
        )

        return True, f"OK. Remaining: {remaining_minute}/min, {remaining_hour}/hour"

    def _cleanup_old_requests(self, client_id: str, current_time: float):
        """Remove requests older than 1 hour."""
        one_hour_ago = current_time - 3600

        # Clean minute requests (older than 1 minute)
        one_minute_ago = current_time - 60
        self.minute_requests[client_id] = [
            ts for ts in self.minute_requests[client_id] if ts > one_minute_ago
        ]

        # Clean hour requests (older than 1 hour)
        self.hour_requests[client_id] = [
            ts for ts in self.hour_requests[client_id] if ts > one_hour_ago
        ]

    def get_status(self, client_id: str) -> dict:
        """Get current rate limit status for a client."""
        current_time = time.time()
        self._cleanup_old_requests(client_id, current_time)

        minute_count = len(self.minute_requests[client_id])
        hour_count = len(self.hour_requests[client_id])

        return {
            "minute": {
                "used": minute_count,
                "limit": self.requests_per_minute,
                "remaining": self.requests_per_minute - minute_count,
            },
            "hour": {
                "used": hour_count,
                "limit": self.requests_per_hour,
                "remaining": self.requests_per_hour - hour_count,
            },
        }


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter(
    requests_per_minute: int = 10, requests_per_hour: int = 100
) -> RateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
        )
    return _rate_limiter
