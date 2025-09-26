# Incident: Postgres statement timeouts & connection pressure
## Symptoms
- "ERROR: canceling statement due to statement timeout"
- "remaining connection slots are reserved..."
- High p99 latency from app to Postgres
## Likely Root Cause
- Long-running queries with lock contention
- Pool exhaustion from leaked/stuck transactions
## Signals to Match
- "statement timeout", "remaining connection slots", "SQLTimeoutException", "p99 latency"
## Remediation
- Per-query timeouts; index/optimize slow queries; ensure connections closed in finally blocks
## Prevention
- Monitor pool in_use/waiters; lock metrics; circuit breaker on DB calls
