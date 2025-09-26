# Incident: 429 Too Many Requests during burst
## Symptoms
- Gateway returns HTTP 429; clients see retry-after
## Likely Root Cause
- Rate limits too strict for burst profile
## Signals to Match
- "HTTP 429 Too Many Requests", "rate_limiter burst exceeded", "retry-after"
## Remediation
- Increase burst capacity; prioritize critical paths; client backoff
## Prevention
- Load tests for burst headroom; alert on 429 rate
