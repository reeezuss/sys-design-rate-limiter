"""
The leaking bucket algorithm is similar to the token bucket except that requests are processed at a fixed rate and "no bursts are allowed". It is usually implemented with a first-in-first-out (FIFO) queue.

Leaking Bucket is all about regularity and smoothing out spikes.
"""

import time
import threading
from collections import deque

class LeakingBucket():
  def __init__(self, capacity: int, leak_rate: float):
    """
    :param capacity: Max request the bucket (queue) can hold
    :param leak_rate: Requests processed per second (the 'drip').
    """
    self.capacity = capacity
    self.leak_rate = leak_rate
    # We store the requests in a double-ended queue (FIFO)
    # deque provides O(1) removals from the front, perfect for a FIFO queue.
    self.bucket = deque()
    self.last_leak_time = time.monotonic()
    # Lock to ensure atomic operations across multiple threads.
    self._lock = threading.Lock()

  def add_request(self, request_id: str) -> bool:
    """
    Attempts to add a request to the bucket.
    Returns True if accepted, False if the bucket is full (overflow).
    """
    with self._lock:
      self._leak_requests()
      
      # Check if there's room in the queue
      if len(self.bucket) < self.capacity:
        self.bucket.append(request_id)
        return True
      
      # Bucket is full; discard the request (Standard Leaking Bucket behavior)
      return False

  def _leak_requests(self):
    """
    Logic to remove requests from the bucket based on elapsed time.
    """
    now = time.monotonic()
    elapsed = now - self.last_leak_time

    # Calculate how many requests should have 'leaked' out by now
    leaked_count = int(elapsed * self.leak_rate)
        
    if leaked_count > 0:
      # Remove the oldest requests from the queue
      for _ in range(min(leaked_count, len(self.bucket))):
        self.bucket.popleft()
      
      # Move the clock forward only by the time corresponding to full requests
      time_per_request = 1 / self.leak_rate
      self.last_leak_time += leaked_count * time_per_request