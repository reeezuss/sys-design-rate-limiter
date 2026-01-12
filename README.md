# 🛡️ Production Distributed Rate Limiter (FastAPI + Redis)

## 🏗️ Design Philosophy

This system is designed for **High Availability** and **Low Latency**. In a high-pace startup, we cannot afford for the rate limiter to become a Single Point of Failure (SPOF).

### Key Features

* **Algorithm:** **Sliding Window Counter** (Weighted Average). Solves the "boundary burst" problem without the high memory cost of a sliding log.
* **Atomicity:** Uses **Redis Lua Scripts** to ensure that `GET -> COMPUTE -> INCREMENT` happens as a single atomic operation, preventing race conditions.
* **Resiliency (Fail-Open):** If Redis becomes unavailable or times out (100ms), the system logs the error and allows the traffic through.
* **Efficiency:**  Space and Time complexity per request.

---

## 🧮 Back-of-the-Envelope Estimation (10M DAU)

* **Memory:**  users  200 bytes per record  **2 GB RAM**.
* **Throughput:** ~4,000 Peak RPS.
* **Latency Overhead:** < 2ms per request (due to Connection Pooling and Lua).

---

## 🚀 Deployment Instructions

### 1. Prerequisites

* Python 3.13+
* Redis Server (Running locally or via Docker)
```bash
docker run -d --name redis-limiter -p 6379:6379 redis:alpine

```



### 2. Installation

```bash
pip install fastapi uvicorn redis requests

```

### 3. Running the Project

1. Start the API:
```bash
uvicorn main:app --reload

```


2. Run the tests:
```bash
python test_limiter.py

```



---

## 🛡️ Reliability & Trade-offs

1. **Consistency vs Availability:** We prioritize **Availability**. The `Fail-Open` mechanism ensures that a Redis outage does not result in a global API outage.
2. **Precision:** The Sliding Window Counter is an approximation. It assumes traffic in the previous window was uniformly distributed. For 99% of web APIs, this is the optimal trade-off.
3. **Storage:** We use a `window * 2` TTL (Time-to-Live) on Redis keys. This ensures that stale data is automatically purged, keeping the 2GB RAM estimate stable.

---