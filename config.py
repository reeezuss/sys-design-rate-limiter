# Configuration for different service types and user tiers
RATE_LIMIT_RULES = {
    "payments": {
        "free": {"limit": 10, "window": 60},       # 10 req/min
        "pro": {"limit": 100, "window": 60},       # 100 req/min
        "enterprise": {"limit": 1000, "window": 60} # 1000 req/min
    },
    "marketing": {
        "free": {"limit": 50, "window": 3600},     # 50 req/hour
        "pro": {"limit": 500, "window": 3600},     # 500 req/hour
        "enterprise": {"limit": 5000, "window": 3600}
    },
    "default": {"limit": 100, "window": 3600}
}

def get_user_tier(user_id: str) -> str:
    """
    In production, this would be a cache lookup (Redis) or DB call.
    Returning 'free' for demo purposes.
    """
    return "free"