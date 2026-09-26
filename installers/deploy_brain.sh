#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# When deployed to installers/, the project root is one level up.
# When invoked directly from the source repo, this also resolves correctly.
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CANONICAL="$PROJECT_ROOT/.agentcortex/bin/deploy.sh"

ACX_SOURCE="${ACX_SOURCE:-}"
ACX_CACHE="$PROJECT_ROOT/.agentcortex-src"
MANIFEST="$PROJECT_ROOT/.agentcortex-manifest"

# Peek at --source <url> (not consumed — deploy.sh parses it too). Without this,
# a `deploy_brain.ps1 -Source <url>` override would be invisible to the cache
# origin-verification below. Explicit ACX_SOURCE env still wins.
if [[ -z "$ACX_SOURCE" ]]; then
    _prev=""
    for _arg in "$@"; do
        if [[ "$_prev" == "--source" ]]; then
            ACX_SOURCE="$_arg"
            break
        fi
        case "$_arg" in
            --source=*)
                ACX_SOURCE="${_arg#--source=}"
                break
                ;;
        esac
        _prev="$_arg"
    done
fi

# Try to read source_repo from manifest
if [[ -z "$ACX_SOURCE" && -f "$MANIFEST" ]]; then
    # tr -d: a manifest checked out CRLF (Windows autocrlf) must not leave a CR in the URL.
    ACX_SOURCE="$(sed -n 's/^source_repo:[[:space:]]*//p' "$MANIFEST" | head -n 1 | tr -d '\r')" || true
fi

# NVM-style dispatch:
#   No manifest + canonical present  → first-time run from the cloned source repo → use canonical
#   Manifest present (already installed) → always fetch fresh source for update
#   No canonical, no manifest          → fresh bootstrap (only installers/ available)
if [[ ! -f "$MANIFEST" && -f "$CANONICAL" ]]; then
    exec bash "$CANONICAL" "$@"
fi

echo "Agentic OS bootstrap — fetching source and deploying..."

if [[ -z "$ACX_SOURCE" ]]; then
    echo "" >&2
    echo "Cannot bootstrap: no ACX_SOURCE configured and no source_repo in manifest." >&2
    echo "" >&2
    echo "Fix: set ACX_SOURCE to the Agentic OS git URL, e.g.:" >&2
    echo "  ACX_SOURCE=https://github.com/KbWen/agentic-os.git ./deploy_brain.sh" >&2
    echo "  Or clone the Agentic OS repo locally and run installers/deploy_brain.sh directly." >&2
    echo "" >&2
    exit 1
fi

if ! command -v git >/dev/null 2>&1; then
    echo "git is required for bootstrap fetch. Install Git from https://git-scm.com/downloads" >&2
    exit 1
fi

# core.longpaths: upstream paths reach ~100 chars, so a clone under a deep Windows
# project root exceeds MAX_PATH without it. Git ignores the setting elsewhere.
acx_git() {
    git -c core.longpaths=true "$@"
}

# Trailing slash / .git suffix differences are not real mismatches.
normalize_git_url() {
    local url="${1%/}"
    printf '%s' "${url%.git}"
}

# rm -rf can fail partway (e.g. Windows "Device or resource busy"), leaving a
# half-deleted dir — possibly without .git, so later git commands would silently
# fall through to the PARENT repo. Never proceed past a failed removal.
remove_cache_or_die() {
    rm -rf "$ACX_CACHE" 2>/dev/null || true
    if [[ -e "$ACX_CACHE" ]]; then
        echo "" >&2
        echo "Failed to fully remove cache at $ACX_CACHE (file in use?)." >&2
        echo "Remove it manually, then re-run this script. Aborting to avoid" >&2
        echo "running git against a half-deleted directory." >&2
        exit 1
    fi
}

if [[ -d "$ACX_CACHE/.git" ]]; then
    # A cache cloned from a different repo (e.g. pre-migration source) must
    # never be pulled or deployed from — verify origin matches the resolved source.
    CACHE_ORIGIN="$(git -C "$ACX_CACHE" remote get-url origin 2>/dev/null || true)"
    if [[ "$(normalize_git_url "$CACHE_ORIGIN")" != "$(normalize_git_url "$ACX_SOURCE")" ]]; then
        echo "Cached source origin does not match the configured source:" >&2
        echo "  cache origin: ${CACHE_ORIGIN:-<none>}" >&2
        echo "  configured:   $ACX_SOURCE" >&2
        echo "Re-cloning from the configured source..." >&2
        remove_cache_or_die
        acx_git clone --depth 1 "$ACX_SOURCE" "$ACX_CACHE"
    else
        echo "Updating cached Agentic OS source..."
        if ! acx_git -C "$ACX_CACHE" pull 2>&1; then
            echo "" >&2
            echo "Failed to update cached source. Removing stale cache and re-cloning..." >&2
            remove_cache_or_die
            acx_git clone --depth 1 "$ACX_SOURCE" "$ACX_CACHE"
        fi
    fi
else
    echo "Cloning Agentic OS from $ACX_SOURCE..."
    # Clean up any partial clone left by a prior interrupted attempt
    [[ -d "$ACX_CACHE" ]] && remove_cache_or_die
    acx_git clone --depth 1 "$ACX_SOURCE" "$ACX_CACHE"
fi

# A failed checkout (e.g. a path over MAX_PATH) leaves an empty index; `git pull`
# then reports "Already up to date" and the partial tree would be deployed with
# exit 0. Deploy only from a cache whose index is populated and clean.
cache_is_intact() {
    # acx_git here too: without core.longpaths a long path reads as "modified".
    acx_git -C "$ACX_CACHE" ls-files --error-unmatch .agentcortex/bin/deploy.sh >/dev/null 2>&1 || return 1
    local _st
    # A failing `git status` prints nothing; that must not read as "clean".
    _st="$(acx_git -C "$ACX_CACHE" status --porcelain --untracked-files=no 2>/dev/null)" || return 1
    [[ -z "$_st" ]]
}
if ! cache_is_intact; then
    echo "Cached Agentic OS source failed its integrity check (partial checkout, modified files, or unreadable). Re-cloning..." >&2
    remove_cache_or_die
    acx_git clone --depth 1 "$ACX_SOURCE" "$ACX_CACHE"
    if ! cache_is_intact; then
        # A checkout that fails (e.g. Filename too long) already stopped at the clone
        # above; what reaches here is a source without deploy.sh, a cache git refuses to
        # read, or a fresh clone git already reports as modified (e.g. a case collision).
        echo "Cached source still fails its integrity check after a fresh clone - aborting. git says:" >&2
        acx_git -C "$ACX_CACHE" ls-files --error-unmatch .agentcortex/bin/deploy.sh >/dev/null || true
        acx_git -C "$ACX_CACHE" status --porcelain --untracked-files=no >&2 || true
        echo "If .agentcortex/bin/deploy.sh is not known to git, check source_repo in .agentcortex-manifest." >&2
        exit 1
    fi
fi

CACHED_CANONICAL="$ACX_CACHE/.agentcortex/bin/deploy.sh"
if [[ ! -f "$CACHED_CANONICAL" ]]; then
    echo "Cached source does not contain .agentcortex/bin/deploy.sh — aborting." >&2
    echo "Try: rm -rf .agentcortex-src && re-run this script to force a fresh clone." >&2
    exit 1
fi

exec bash "$CACHED_CANONICAL" "$@"
