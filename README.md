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

## Token Bucket Algorithm

### Core Components
- The Bucket: A container for tokens. Its Capacity defines the maximum burst of requests the system can handle at once.
- Tokens: A "unit of permission." Every request must "spend" a token to proceed.
- Refill Rate: The speed at which tokens are added back to the bucket. This defines the Sustained Rate of your API (e.g., if refill is 10/sec, you average 10 requests per second long-term).
- Lazy Refill Strategy: Instead of a background thread constantly adding tokens (which wastes resources), we calculate the refill amount only when a request actually hits the system.

### Practical Scenarios
> Let's use a bucket where Capacity = 100 and Refill Rate = 10 tokens/second.

#### Scenario A: The Morning Rush (Bursting) ☕
- Initial State: The bucket has been idle all night. tokens = 100.
- Action: At 9:00:00 AM, a script sends 110 requests instantly.
- Execution:
  - The first 100 requests find tokens available and pass through.
  - self.tokens drops to 0.
  - Requests 101 through 110 call _refill(). Since 0 seconds have passed, new_tokens is 0. They are rejected.
- Result: You successfully "burst" 100 requests, but the system protected itself from the extra 10.

#### Scenario B: The Steady Drip (Sustained Traffic) 💧
- Initial State: The bucket is empty (tokens = 0) right after Scenario A.
- Action: The user sends 1 request every 0.1 seconds.
- Execution:
  - Request 1 arrives 0.1s later. elapsed = 0.1.
  - new_tokens = 0.1 * 10 = 1 token.
  - The bucket now has 1 token. The request is accepted. tokens becomes 0.
  - Request 2 arrives 0.1s later. The cycle repeats.
- Result: The user is now locked into the refill_rate. They can only go as fast as the "drip" allows.

#### Scenario C: The Recovery (Idle Time) 🛌
- Initial State: Bucket is empty (tokens = 0).
- Action: No one sends a request for 5 seconds. Then, 1 request arrives.
- Execution:
  - elapsed = 5.0.
  - new_tokens = 5.0 * 10 = 50 tokens.
  - tokens = min(100, 0 + 50) = 50.
  - The request is accepted. tokens becomes 49.
- Result: The system "remembered" the idle time and built up a new credit of 50 tokens for the user to use later.

### Advantages
- Supports Bursts: Unlike other algorithms, this allows a user to send a spike of traffic as long as they have "saved up" tokens.
- Memory Efficient: You only need to store two numbers (token count and last timestamp) per user/key.
- Flexible: Different endpoints can require different numbers of tokens (e.g., a heavy POST costs 5 tokens, while a light GET costs 1).

------------------------------------------------------------------------------

## Leaking Bucket Algorithm

