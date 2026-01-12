"""
We use integer division on the current Unix timestamp to create discrete, non-overlapping blocks of time. Each block (window) is assigned a unique integer ID.
This algorithm is static in nature in comparison to token bucket and leaking bucket.
Most basic kind of rate limiting algorithm for APIs like 1000 request per hour, etc.
"""

import time
import threading

class FixedWindowCounter():
  def __init__(self, limit: int, window_size: int):
    """
    :param limit: Maximum requests allowed per window
    :param window_size: Size of the window in seconds (e.g., 60 for 1 minute)
    """
    self.limit = limit
    self.window_size = window_size
    # A hash map (dictionary) where:
    # Key = The Window ID (a timestamp)
    # Value = The integer count of requests made in that window.
    self.windows = dict()

    self._lock = threading.Lock()

  def allow_request(self) -> bool:
    """
    Checks if a request is allowed within the current fixed time window
    """
    # Calculate which 'bucket' of time we are currently in.
    # We take the current Unix timestamp and divide by the window size.
    # Example: If it's 10:00:15 (timestamp 1700000015) and window is 60s,
    # 1700000015 // 60 = 28333333.
    # Every second from 10:00:00 to 10:00:59 will result in the same ID.
    current_window = int(time.time() / self.window_size)

    with self._lock:
      # If this is the first request in this specific window, initialize it to zero.
      if current_window not in self.windows:
        self.windows[current_window] = 0

        # Housekeeping: Remove old windows from memory so the dictionary doesn't grow forever.
        self._cleanup(current_window)

      # Check if the user has already hit the ceiling.
      if self.windows[current_window] < self.limit:
        # Increment the counter and allow the request through.
        self.windows[current_window] += 1
        return True
      
      # Request blocked: Limit exceeded for this fixed time block.
      return False

  def _cleanup(self, current_window: int): 
    """
    Removes all window data older than the current active window.
    """
    # We identify keys that represent 'past' time.
    old_windows = [w for w in self.windows if w < current_window]
    for w in old_windows:
      # Delete them from the dictionary to free up memory.
      del self.windows[w]
