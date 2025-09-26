import json






# backend/app/parsers/log_parser.py
import re
from collections import Counter

_TS_PATS = [
    r'(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d{3})?)',  # 2025-01-05 14:30:15 or 14:30:15,842
    r'(?P<ts>\d{2}:\d{2}:\d{2})',                                     # 14:30:15
]
_LEVELS = ['ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG', 'TRACE']


def _parse_line(line: str):
    # 1) JSON line? Try to parse common keys
    s = line.strip()
    if s.startswith("{") and s.endswith("}"):
        try:
            obj = json.loads(s)
            # common timestamp keys
            ts = obj.get("ts") or obj.get("time") or obj.get("@timestamp") or obj.get("timestamp")
            # common level keys
            level = (obj.get("level") or obj.get("severity") or obj.get("lvl") or "INFO").upper()
            if level == "WARNING": level = "WARN"
            # common message keys
            msg = obj.get("message") or obj.get("msg") or obj.get("log") or s
            return ts, level, str(msg).strip()
        except Exception:
            pass  # fall back to regex path

    # 2) Fallback: regex timestamp + level in plain text
    ts = None
    for pat in _TS_PATS:
        m = re.search(pat, line)
        if m:
            ts = m.group('ts'); break
    level = 'INFO'
    for L in _LEVELS:
        if re.search(r'\b' + L + r'\b', line):
            level = 'WARN' if L == 'WARNING' else L
            break
    msg = line
    if ts:
        msg = msg.replace(ts, '')
    msg = re.sub(r'\b(?:ERROR|WARN|WARNING|INFO|DEBUG|TRACE)\b', '', msg, flags=re.I)
    msg = msg.strip(' -:\t')
    return ts, level, msg


def parse_log_files(paths):
    """Parse .log/.txt files → events, evidence, simple summary hint."""
    events, evidence_lines, all_text = [], [], []
    counts = Counter()

    for p in paths:
        try:
            with open(p, 'r', errors='ignore') as f:
                for line in f:
                    line = line.rstrip('\n')
                    if not line.strip():
                        continue
                    ts, level, msg = _parse_line(line)
                    events.append({
                        'time': ts,
                        'level': level,
                        'message': msg,
                        'source': p.split('/')[-1]
                    })
                    all_text.append(line)
                    if level in ('ERROR', 'WARN'):
                        evidence_lines.append(f"{p.split('/')[-1]}: {msg}")
                        counts[level] += 1
        except FileNotFoundError:
            continue

    low = " ".join(all_text).lower()
    hint = None
    if 'pool' in low and 'timeout' in low:
        hint = "Database pool exhaustion/timeout observed; multiple services impacted."
    elif 'exception' in low:
        hint = "Exceptions detected; see top error lines."

    # de-dupe evidence
    seen, dedup = set(), []
    for line in evidence_lines:
        if line not in seen:
            seen.add(line)
            dedup.append(line)

    return {
        'events': events,
        'top_lines': dedup,
        'counts': dict(counts),
        'summary_hint': hint,
        'all_text': all_text,
    }