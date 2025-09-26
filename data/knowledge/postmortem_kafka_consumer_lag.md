# Incident: Kafka consumer lag & backpressure
## Symptoms
- Large consumer lag (minutes behind), rebalances, processing timeouts
## Likely Root Cause
- Under-provisioned consumers or slow handler; burst traffic
## Signals to Match
- "lag=", "rebalance in progress", "processing timeout"
## Remediation
- Scale consumers; tune max.poll.interval.ms; optimize handler; DLQ slow paths
## Prevention
- SLOs on lag; autoscale by lag; alert on time-behind
