#!/bin/bash
# Quick Performance Test Script
# Run with: bash tests/performance/quick_test.sh

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       WS-AVAILABILITY QUICK PERFORMANCE TEST                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
HOST="http://localhost:9001"
RESULTS_FILE="tests/performance/quick_results.txt"

# Check if service is running
echo "Checking if service is running..."
if ! curl -s "$HOST/version" > /dev/null; then
    echo "❌ Service not running at $HOST"
    echo "Start with: RUNMODE=test gunicorn --workers 2 --bind 0.0.0.0:9001 start:app"
    exit 1
fi

echo "✅ Service is running"
echo ""

# Create results file
echo "Performance Test Results - $(date)" > $RESULTS_FILE
echo "======================================" >> $RESULTS_FILE
echo "" >> $RESULTS_FILE

# Test 1: Small query
echo "Test 1: Small Query (1 week, single station)"
echo "Test 1: Small Query" >> $RESULTS_FILE
URL="$HOST/query?net=NL&sta=HGN&start=2023-01-01&end=2023-01-07"
curl -w "\n  Time: %{time_total}s\n  Size: %{size_download} bytes\n  Status: %{http_code}\n" \
     -o /dev/null -s "$URL" | tee -a $RESULTS_FILE
echo "" | tee -a $RESULTS_FILE

# Test 2: Medium query
echo "Test 2: Medium Query (1 month, network)"
echo "Test 2: Medium Query" >> $RESULTS_FILE
URL="$HOST/query?net=NL&start=2023-01-01&end=2023-02-01"
curl -w "\n  Time: %{time_total}s\n  Size: %{size_download} bytes\n  Status: %{http_code}\n" \
     -o /dev/null -s "$URL" | tee -a $RESULTS_FILE
echo "" | tee -a $RESULTS_FILE

# Test 3: Extent query
echo "Test 3: Extent Query"
echo "Test 3: Extent Query" >> $RESULTS_FILE
URL="$HOST/extent?net=NA&start=2023-02-01"
curl -w "\n  Time: %{time_total}s\n  Size: %{size_download} bytes\n  Status: %{http_code}\n" \
     -o /dev/null -s "$URL" | tee -a $RESULTS_FILE
echo "" | tee -a $RESULTS_FILE

# Test 4: JSON format
echo "Test 4: JSON Format"
echo "Test 4: JSON Format" >> $RESULTS_FILE
URL="$HOST/query?net=NL&start=2023-01-01&format=json"
curl -w "\n  Time: %{time_total}s\n  Size: %{size_download} bytes\n  Status: %{http_code}\n" \
     -o /dev/null -s "$URL" | tee -a $RESULTS_FILE
echo "" | tee -a $RESULTS_FILE

# Test 5: Cache effectiveness (run same query twice)
echo "Test 5: Cache Effectiveness"
echo "Test 5: Cache Effectiveness" >> $RESULTS_FILE
URL="$HOST/query?net=NL&sta=HGN&start=2023-01-01"

echo "  First request (cache miss):" | tee -a $RESULTS_FILE
curl -w "    Time: %{time_total}s\n" -o /dev/null -s "$URL" | tee -a $RESULTS_FILE

echo "  Second request (cache hit):" | tee -a $RESULTS_FILE
curl -w "    Time: %{time_total}s\n" -o /dev/null -s "$URL" | tee -a $RESULTS_FILE
echo "" | tee -a $RESULTS_FILE

# Test 6: Concurrent requests
echo "Test 6: Concurrent Requests (10 parallel)"
echo "Test 6: Concurrent Requests" >> $RESULTS_FILE
START_TIME=$(date +%s.%N)
for i in {1..10}; do
    curl -s "$HOST/query?net=NL&start=2023-01-01" > /dev/null &
done
wait
END_TIME=$(date +%s.%N)
ELAPSED=$(echo "$END_TIME - $START_TIME" | bc)
echo "  Total time for 10 concurrent requests: ${ELAPSED}s" | tee -a $RESULTS_FILE
echo "" | tee -a $RESULTS_FILE

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  TESTING COMPLETE                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Results saved to: $RESULTS_FILE"
