import time
import threading

class SlidingWindowCounter:
    def __init__(self, limit: int, window_size: int):
      """
      :param limit: Max requests allowed in the sliding period.
      :param window_size: Size of each fixed window in seconds.
      """
      self.limit = limit
      self.window_size = window_size
      # Metadata storage: {10:00:00_id: 80, 10:01:00_id: 10}
      self.counts = {}
      self._lock = threading.Lock()

    def allow_request(self) -> bool:
      """
      Approximates the sliding window count using a weighted average of the current and previous fixed windows.
      """
      now = time.time()
      # 1. Identify the current fixed window (e.g., the '10:01' bucket)
      current_window = int(now / self.window_size)
      
      # 2. Calculate our position in the window.
      # If it's 10:01:30, we are 30s into a 60s window. 
      # overlap_percentage = 30 / 60 = 0.5 (50% through)
      overlap_percentage = (now % self.window_size) / self.window_size

      # 3. Calculate how much of the previous window still 'matters'.
      # If we are 50% into the current minute, the 'sliding' 60s window 
      # covers the last 30s of the previous minute.
      # previous_window_weight = 1 - 0.5 = 0.5
      previous_window_weight = 1 - overlap_percentage

      with self._lock:
        # 4. Fetch the raw counts from our dictionary.
        current_count = self.counts.get(current_window, 0)
        previous_count = self.counts.get(current_window - 1, 0)

        # 5. THE SOLUTION TO DOUBLE-DRIP:
        # Instead of a hard reset, we estimate:
        # (80 requests in prev * 0.5 weight) + (current requests)
        # Estimated = 40 + current_count
        estimated_count = (previous_count * previous_window_weight) + current_count

        # 6. Admission Control
        if estimated_count < self.limit:
          self.counts[current_window] = current_count + 1
          self._cleanup(current_window)
          return True
        
        return False

    def _cleanup(self, current_window: int):
      """Removes windows older than the previous one."""
      # We only care about 'now' and 'just before now'. 
      # Everything else is stale data. 🧹
      keys_to_del = [w for w in self.counts if w < current_window - 1]
      for w in keys_to_del:
        del self.counts[w]