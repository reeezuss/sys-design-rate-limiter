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

### Core Components
- The Queue (The Bucket): A FIFO structure that holds incoming requests. Its Capacity determines the maximum number of requests that can be "queued" for processing.
- The Drip (Leak Rate): The fixed rate at which requests are removed from the queue and passed to the underlying system.
- Overflow: If a request arrives and the queue is at capacity, it is dropped immediately.

> The primary goal of a Leaking Bucket is **Traffic Smoothing** (shape traffic) and **provide predictability** for downstream systems. If you have a backend database that can only handle exactly 50 queries per second without crashing, a Leaking Bucket ensures that even if a user sends 500 requests in a single second, your database only sees a steady 50/sec stream.

### Practical Scenarios

#### Database Write Smoothing 🗄️
Imagine a high-traffic startup where users are constantly updating their profiles. If 10,000 users hit "Save" at the exact same second, your database might lock up or crash. 💥
- The Bucket: Acts as a buffer for these "write" requests.
- The Leak: We process exactly 100 writes per second—the maximum your database can handle comfortably without increasing latency for other queries.
- The Benefit: You transform a dangerous spike into a manageable, steady stream.

#### Third-Party API Compliance ☁️
Many professional services (like Twilio for SMS or Stripe for payments) have strict, non-negotiable rate limits. If you exceed them, they might block your account or charge heavy penalties. 💸
- The Bucket: Holds your outgoing API calls.
- The Leak: Set precisely to the third party's limit (e.g., 50 requests per second).
- The Benefit: Your application logic can "burst" requests into the bucket, but your outgoing infrastructure ensures you never violate the external provider's terms.

#### Video Ingest & Processing 📽️
In a video-sharing platform, processing a 4K upload is CPU-intensive. If your ingest server tries to process 20 uploads simultaneously, the entire machine might become unresponsive. 🖥️
- The Bucket: A queue of "Processing Jobs."
- The Leak: Jobs are pulled for processing only when CPU resources are available at a constant rate (e.g., 2 videos at a time).
- The Benefit: It prevents "Resource Exhaustion" and ensures that once a process starts, it has the resources to finish.

### Limitations
- Memory: Unlike Token Bucket (which just stores a number), a Leaking Bucket (if implemented as a real queue) needs memory for every item in the queue.
- Latency: It forces a delay on requests during spikes, as they must wait their turn to "leak."

-----------------------------------------------------------------------------------------

## Fixed Window Algorithm

### Core Components
- Window ID: Calculated as current_time / window_size. This ensures every request in a specific 60-second block (or whatever size you choose) hits the same counter.
- Counter: A simple integer that resets mentally every time a new window starts.

### Engineering Trade-offs
- Pros: Extremely memory-efficient (only 1 integer per window) and very fast (O(1) time complexity).
- Cons: Vulnerable to spikes at the edges of windows. Can allow double the intended traffic in a short burst across a boundary.

### Practical Scenarios
- Tiered API Plans: If you offer a "Free Tier" allowing 1,000 requests per day, this algorithm is perfect. It's easy for the user to understand: "My limit resets at midnight."
- Newsletter Signups: To prevent bot spam on a signup form, you might limit a specific IP address to 5 attempts per hour.
- Heavy Computation Endpoints: For an AI startup, you might limit a user to 10 "Image Generations" per minute to ensure your GPU cluster isn't monopolized by one person.

### The Critical Flaw: The "Edge Case" ⚠️
> This algorithm has a major vulnerability known as the "Boundary Problem." Imagine your limit is 100 requests per minute. Because each window is an independent bucket, a user can exhaust the limit at the very end of Window A and immediately use the full limit again at the start of Window B.
- User A sends 100 requests at 10:00:59. (Accepted ✅)
- The window resets at 10:01:00.
- User A sends another 100 requests at 10:01:01. (Accepted ✅)

### How to mitigate this:
- Lower the Limit: Set the limit lower than the actual system capacity to provide a "buffer" for these spikes.
- Use Smaller Windows: Instead of 1,000 requests per hour, use 16 requests per minute. This spreads the "edge" risk over more frequent intervals.

---------------------------------------------------------------------------------------