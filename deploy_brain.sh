#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL="$SCRIPT_DIR/.agentcortex/bin/deploy.sh"

# If canonical deploy exists locally, use it (normal path)
if [[ -f "$CANONICAL" ]]; then
  exec bash "$CANONICAL" "$@"
fi

# --- Bootstrap: canonical deploy not found (fresh clone with gitignored AgentCortex) ---
echo "AgentCortex framework not found locally — bootstrapping from remote..."

ACX_SOURCE="${ACX_SOURCE:-}"
ACX_CACHE="$SCRIPT_DIR/.agentcortex-src"
MANIFEST="$SCRIPT_DIR/.agentcortex-manifest"

# Try to read source_repo from manifest
if [[ -z "$ACX_SOURCE" && -f "$MANIFEST" ]]; then
    ACX_SOURCE="$(grep '^source_repo:' "$MANIFEST" | awk '{print $2}')" || true
fi

if [[ -z "$ACX_SOURCE" ]]; then
    echo "" >&2
    echo "Cannot bootstrap: no ACX_SOURCE configured and no source_repo in manifest." >&2
    echo "" >&2
    echo "Fix: set ACX_SOURCE to the AgentCortex git URL, e.g.:" >&2
    echo "  ACX_SOURCE=https://github.com/KbWen/AgentCortex.git ./deploy_brain.sh" >&2
    echo "" >&2
    exit 1
fi

if ! command -v git >/dev/null 2>&1; then
    echo "git is required for bootstrap fetch." >&2
    exit 1
fi

if [[ -d "$ACX_CACHE/.git" ]]; then
    echo "Updating cached AgentCortex source..."
    git -C "$ACX_CACHE" pull --quiet
else
    echo "Cloning AgentCortex from $ACX_SOURCE..."
    git clone --quiet "$ACX_SOURCE" "$ACX_CACHE"
fi

CACHED_CANONICAL="$ACX_CACHE/.agentcortex/bin/deploy.sh"
if [[ ! -f "$CACHED_CANONICAL" ]]; then
    echo "Cached source does not contain .agentcortex/bin/deploy.sh — aborting." >&2
    exit 1
fi

exec bash "$CACHED_CANONICAL" "$@"
