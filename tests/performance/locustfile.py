"""
Locust Load Testing for ws-availability

Install: pip install locust
Run: locust -f tests/performance/locustfile.py --host=http://localhost:9001
Web UI: http://localhost:8089
"""
from locust import HttpUser, task, between, events
import random
from datetime import datetime, timedelta


class AvailabilityUser(HttpUser):
    """
    Simulates a user making requests to the ws-availability service
    """
    # Wait 1-3 seconds between requests
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts"""
        self.networks = ['NL', 'NA', 'GR', 'FR', 'IT']
        self.stations = ['HGN', 'SABA', 'DBN', 'G014', '*']
        self.formats = ['text', 'json', 'geocsv']
    
    @task(5)
    def query_recent_data(self):
        """
        Most common use case: Query recent data (last 30 days)
        Weight: 5 (50% of requests)
        """
        net = random.choice(self.networks)
        start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        self.client.get(
            f"/query?net={net}&start={start}",
            name="/query [recent]"
        )
    
    @task(3)
    def query_specific_station(self):
        """
        Query specific station with date range
        Weight: 3 (30% of requests)
        """
        net = random.choice(self.networks)
        sta = random.choice(self.stations)
        start = '2023-01-01'
        end = '2023-02-01'
        
        self.client.get(
            f"/query?net={net}&sta={sta}&start={start}&end={end}",
            name="/query [station]"
        )
    
    @task(2)
    def extent_query(self):
        """
        Extent query (aggregated data)
        Weight: 2 (20% of requests)
        """
        net = random.choice(self.networks)
        start = '2023-01-01'
        
        self.client.get(
            f"/extent?net={net}&start={start}",
            name="/extent"
        )
    
    @task(1)
    def query_different_formats(self):
        """
        Test different output formats
        Weight: 1 (10% of requests)
        """
        net = random.choice(self.networks)
        fmt = random.choice(self.formats)
        start = '2023-01-01'
        
        self.client.get(
            f"/query?net={net}&start={start}&format={fmt}",
            name=f"/query [format={fmt}]"
        )
    
    @task(1)
    def version_check(self):
        """
        Version endpoint (lightweight)
        Weight: 1 (10% of requests)
        """
        self.client.get("/version", name="/version")


class HeavyUser(HttpUser):
    """
    Simulates heavy users making large queries
    """
    wait_time = between(5, 10)
    
    @task
    def large_query(self):
        """Query large date range"""
        self.client.get(
            "/query?net=*&start=2023-01-01&end=2023-12-31",
            name="/query [heavy]"
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print test configuration"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         LOCUST LOAD TEST - WS-AVAILABILITY                   ║
╚══════════════════════════════════════════════════════════════╝

Test Scenarios:
  - AvailabilityUser: Normal user traffic (50% recent queries)
  - HeavyUser: Large queries (optional)

Access Web UI: http://localhost:8089

Recommended Settings:
  - Start: 10 users
  - Spawn rate: 2 users/sec
  - Duration: 5-10 minutes

Example CLI:
  locust -f locustfile.py --host=http://localhost:9001 \\
         --users 50 --spawn-rate 5 --run-time 5m --headless
    """)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log slow requests"""
    if response_time > 2000:  # > 2 seconds
        print(f"⚠️  SLOW REQUEST: {name} took {response_time}ms")
