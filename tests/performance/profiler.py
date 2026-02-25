"""
Performance Testing Suite for ws-availability

This module provides tools for profiling and benchmarking the Flask application.
Run with: python tests/performance/profiler.py
"""
import cProfile
import pstats
import time
import json
from io import StringIO
from pstats import SortKey
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Set test environment
os.environ['RUNMODE'] = 'test'

from start import app


class PerformanceProfiler:
    """Profile Flask application endpoints"""
    
    def __init__(self):
        self.client = app.test_client()
        self.results = {}
    
    def profile_endpoint(self, endpoint, params, name=None):
        """
        Profile a single endpoint request
        
        Args:
            endpoint: URL path (e.g., '/query')
            params: Query parameters as dict
            name: Optional name for the test
        """
        test_name = name or f"{endpoint}_{params.get('net', 'default')}"
        print(f"\n{'='*60}")
        print(f"Profiling: {test_name}")
        print(f"URL: {endpoint}?{self._dict_to_query(params)}")
        print(f"{'='*60}\n")
        
        # Create profiler
        profiler = cProfile.Profile()
        
        # Profile the request
        profiler.enable()
        start_time = time.perf_counter()
        
        response = self.client.get(f"{endpoint}?{self._dict_to_query(params)}")
        
        end_time = time.perf_counter()
        profiler.disable()
        
        # Calculate metrics
        elapsed = end_time - start_time
        status = response.status_code
        size = len(response.data)
        
        # Store results
        self.results[test_name] = {
            'elapsed': elapsed,
            'status': status,
            'size_bytes': size,
            'timestamp': datetime.now().isoformat()
        }
        
        # Print summary
        print(f"Status: {status}")
        print(f"Response Size: {size:,} bytes ({size/1024:.2f} KB)")
        print(f"Total Time: {elapsed:.4f} seconds")
        print(f"Throughput: {size/elapsed/1024:.2f} KB/s")
        
        # Print top functions
        print(f"\n{'─'*60}")
        print("Top 20 Functions by Cumulative Time:")
        print(f"{'─'*60}")
        
        s = StringIO()
        stats = pstats.Stats(profiler, stream=s)
        stats.sort_stats(SortKey.CUMULATIVE)
        stats.print_stats(20)
        print(s.getvalue())
        
        return response
    
    def benchmark_endpoint(self, endpoint, params, iterations=10, name=None):
        """
        Benchmark endpoint with multiple iterations
        
        Args:
            endpoint: URL path
            params: Query parameters
            iterations: Number of times to run
            name: Optional test name
        """
        test_name = name or f"{endpoint}_benchmark"
        print(f"\n{'='*60}")
        print(f"Benchmarking: {test_name} ({iterations} iterations)")
        print(f"URL: {endpoint}?{self._dict_to_query(params)}")
        print(f"{'='*60}\n")
        
        times = []
        sizes = []
        
        for i in range(iterations):
            start = time.perf_counter()
            response = self.client.get(f"{endpoint}?{self._dict_to_query(params)}")
            elapsed = time.perf_counter() - start
            
            times.append(elapsed)
            sizes.append(len(response.data))
            
            print(f"Iteration {i+1}/{iterations}: {elapsed:.4f}s ({response.status_code})")
        
        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        avg_size = sum(sizes) / len(sizes)
        
        # Calculate percentiles
        sorted_times = sorted(times)
        p50 = sorted_times[len(sorted_times) // 2]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        print(f"\n{'─'*60}")
        print("Statistics:")
        print(f"{'─'*60}")
        print(f"Average Time: {avg_time:.4f}s")
        print(f"Min Time: {min_time:.4f}s")
        print(f"Max Time: {max_time:.4f}s")
        print(f"P50 (Median): {p50:.4f}s")
        print(f"P95: {p95:.4f}s")
        print(f"P99: {p99:.4f}s")
        print(f"Avg Response Size: {avg_size:,.0f} bytes ({avg_size/1024:.2f} KB)")
        print(f"Throughput: {avg_size/avg_time/1024:.2f} KB/s")
        
        self.results[test_name] = {
            'iterations': iterations,
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'p50': p50,
            'p95': p95,
            'p99': p99,
            'avg_size': avg_size,
            'timestamp': datetime.now().isoformat()
        }
    
    def save_results(self, filename='performance_results.json'):
        """Save all results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✅ Results saved to {filename}")
    
    @staticmethod
    def _dict_to_query(params):
        """Convert dict to query string"""
        return '&'.join([f"{k}={v}" for k, v in params.items()])


def run_performance_tests():
    """Run comprehensive performance test suite"""
    profiler = PerformanceProfiler()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║       WS-AVAILABILITY PERFORMANCE TESTING SUITE              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Test 1: Small query (single station, 1 week)
    profiler.profile_endpoint(
        '/query',
        {'net': 'NL', 'sta': 'HGN', 'start': '2023-01-01', 'end': '2023-01-07'},
        name='small_query'
    )
    
    # Test 2: Medium query (network, 1 month)
    profiler.profile_endpoint(
        '/query',
        {'net': 'NL', 'start': '2023-01-01', 'end': '2023-02-01'},
        name='medium_query'
    )
    
    # Test 3: Extent query
    profiler.profile_endpoint(
        '/extent',
        {'net': 'NA', 'start': '2023-02-01'},
        name='extent_query'
    )
    
    # Test 4: JSON format
    profiler.profile_endpoint(
        '/query',
        {'net': 'NL', 'start': '2023-01-01', 'format': 'json'},
        name='json_format'
    )
    
    # Test 5: Benchmark cache effectiveness (run same query 10 times)
    print("\n" + "="*60)
    print("CACHE EFFECTIVENESS TEST")
    print("="*60)
    profiler.benchmark_endpoint(
        '/query',
        {'net': 'NL', 'sta': 'HGN', 'start': '2023-01-01'},
        iterations=10,
        name='cache_test'
    )
    
    # Save results
    profiler.save_results('tests/performance/results.json')
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                  TESTING COMPLETE                            ║
╚══════════════════════════════════════════════════════════════╝
    """)


if __name__ == '__main__':
    run_performance_tests()
