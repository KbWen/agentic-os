#!/usr/bin/env bash
# No-python credential pre-screen FLOOR (ADR-008).
#
# A deliberately NARROW, FP-free SUBSET of scan_credentials.py for hosts WITHOUT
# Python. It scans the STAGED content of each staged file for unambiguous credential
# prefixes and prints REDACTED `path:line: name` (NEVER the value); exit 1 on any
# hit, 0 clean, 3 on git failure (fail-closed — never a silent "clean").
#
# Scope (honest): narrow > recall. A blocking hook that false-positives gets
# `--no-verify`'d into uselessness, so this catches only the three prefixes that
# cannot plausibly collide with benign text. Full detection = scan_credentials.py
# (when Python is present) or CI TruffleHog (post-commit). Patterns are POSIX ERE
# only (no `\b` / PCRE) so the floor runs on macOS/BSD/busybox grep.
set -u

# name|ERE  (one per line; first '|' splits)
PATTERNS='aws-access-key-id|AKIA[0-9A-Z]{16}
pem-private-key|-----BEGIN[ A-Z]*PRIVATE KEY-----
github-token|ghp_[0-9A-Za-z]{36}'

ALLOW='pragma: allowlist secret'

# Optional --staged alias (staged scan is the default); ignore other args.
[ "${1:-}" = "--staged" ] && shift || true

# Staged file list (newline-delimited; bash 3.2-safe). Fail-CLOSED on git error.
files="$(git diff --cached --name-only 2>/dev/null)" || exit 3
[ -n "$files" ] || exit 0

hit=0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  content="$(git show ":$f" 2>/dev/null)" || continue   # skip staged deletions
  while IFS='|' read -r name re; do
    [ -n "$re" ] || continue
    while IFS= read -r match; do
      lno="${match%%:*}"
      printf '%s:%s: %s\n' "$f" "$lno" "$name" >&2
      hit=1
    done < <(printf '%s\n' "$content" | grep -nE -- "$re" | grep -vF -- "$ALLOW")
  done <<PATTERN_EOF
$PATTERNS
PATTERN_EOF
done <<FILE_EOF
$files
FILE_EOF

if [ "$hit" -ne 0 ]; then
  printf 'ACX credential floor: high-confidence secret shape in staged content (redacted above). Rotate/remove it, then re-commit. (narrow no-python floor; a full scan needs the python scanner or CI secret scanning)\n' >&2
fi
exit "$hit"
