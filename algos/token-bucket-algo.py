"""
- Token Bucket algorithm allows for burstiness by allowing user to "burst" through a set of requests immediately until the bucket is empty.
- Each request requires one or more tokens. If the bucket has enough tokens, the request passes, and tokens are removed. Otherwise, the request is throttled (429 Too Many Requests)
"""

import time
import threading

class TokenBucket():
  def __init__(self, capacity: int, refill_rate: float):
    """
    Initializes the bucket.
    :param capacity: The max tokens the bucket can hold (the 'burst' limit).
    :param refill_rate: How many tokens are added per second.
    """
    self.capacity = capacity
    self.refill_rate = refill_rate
    # Start with a full bucket to allow an immediate burst of traffic.
    self.tokens = capacity
    # Use monotonic clock to measure elapsed time accurately, 
    # avoiding issues with system clock resets or NTP syncs.
    self.last_refill_time = time.monotonic()
    # Lock ensures thread safety: only one thread can modify token count at a time.
    self._lock = threading.Lock()

  def allow_request(self, tokens_requested: int = 1) -> bool:
    """
    Main entry point. Determines if a request should be throttled.
    """
    with self._lock:
      # We refill 'lazily' (only when a request arrives) to save CPU.
      self._refill()

      if self.tokens >= tokens_requested: # if tokens exist in bucket
        # Deduct tokens and let the request through.
        self.tokens -= tokens_requested
        return True
      
      # Not enough tokens; the request is rate-limited.
      return False
  
  def _refill(self):
    """
    Internal logic to calculate how many tokens have been earned 
    since the last check.
    """
    now = time.monotonic()
    elapsed = now - self.last_refill_time
    
    # Earn tokens proportional to the time that has passed.
    new_tokens = elapsed * self.refill_rate

    # Only update state if enough time has passed to generate tokens.
    if new_tokens > 0:
      # Add tokens but never exceed the defined capacity.
      self.tokens = min(self.capacity, self.tokens + new_tokens)
      # Update the timestamp for the next refill calculation.
      self.last_refill_time = now


