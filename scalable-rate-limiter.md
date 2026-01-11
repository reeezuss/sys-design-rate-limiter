# System Design : Scalable Rate Limiter

## 1. Problem Statement
> Design a high-performance, distributed rate limiter to protect services from abuse, ensure fair usage, and prevent resource exhaustion.

## 2. Algorithm Comparison 📊
| **Token Bucket** 🪙 | Tokens added at fixed rate; consumed per request. | Supports bursts; memory efficient. | Race conditions in distributed setups. | Generic API throttling. |
| **Leaking Bucket** 🚰 | FIFO queue; "leaks" at a constant rate. | Smooths traffic; protects downstream. | Adds latency; queue memory overhead. | Database/Legacy system protection. |
| **Fixed Window** 🪟 | Counters in static time slots (e.g., 1 min). | Very simple; minimal memory. | "Double-dip" bursts at window edges. | Simple hourly/daily quotas. |
| **Sliding Window Log** 🪵 | Stores every timestamp in a rolling window. | 100% accurate; no edge spikes. | High memory usage ($O(N)$). | High-stakes security/finance. |
| **Sliding Window Counter** ⚖️ | Weighted average of current and previous windows. | Smooth; $O(1)$ memory. | Slight approximation error. | **Industry Standard** for scale. |

## 3. Distributed Architecture 🏛️
For a startup-scale environment, a centralized data store is required to keep all application nodes in sync.
### 🧱 Core Components
- Load Balancer: Distributes traffic to API Gateways.
- Rate Limiter Middleware: Executes the logic (Sliding Window Counter) before reaching the backend.
- Redis Cache: Stores request counts and timestamps with TTL (Time-To-Live).
- Configuration Service: Holds the rules (e.g., "User A gets 100 req/min").

## 4. Interview "Deep Dive" Topics 🧠
- ⚡ Performance & Scalability
  - Lua Scripting: To solve race conditions (Read-Modify-Write), use Lua scripts in Redis to make the check-and-increment process atomic.
  - Edge Rate Limiting: For global scale, move rate limiting to the Edge (CDN) to stop malicious traffic before it hits your data center.

- 🛡️ Resiliency (The Fail-Safe)
  - Fail-Open: If Redis is unreachable, allow requests to pass (prioritize availability).
  - Local Fallback: Maintain a secondary, less-strict limit in the server's local RAM as a backup.

----------------------------------------------------------------------------------------

# Back of the envelope estimation

> Three parts: **Requests per Second (RPS)**, **Memory (RAM)**, and **Network Bandwidth**.

1. Estimating Throughput (RPS) 📈 : Let's assume we have 10 million daily active users (DAU).
- Total Requests: If an average user makes 20 API calls per day, that's `10,000,000 * 20 = 200,000,000` requests per day.
- Average RPS: There are roughly 86,400 seconds in a day (let's round to 100,000 for easier interview math). 
  - `200,000,000 / 100,000 = 2,000` requests per second.
- Peak RPS: Traffic isn't flat. We usually assume a "peak" factor of 2x.
  - `2,000 * 2 = 4,000` peak requests per second.

2. Estimating Memory (RAM) 💾 : We need to store the rate limit state in Redis. We're using the Sliding Window Counter algorithm.
- For each user, we need to store:
  - Current Window Key: e.g., rl:user123:window456 (approx. 30 bytes)
  - Current Window Count: an integer (approx. 4 bytes)
  - Previous Window Key: e.g., rl:user123:window455 (approx. 30 bytes)
  - Previous Window Count: an integer (approx. 4 bytes)
- Redis adds some overhead for each key (around 50 bytes). Let's estimate each "user record" (both windows) takes roughly 200 bytes of RAM.
- If we have 10 million users active in a given day, and we want to keep their data in Redis, how much total RAM would we need in gigabytes? (Remember: $1,000,000,000 \text{ bytes} \approx 1 \text{ GB}$).
- If we have 10 million users and each user's state takes up 200 bytes, the calculation is:$10,000,000 \times 200 = 2,000,000,000$ bytes.
- Since 1 GB is roughly 1 billion bytes ($1,000,000,000$), we need 2 GB of RAM 💾 to store our rate-limiting data in Redis. In a real-world startup, 2 GB is quite small—you could easily run this on a single small Redis instance, though you'd likely use a cluster for high availability.

3. Network Bandwidth 🌐 
- To calculate the peak network bandwidth 🌐, we multiply our peak traffic by the data size of each "check" we perform:
  - Peak Traffic: 4,000 requests per second.
  - Data per Request: 500 bytes.
  - Total Throughput: $4,000 \times 500 = 2,000,000$ bytes per second.
- Since 1,000,000 bytes equals 1 Megabyte (MB), our rate limiter uses 2 MB/s of bandwidth at peak. 

#### 📈Is this a bottleneck? 🚦
> In a modern high-pace startup environment, 2 MB/s is almost negligible. Standard 1 Gbps (Gigabit per second) network cards can handle about 125 MB/s. This means our rate limiter is incredibly "light" on the network, leaving plenty of room for actual application data and progress in other areas like financial transactions or video streaming. 🚀