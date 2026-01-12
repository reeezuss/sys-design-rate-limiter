from fastapi import FastAPI, Depends
from limiter import RateLimiter

app = FastAPI(title="High-Scale Rate Limited API")

# Configuration: 5 requests per 60 seconds
# This dependency can be applied globally or per-route
standard_limiter = RateLimiter(limit=5, window=60)

@app.get("/")
async def root():
    return {"message": "Public access - No limit"}

@app.get("/api/secure", dependencies=[Depends(standard_limiter)])
async def secure_data():
    """
    This endpoint is protected by the Sliding Window Counter.
    """
    return {
        "status": "success",
        "data": "This is protected production-grade data."
    }

@app.get("/api/heavy", dependencies=[Depends(RateLimiter(limit=2, window=10))])
async def heavy_task():
    """
    Specific limit for expensive operations (2 requests per 10s).
    """
    return {"message": "Expensive computation successful"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)