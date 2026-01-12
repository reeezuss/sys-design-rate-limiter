# Rate Limiting

> In the HTTP world, a rate limiter limits the number of client requests allowed to be sent over a specified period. If the API request count exceeds the threshold defined by the rate limiter, all the excess calls are blocked. *HTTP Status Code = 429 Too Many Requests*

### Here are a few examples:
- A user can write no more than 2 posts per second.
- You can create a maximum of 10 accounts per day from the same IP address.
- You can claim rewards no more than 5 times per week from the same device.

### Benefits:
- Prevent resource starvation caused by denial of service attacks.
- Prevent excess cost by limiting unnecessary requests
- Prevent overloading of servers

### Ideal Rate Limiter Characterstics (for a startup with huge traffic)
- Low Latency, the rate limiter should not slow down HTTP response time
- High Fault Tolerance (if part of rate limiter like cache dies, it does not effect the entire system).
- Throttle request based on IP address, the user ID or other properties
- Should work in distributed environment (the rate limiter can be shared across multiple servers or processes)
- Should handle large number of requests out of the box and should use minimal resources like memory
- Inform users who have been throttled (Exception Handling)
- Find out kind of rate limiter : Client side or Server side (however not preferred to put rate limiter on client side because it is easier to forge)
- Optional decision: (code part of application or separate service)

### Popular Rate Limiting Algorithms
- Token bucket
- Leaking bucket
- Fixed window counter
- Sliding window log
- Sliding window counter