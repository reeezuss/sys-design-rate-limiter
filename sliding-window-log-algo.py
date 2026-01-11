"""
This algorithm maintains a log of timestamps for all requests. For every new request, it discards timestamps older than the window duration and calculates the remaining log size.
"""

import time
import threading

class SlidingWindowLog():
  def __init__(self, limit: int, window_size: int):
    """
    :param limit: Maximum requests allowed in the rolling window.
    :param window_size: The rolling window duration in seconds.
    """
    self.limit = limit
    self.window_size = window_size
    # The 'Log': A list of timestamps for every successful request.
    self.log = list()
    # Thread safety is critical as we are modifying a shared list.
    self._lock = threading.Lock()

  def allow_request(self) -> bool:
    """
    Determines if a request is allowed by looking at the exact 
    history of the last 'window_size' seconds.
    """
    now = time.time()
    # Define the boundary of our rolling window
    window_start = now - self.window_size

    with self._lock:
      # 1. CLEANUP: Filter the log to remove timestamps older than window_start.
      # Only requests within the last 'window_size' seconds stay.
      self.log = [timestamp for timestamp in self.log if timestamp > window_start]

      # 2. CHECK: If the number of logs is under the limit, we allow it
      if len(self.log) < self.limit:
        self.log.append(now)
        return True
      
      # Limit reached: request is dropped
      return False