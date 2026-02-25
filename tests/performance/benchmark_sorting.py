"""
Quick benchmark to demonstrate sorting optimization impact

Before: 3 separate sort passes
After: 1 single compound key sort

Run with: python tests/performance/benchmark_sorting.py
"""
import time
import random
from datetime import datetime, timedelta

# Simulate data structure
QUALITY = 4
SAMPLERATE = 5
START = 6
END = 7

def generate_test_data(n=10000):
    """Generate random test data"""
    networks = ['NL', 'NA', 'GR', 'FR', 'IT']
    stations = ['HGN', 'SABA', 'DBN', 'G014', 'TEST']
    locations = ['', '00', '10']
    channels = ['BHZ', 'BHN', 'BHE', 'HHZ']
    qualities = ['D', 'M', 'Q', 'R']
    
    data = []
    base_time = datetime(2023, 1, 1)
    
    for i in range(n):
        start_time = base_time + timedelta(days=random.randint(0, 365))
        end_time = start_time + timedelta(hours=24)
        
        row = [
            random.choice(networks),    # 0: Network
            random.choice(stations),    # 1: Station
            random.choice(locations),   # 2: Location
            random.choice(channels),    # 3: Channel
            random.choice(qualities),   # 4: Quality
            random.choice([20.0, 40.0, 100.0]),  # 5: SampleRate
            start_time,                 # 6: START
            end_time,                   # 7: END
        ]
        data.append(row)
    
    return data


def old_sort_method(data):
    """Original: 3 separate sort passes"""
    data_copy = [row[:] for row in data]  # Deep copy
    
    # Pass 1: Quality and SampleRate
    data_copy.sort(key=lambda x: (x[QUALITY], x[SAMPLERATE]))
    # Pass 2: Time
    data_copy.sort(key=lambda x: (x[START], x[END]))
    # Pass 3: NSLC
    data_copy.sort(key=lambda x: x[:QUALITY])
    
    return data_copy


def new_sort_method(data):
    """Optimized: Single compound key sort"""
    data_copy = [row[:] for row in data]  # Deep copy
    
    data_copy.sort(key=lambda x: (
        x[0],           # Network
        x[1],           # Station
        x[2],           # Location
        x[3],           # Channel
        x[START],       # Start time
        x[END],         # End time
        x[QUALITY],     # Quality
        x[SAMPLERATE]   # Sample rate
    ))
    
    return data_copy


def benchmark_sorting(sizes=[1000, 5000, 10000, 50000]):
    """Benchmark both methods"""
    print("="*70)
    print("SORTING OPTIMIZATION BENCHMARK")
    print("="*70)
    print()
    
    results = []
    
    for size in sizes:
        print(f"Testing with {size:,} records...")
        data = generate_test_data(size)
        
        # Benchmark old method
        start = time.perf_counter()
        old_result = old_sort_method(data)
        old_time = time.perf_counter() - start
        
        # Benchmark new method
        start = time.perf_counter()
        new_result = new_sort_method(data)
        new_time = time.perf_counter() - start
        
        # Verify results are identical
        assert old_result == new_result, "Sort results differ!"
        
        speedup = old_time / new_time
        improvement = ((old_time - new_time) / old_time) * 100
        
        results.append({
            'size': size,
            'old_time': old_time,
            'new_time': new_time,
            'speedup': speedup,
            'improvement': improvement
        })
        
        print(f"  Old method (3 passes): {old_time:.4f}s")
        print(f"  New method (1 pass):   {new_time:.4f}s")
        print(f"  Speedup: {speedup:.2f}x ({improvement:.1f}% faster)")
        print()
    
    # Summary
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print()
    print(f"{'Records':<12} {'Old (s)':<12} {'New (s)':<12} {'Speedup':<12} {'Improvement'}")
    print("-"*70)
    
    for r in results:
        print(f"{r['size']:<12,} {r['old_time']:<12.4f} {r['new_time']:<12.4f} "
              f"{r['speedup']:<12.2f}x {r['improvement']:.1f}%")
    
    avg_speedup = sum(r['speedup'] for r in results) / len(results)
    avg_improvement = sum(r['improvement'] for r in results) / len(results)
    
    print()
    print(f"Average speedup: {avg_speedup:.2f}x ({avg_improvement:.1f}% faster)")
    print()
    print("✅ Optimization verified: Single compound sort is faster and produces")
    print("   identical results to the original 3-pass approach.")


if __name__ == '__main__':
    benchmark_sorting()
