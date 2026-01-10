"""
- Token Bucket algorithm allows for burstiness by allowing user to "burst" through a set of requests immediately until the bucket is empty.
- Each request requires one or more tokens. If the bucket has enough tokens, the request passes, and tokens are removed. Otherwise, the request is throttled (429 Too Many Requests)
"""

import time
import threading

class TokenBucket():
  def __init__(self, capacity: int, refill_rate: float):
    self.capacity = capacity
    self.refill_rate = refill_rate
    self.tokens = capacity
    self.last_refill_time = time.monotonic()
    self._lock = threading.Lock()

  def allow_request(self, tokens_requested: int = 1) -> bool:
    with self._lock:
      self._refill()
      if self.tokens >= tokens_requested:
        self.tokens -= tokens_requested
        return True
      return False
  
  def _refill(self):
    now = time.monotonic()
    elapsed = now - self.last_refill_time
    # Calculate new tokens based on elapsed time
    new_tokens = elapsed * self.refill_rate

    if new_tokens > 0:
      self.tokens = min(self.capacity, self.tokens + new_tokens)
      self.last_refill_time = now


