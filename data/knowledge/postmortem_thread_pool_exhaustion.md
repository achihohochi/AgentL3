# Incident: Application thread pool exhaustion
## Symptoms
- Work queue saturated; active threads at max; p99 latency spikes
## Likely Root Cause
- Under-provisioned pool; blocking operations on main executor
## Signals to Match
- "work queue length", "threads_active", "RejectedExecutionException", "p99=30s"
## Remediation
- Increase pool cautiously; move blocking I/O off main; backpressure & timeouts
## Prevention
- Dashboards on queue length/active threads; circuit breakers; bulkheads
