import time
import redis
from fastapi import HTTPException, Request
from config import RATE_LIMIT_RULES, get_user_tier

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

class DynamicRateLimiter:
    def __init__(self, service_name: str):
        self.service_name = service_name

    async def __call__(self, request: Request):
        user_id = request.headers.get("X-Forwarded-For") or request.client.host
        
        # PRODUCTION PATTERN: Fetch user tier from Redis (cached from DB)
        # This avoids a slow DB hit on every single API request.
        tier = r.get(f"user:tier:{user_id}") or "free"
        
        service_rules = RATE_LIMIT_RULES.get(self.service_name, RATE_LIMIT_RULES["default"])
        rule = service_rules.get(tier, RATE_LIMIT_RULES["default"])
        
        if not self._sliding_window_counter(user_id, rule["limit"], rule["window"]):
            # Strategic: Include 'Retry-After' header for professional clients
            raise HTTPException(
                status_code=429,
                detail=f"Quota exceeded for {self.service_name}. Tier: {tier}",
                headers={"Retry-After": str(rule["window"] // 2)}
            )

    def _sliding_window_counter(self, user_id: str, limit: int, window: int) -> bool:
        # The same high-performance Lua script we mastered earlier
        lua_script = """
        local curr_key, prev_key = KEYS[1], KEYS[2]
        local limit, weight, expiry = tonumber(ARGV[1]), tonumber(ARGV[2]), tonumber(ARGV[3])

        local curr_count = tonumber(redis.call('get', curr_key) or "0")
        local prev_count = tonumber(redis.call('get', prev_key) or "0")
        
        if (prev_count * weight) + curr_count < limit then
            redis.call('incr', curr_key)
            redis.call('expire', curr_key, expiry)
            return 1
        end
        return 0
        """
        now = time.time()
        curr_window = int(now / window)
        
        overlap = (now % window) / window
        weight = 1 - overlap

        # Key structure now includes the service name to prevent limit-bleeding
        keys = [f"rl:{self.service_name}:{user_id}:{curr_window}", 
                f"rl:{self.service_name}:{user_id}:{curr_window - 1}"]
        
        return bool(r.eval(lua_script, 2, *keys, limit, weight, window * 2))