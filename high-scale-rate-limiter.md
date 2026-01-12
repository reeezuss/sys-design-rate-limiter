# 🛡️ System Design: High-Scale Distributed Rate Limiter

## 📖 Executive Summary

A rate limiter is a critical defense mechanism used to control the rate of traffic sent by a client to a server. This project documents the transition from local algorithmic implementations to a production-grade, distributed system capable of handling **10M+ Daily Active Users (DAU)**.

---

## 🏗️ 1. Core Architectures & Trade-offs

### The "Goldilocks" Algorithm: Sliding Window Counter

While we implemented five algorithms (Token Bucket, Leaking Bucket, Fixed Window, Sliding Window Log, and Sliding Window Counter), the **Sliding Window Counter** is the preferred choice for high-scale APIs.

* **Mechanism:** Uses a weighted average of the current and previous fixed-time windows to estimate the current request rate.
* **Formula:** 
* **Why:** It eliminates the "Boundary Problem" (bursts at the edge of fixed windows) without the  memory cost of storing every timestamp.

---

## ⚡ 2. Distributed Strategy: Redis + Lua

To scale across multiple application servers, we move state out of local RAM and into **Redis**.

### Atomicity & Performance

In a distributed environment, the "Check-then-Increment" pattern is vulnerable to **Race Conditions**.

* **Traditional Solution:** Distributed Locks (High overhead, slow).
* **Production Solution:** **Redis Lua Scripting**.

By executing the logic inside Redis as a Lua script, we ensure the entire operation is **atomic** (runs as a single unit) and minimize network latency by reducing round-trips.

#### Production Lua Snippet (Sliding Window Counter)

```lua
-- KEYS[1]: current_window_key, KEYS[2]: prev_window_key
-- ARGV[1]: weight, ARGV[2]: limit, ARGV[3]: expiry_seconds

local curr_count = tonumber(redis.call('GET', KEYS[1]) or "0")
local prev_count = tonumber(redis.call('GET', KEYS[2]) or "0")
local estimated = (prev_count * tonumber(ARGV[1])) + curr_count

if estimated < tonumber(ARGV[2]) then
    redis.call('INCR', KEYS[1])
    redis.call('EXPIRE', KEYS[1], ARGV[3])
    return 1 -- Allowed
end
return 0 -- Throttled

```

---

## 🧮 3. Back-of-the-Envelope Estimation (10M DAU)

To ensure the system is viable, we perform a capacity planning exercise:

* **Traffic:** 10M users @ 20 requests/day  2,000 Avg RPS. Peak (2x)  **4,000 RPS**.
* **Memory:** Each user requires ~200 bytes in Redis (Keys + Counters + Metadata).
*  **2 GB RAM**.


* **Bandwidth:** Each check is ~500 bytes (Request + Response).
*  **2 MB/s**.



**Conclusion:** A single medium-sized Redis node can handle the entire 10M user load, but we use a **Redis Cluster** for high availability.

---

## 💾 4. Persistence & Reliability

### Data Sharding

Redis Cluster uses **Hash Slots**. Requests for `user_123` always map to the same Redis node. This prevents synchronization lag between nodes—the node owning the slot is always the single source of truth for that user.

### Handling Shutdowns (RAM Volatility)

If Redis restarts, we use two mechanisms to recover data:

1. **AOF (Append Only File):** Logs every write operation. Best for durability but slower.
2. **RDB (Snapshot):** Point-in-time binary backups. Faster to load but risks small data loss.

* **Startup Tip:** For rate limiting, "Soft State" is often acceptable. We prioritize **RAM-only performance**; if counters reset on a rare crash, the system self-heals within one window duration (e.g., 60 seconds).

---

## 🛡️ 5. Resiliency: Fail-Open Strategy

If the Redis cluster is unreachable, the system must not crash. We implement **Graceful Degradation**:

1. **Fail-Open:** If the middleware times out reaching Redis, we allow the request.
2. **Local Fallback:** The application server reverts to its own local memory `FixedWindowCounter` as a temporary safety net until Redis connectivity is restored.

---

## 📊 Summary Comparison

| Feature | Local Memory | Redis (Single) | Redis Cluster |
| --- | --- | --- | --- |
| **Consistency** | None (Node-specific) | Strong (Global) | Strong (via Sharding) |
| **Availability** | High | Single Point of Failure | High (Replica Failover) |
| **Latency** | < 1ms | 1-2ms | 1-2ms |
| **Scalability** | Vertical only | Vertical only | Horizontal (Add Nodes) |

---