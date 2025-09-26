# Incident: Kubernetes OOMKilled & CrashLoopBackOff
## Symptoms
- Pod OOMKilled; BackOff restarting; readiness probe 503
## Likely Root Cause
- Memory leak or insufficient limits for service
## Signals to Match
- "OOMKilled", "BackOff", "Readiness probe failed", "503"
## Remediation
- Increase memory limits; fix leak; add heap profiling
## Prevention
- Alerts on RSS; HPA on memory; GC pause monitoring
