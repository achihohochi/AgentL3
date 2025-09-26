# Incident: TLS handshake failures / certificate expiry
## Symptoms
- Handshake failure; "certificate expired"; third-party SNI failures
## Likely Root Cause
- Expired certificate or protocol mismatch
## Signals to Match
- "handshake failure", "certificate expired", "TLS1.2 fallback failed"
## Remediation
- Renew certs; verify chain; enforce minimum TLS; coordinate with partner endpoints
## Prevention
- Cert expiry alerts; pre-rotation runbooks; synthetic TLS probes
