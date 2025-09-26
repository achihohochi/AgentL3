# Incident: Disk full (ENOSPC) affecting proxy/logs
## Symptoms
- "No space left on device" in proxy temp or logs; rotation failures
## Likely Root Cause
- Insufficient disk quota; runaway temp files
## Signals to Match
- "No space left on device", "ENOSPC", "proxy_temp"
## Remediation
- Cleanup temp; increase volume; quotas/retention policies
## Prevention
- Alerts on disk/inode usage; auto-clean policies
