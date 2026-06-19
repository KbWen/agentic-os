#!/usr/bin/env sh
# demo/run.sh — watch a machine gate block a real corner-cut, on your machine.
#
# This runs Agentic OS's actual credential scanner
# (.agentcortex/tools/scan_credentials.py) against a file an agent is "about to
# commit". The leaked key is generated at runtime, so this script never stores a
# real-looking secret of its own. Nothing is staged or committed; a temp dir is
# used and cleaned up.
#
# Reproduce anytime:  bash demo/run.sh

set -eu

script_dir=$(cd "$(dirname "$0")" && pwd)
repo_root=$(dirname "$script_dir")
scanner="$repo_root/.agentcortex/tools/scan_credentials.py"

py=python
command -v python >/dev/null 2>&1 || py=python3
command -v "$py" >/dev/null 2>&1 || { echo "This demo needs Python 3.9+ (the scanner is Python)." >&2; exit 2; }
[ -f "$scanner" ] || { echo "Scanner not found at $scanner" >&2; exit 2; }

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# An agent, mid-task, writes a config file and slips in a live AWS key.
# Built at runtime so this repo's own scanner never flags the demo itself.
key="AKIA""IOSFODNN7EXAMPLE"
printf 'DB_HOST=prod.internal\naws_access_key_id = %s\n' "$key" > "$work/config.env"

printf '\n  An AI agent wrote this file and reported: "Done — config added."\n'
printf '  ----------------------------------------------------------------\n'
sed "s/$key/AKIA****************/; s/^/    /" "$work/config.env"
printf '  ----------------------------------------------------------------\n'
printf '\n  Without a gate, that commit lands and the key is in git history forever.\n'
printf '  Agentic OS runs this before the commit is allowed:\n\n'
printf '    $ scan_credentials.py config.env\n\n'

if (cd "$work" && "$py" "$scanner" config.env); then
  printf '\n  [!] Demo problem: the scanner did not flag the key. Please open an issue.\n' >&2
  exit 1
fi

printf '\n  Commit BLOCKED. The agent said "done"; the machine said no — and it\n'
printf '  redacted the value instead of echoing your secret back at you.\n\n'
printf '  This is one machine-enforced check of several (CI runs your real tests;\n'
printf '  validators check the work trail). Reproduce anytime: bash demo/run.sh\n\n'
