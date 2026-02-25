# Performance Testing Suite

This directory contains tools for profiling and benchmarking the ws-availability service.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r tests/performance/requirements.txt
```

### 2. Run Quick Tests
```bash
# Make sure service is running first
RUNMODE=test gunicorn --workers 2 --bind 0.0.0.0:9001 start:app

# In another terminal
bash tests/performance/quick_test.sh
```

### 3. Run Detailed Profiling
```bash
python tests/performance/profiler.py
```

### 4. Analyze MongoDB Performance
```bash
python tests/performance/mongo_analyzer.py
```

### 5. Run Load Tests
```bash
# Start Locust web UI
locust -f tests/performance/locustfile.py --host=http://localhost:9001

# Or run headless
locust -f tests/performance/locustfile.py --host=http://localhost:9001 \
       --users 50 --spawn-rate 5 --run-time 5m --headless
```

## Tools Overview

### profiler.py
- **Purpose**: Profile individual endpoints with cProfile
- **Output**: Function-level timing, cumulative time analysis
- **Use when**: Identifying slow functions in the code

### locustfile.py
- **Purpose**: Load testing with realistic user scenarios
- **Output**: Requests/sec, response times, failure rates
- **Use when**: Testing under concurrent load

### mongo_analyzer.py
- **Purpose**: Analyze MongoDB query performance
- **Output**: Query plans, index usage, optimization recommendations
- **Use when**: Database queries are slow

### quick_test.sh
- **Purpose**: Fast smoke test of common endpoints
- **Output**: Response times and sizes
- **Use when**: Quick validation after changes

## Performance Metrics to Track

| Metric | Target | Tool |
|--------|--------|------|
| P50 Response Time | < 500ms | Locust |
| P95 Response Time | < 2s | Locust |
| Cache Hit Rate | > 70% | Redis INFO |
| MongoDB Query Time | < 200ms | mongo_analyzer.py |
| Requests/sec | > 100 | Locust |

## Common Issues & Solutions

### Slow Queries
1. Run `mongo_analyzer.py` to check index usage
2. Add recommended indexes
3. Verify with explain plans

### High Memory Usage
1. Run `profiler.py` with memory profiling
2. Check for large dataset loading
3. Consider pagination or streaming

### Low Throughput
1. Increase Gunicorn workers
2. Increase MongoDB connection pool
3. Enable HTTP compression

## Next Steps

See [performance_analysis_plan.md](../../.gemini/antigravity/brain/ca13255c-0e6e-42f4-a3da-3fc045d6eaf8/performance_analysis_plan.md) for comprehensive analysis strategy.
