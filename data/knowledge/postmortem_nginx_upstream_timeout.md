# Incident: Nginx upstream timeouts during checkout burst
## Symptoms
- Nginx logs: "upstream timed out", "upstream prematurely closed connection"
- 5xx spikes on POST /checkout, GET /orders/*
## Likely Root Cause
- Upstream service latency (DB pool exhaustion or slow queries)
- Sometimes disk exhaustion in proxy temp
## Signals to Match
- "upstream timed out", "prematurely closed connection", "Connection timed out", "5xx"
## Remediation
- Temporarily increase proxy read timeout; reduce DB timeouts; fix pool leaks; coalesce requests
## Prevention
- SLOs on p95/p99 latency; alert on DB pool in_use/waiters
