# Design a rate limiter for distributed environment

> We need to use an in-memory data store (like Redis) which all nodes can reach and it supports **atmoic operations (thread-safety)** so that we can prevent race conditions.

## Sliding Window Counter in a distributed way using Redis.
- Instead of a Python dictionary, we use Redis keys to store our counts.
  - Key Format: rate_limit:{user_id}:{window_timestamp}
  - Expiration: We set a Time-To-Live (TTL) on these keys so Redis automatically cleans up old windows for us. 🧹

### Production-Grade Simulation (Python + Redis) 🐍
```py
import time
import redis # High-performance Redis client

class RedisSlidingWindowCounter:
    def __init__(self, redis_client, limit: int, window_size: int):
        self.redis = redis_client
        self.limit = limit
        self.window_size = window_size

    def allow_request(self, user_id: str) -> bool:
        now = time.time()
        current_window = int(now / self.window_size)
        prev_window = current_window - 1
        
        # Calculate weights for the sliding window approximation
        overlap_percentage = (now % self.window_size) / self.window_size
        prev_weight = 1 - overlap_percentage

        # Define Redis keys for this specific user
        curr_key = f"rl:{user_id}:{current_window}"
        prev_key = f"rl:{user_id}:{prev_window}"

        # 1. Fetch counts from Redis
        # We use mget to fetch both keys in a single network round-trip
        counts = self.redis.mget([curr_key, prev_key])
        curr_count = int(counts[0]) if counts[0] else 0
        prev_count = int(counts[1]) if counts[1] else 0

        # 2. Calculate the estimated sliding count
        estimated = (prev_count * prev_weight) + curr_count

        if estimated < self.limit:
            # 3. Increment the current window counter
            # pipeline ensures these commands are sent together
            pipe = self.redis.pipeline()
            pipe.incr(curr_key)
            # Set expiry to window_size * 2 so it lasts long enough to be a 'prev_window'
            pipe.expire(curr_key, self.window_size * 2)
            pipe.execute()
            return True
        
        return False
```

### The Interview "Gotcha": Race Conditions 🏃💨
> Even with Redis, there is a small "race" in the code above. Look at the gap between fetching the counts and incrementing the counter. If two different servers run `allow_request` for the same user at the same time, they might both see `estimated < limit` and both increment, effectively letting 2 requests in when only 1 was allowed.
> To solve this in a real interview, you should mention Lua Scripts. Redis can execute a Lua script as a single atomic unit—meaning no other server can "interfere" while the script is running the math.
> **The solution is here is not Redis but an in-memory data storage with atmoic operations so that race conditions are prevented**

#### Designing for failure in a high-pace startup environment is all about graceful degradation. We want the system to stay up even if our "policing" mechanism (Redis) goes offline. 🛠️

In a system design interview, a solid strategy is to implement a fail-open approach with local fallback. Here is how we can break that plan down:

1. The Fail-Open Strategy 🔓
  - If the code can't connect to Redis, we don't want to block 100% of our traffic (that's a self-inflicted DDoS). Instead, we "fail-open," meaning we let the request through but log an error for the engineering team to investigate.
2. Local Memory Fallback 💾
  - To prevent being completely unprotected while Redis is down, each application server can maintain its own tiny Fixed Window Counter in its local RAM.
    - It won't be as accurate as the distributed version (since servers aren't sharing data).
    - However, it provides a "safety net" that prevents any single server from being overwhelmed by a single rogue client.

### Implementation Plan for Designing a Rate Limiter 🏛️
- If you were asked to "Design a Rate Limiter" in a 45-minute interview, we would finalize the plan using these five pillars:
  - Functional Requirements: Define the scale (millions of users) and the types of limits (per IP, per UserID).
  - Algorithm Selection: Choose the Sliding Window Counter (as the "Goldilocks" choice) or Token Bucket (for burst support).
  - Data Schema: Use Redis with keys like rl:{user_id}:{timestamp} and TTLs for auto-cleanup.
  - Distributed Logic: Use Lua Scripts to make the "Check-and-Increment" step atomic. 🔒
  - High Availability: Discuss the fail-open/local fallback mentioned above.