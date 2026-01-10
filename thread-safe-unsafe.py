import threading
import time

"""
In this scenario, multiple threads try to increment a counter. Because count += 1 is actually three steps in Python bytecode (Read, Increment, Write), threads will "step on each other."

A function is said to be thread-safe if and only if it will always produce correct results when called repeatedly from multiple concurrent threads.
"""
class UnsafeCounter:
  def __init__(self):
    self.value = 0

  def increment(self):
    current = self.value
    time.sleep(0.000001)
    self.value = current + 1

class SafeCounter:
  def __init__(self):
    self.value = 0
    self._lock = threading.Lock() # lock for thread-safe counter
  
  def increment(self):
    with self._lock:
      current = self.value
      time.sleep(0.000001)
      self.value = current + 1

def worker(counter, updates):
  for _ in range(updates):
    counter.increment()

# Simulation of safe, unsafe counter logic
updates_per_thread = 100

unsafe_counter = UnsafeCounter()
safe_counter = SafeCounter()

threads = [threading.Thread(target=worker, args=(unsafe_counter, updates_per_thread)) for _ in range(10)]
safe_threads = [threading.Thread(target=worker, args=(safe_counter, updates_per_thread)) for _ in range(10)]

print(f"Target Value: {10 * updates_per_thread}")

for t in threads: t.start()
for t in threads: t.join()
print(f"Final Unsafe Value: {counter.value}")

for t in safe_threads: t.start()
for t in safe_threads: t.join()
print(f"Final Safe Value: {counter.value}")
