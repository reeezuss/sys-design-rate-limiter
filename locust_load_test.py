from locust import HttpUser, task, between, events
import random

class APIUser(HttpUser):
    # Wait between 0.1 and 0.5 seconds between tasks to simulate real traffic
    wait_time = between(0.1, 0.5)

    @task(3)  # Higher weight: Users check stats more often
    def test_marketing_api(self):
        """Tests the marketing endpoint with its specific tier limits."""
        self.client.get("/marketing/stats", name="/marketing/stats")

    @task(1)  # Lower weight: Payments are less frequent but more critical
    def test_payment_api(self):
        """Tests the payment endpoint."""
        self.client.post("/payments/charge", name="/payments/charge")

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    if exception:
        # In a real startup, we track 429s in Grafana
        print(f"Request to {name} failed: {exception}")