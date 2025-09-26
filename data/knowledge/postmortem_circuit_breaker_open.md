# Incident: Circuit breaker opened due to downstream slowness
## Symptoms
- "CircuitBreaker OPEN" for datasource
- App errors: timeouts, fallback engaged
## Likely Root Cause
- Sustained downstream latency (DB or DNS)
## Signals to Match
- "CircuitBreaker OPEN", "sql timeout", "acquire>30s", "p99 latency"
## Remediation
- Reduce timeouts/acquire pressure; raise pool cautiously; add backoff/bulkheads
## Prevention
- Alert on breaker open rate; jittered retries; load-shedding
