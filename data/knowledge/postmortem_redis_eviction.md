# Incident: Redis eviction & thundering herd
## Symptoms
- "OOM command not allowed"; eviction spikes; herd after TTL expiry
## Likely Root Cause
- Small maxmemory; hot keys expiring simultaneously
## Signals to Match
- "OOM command not allowed", "eviction spike", "thundering herd", "miss_rate"
## Remediation
- Increase maxmemory carefully; request coalescing; stagger TTLs; add jitter
## Prevention
- Dashboards on evictions/miss rate; hot key alerts
