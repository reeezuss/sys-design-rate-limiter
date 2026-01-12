import time
import requests
from concurrent.futures import ThreadPoolExecutor

API_URL = "http://localhost:8000/api/secure"

def make_request(i):
    resp = requests.get(API_URL)
    print(f"Req {i}: Status {resp.status_code} | {resp.json().get('detail', 'Success')}")

def simulate_burst(n):
    print(f"--- Sending {n} requests ---")
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(make_request, range(n))

if __name__ == "__main__":
    # Test 1: First burst (Limit is 5 per 60s)
    simulate_burst(7)
    
    print("\nWaiting 5 seconds to test sliding weight...")
    time.sleep(5)
    
    # Test 2: Should still be blocked or partially allowed depending on window slide
    simulate_burst(2)