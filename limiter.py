import time
import logging
import redis
from fastapi import HTTPException, Request

# Setup logging for production monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection Pool for high-performance reuse of connections
pool = redis.ConnectionPool(
    host='localhost', 
    port=6379, 
    decode_responses=True,
    socket_timeout=0.1,  # 100ms timeout to prevent blocking API
    retry_on_timeout=True
)
r = redis.Redis(connection_pool=pool)

class RateLimiter:
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window

    async def __call__(self, request: Request):
        # 1. Identify User (Handles Proxies like Nginx/Cloudflare)
        user_id = request.headers.get("X-Forwarded-For") or request.client.host
        
        try:
            if not self._sliding_window_counter(user_id):
                raise HTTPException(status_code=429, detail="Too Many Requests")
        except redis.exceptions.RedisError as e:
            # FAIL-OPEN: If Redis is down, we log the error and let the request pass.
            # In a multi-million DAU startup, availability > perfect rate limiting.
            logger.error(f"Redis Rate Limiter Error: {e}. Failing open.")
            return

    def _sliding_window_counter(self, user_id: str) -> bool:
        lua_script = """
        local curr_key = KEYS[1]
        local prev_key = KEYS[2]
        local limit = tonumber(ARGV[1])
        local weight = tonumber(ARGV[2])
        local expiry = tonumber(ARGV[3])

        local curr_count = tonumber(redis.call('get', curr_key) or "0")
        local prev_count = tonumber(redis.call('get', prev_key) or "0")
        
        local estimated = (prev_count * weight) + curr_count
        
        if estimated < limit then
            redis.call('incr', curr_key)
            redis.call('expire', curr_key, expiry)
            return 1
        else
            return 0
        end
        """
        now = time.time()
        curr_window = int(now / self.window)
        prev_window = curr_window - 1
        
        # Calculate overlap for the rolling window
        overlap_percent = (now % self.window) / self.window
        weight = 1 - overlap_percent

        keys = [f"rl:{user_id}:{curr_window}", f"rl:{user_id}:{prev_window}"]
        args = [self.limit, weight, self.window * 2]

        return bool(r.eval(lua_script, 2, *keys, *args))