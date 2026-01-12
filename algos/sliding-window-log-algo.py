import time
import threading

class SlidingWindowLog():
    def __init__(self, limit: int, window_size: int):
      # The maximum number of requests we allow in any rolling period.
      self.limit = limit
      # The duration of our rolling window in seconds (e.g., 10 seconds).
      self.window_size = window_size
      # This list acts as our 'log'. It stores the float timestamp of every accepted request.
      self.log = list()
      # We use a Lock to prevent two simultaneous requests from corrupting the log list.
      self._lock = threading.Lock()

    def allow_request(self) -> bool:
      # Step 1: Get the current time exactly when the request hits the server.
      now = time.time()
      
      # Step 2: Calculate the 'cutoff' point. 
      # Anything older than (now - window_size) is irrelevant to our current limit.
      window_start = now - self.window_size

      with self._lock:
        # Step 3: THE CLEANUP 🧹
        # We recreate the list, keeping only timestamps that are LARGER than our window_start.
        # This 'slides' the window forward by dropping the expired history.
        self.log = [timestamp for timestamp in self.log if timestamp > window_start]

        # Step 4: THE DECISION ⚖️
        # We check the size of our cleaned-up log. 
        # If we haven't hit the 'limit' yet, this new request is welcome.
        if len(self.log) < self.limit:
          # Store the exact time this request was accepted so it can be 
          # used to throttle future requests.
          self.log.append(now)
          return True
        
        # If the log is already at the limit, we don't append 'now' and we return False.
        return False