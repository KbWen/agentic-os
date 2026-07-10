#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# Whitelist CP_FLAG to prevent command injection via environment variable.
_raw_cp_flag="${CP_FLAG:-}"
case "$_raw_cp_flag" in
    -i|-v|-p|-n|-f|-a|"") CP_FLAG="$_raw_cp_flag" ;;
    *) echo "ERROR: Invalid CP_FLAG='$_raw_cp_flag'. Allowed: -i -v -p -n -f -a (or empty)." >&2; exit 1 ;;
esac
ACX_SOURCE="${ACX_SOURCE:-}"
TARGET=""
DRY_RUN=false

# --- Argument parsing ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --source) ACX_SOURCE="$2"; shift 2 ;;
        --source=*) ACX_SOURCE="${1#--source=}"; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        *) TARGET="$1"; shift ;;
    esac
done
TARGET="${TARGET:-.}"
TARGET="${TARGET%/}"

MANIFEST_FILE="$TARGET/.agentcortex-manifest"
ACX_VERSION="1.8.10"

# --- Self-deploy guard ---
TARGET_ABS="$(cd "$TARGET" 2>/dev/null && pwd || echo "$TARGET")"
REPO_ABS="$(cd "$REPO_ROOT" 2>/dev/null && pwd)"
if [ "$TARGET_ABS" = "$REPO_ABS" ]; then
    echo "" >&2
    echo "ERROR: Target is the Agentic OS source repo itself." >&2
    echo "Deploy INTO your project, not into the framework source." >&2
    echo "Usage: $0 /path/to/your-project" >&2
    exit 1
fi

# --- Counters ---
COUNT_UPDATED=0
COUNT_SKIPPED=0
COUNT_NEW=0
COUNT_REMOVED=0
COUNT_CORE_OVERWRITTEN=0

# --- SHA256 utility (cross-platform) ---
compute_sha256() {
    local file="$1"
    # NOTE: GNU sha256sum / BSD shasum escape filenames containing a backslash
    # or newline by prefixing the output line with a literal '\' (and escaping
    # the name). On Windows/Git Bash a backslash TARGET path (e.g. C:\proj)
    # therefore yields "\<hash>", which silently breaks every dst-hash
    # comparison (a clean repo path hashes without the prefix). Strip a leading
    # backslash so the hash is comparable regardless of path style.
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$file" | cut -d' ' -f1 | sed 's/^\\//'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$file" | cut -d' ' -f1 | sed 's/^\\//'
    elif command -v openssl >/dev/null 2>&1; then
        openssl dgst -sha256 "$file" | awk '{print $NF}'
    else
        echo "ERROR: No SHA-256 tool found (need sha256sum, shasum, or openssl)." >&2
        exit 1
    fi
}

# --- EOL-normalized SHA256 (CR-stripped) ---
# Strips bare CR (\r) before hashing so that a CRLF working-tree checkout of an
# otherwise-unmodified text file produces the same hash as the LF source. This
# closes the CRLF hash-mismatch bug: downstream repos using git autocrlf=true (or
# .gitattributes `*.md text` without eol=lf) check out .md/.yaml files with CRLF,
# making every unmodified scaffold file appear "locally modified" and spuriously
# sidecar'd to .acx-incoming on every re-deploy.
#
# All files deployed by Agentic OS are text (no binaries in the deploy set), so
# normalizing unconditionally is safe. For genuinely binary files, compute_sha256
# (raw) must be used explicitly.
compute_sha256_normalized() {
    local file="$1"
    if command -v sha256sum >/dev/null 2>&1; then
        tr -d '\r' < "$file" | sha256sum | cut -d' ' -f1
    elif command -v shasum >/dev/null 2>&1; then
        tr -d '\r' < "$file" | shasum -a 256 | cut -d' ' -f1
    elif command -v openssl >/dev/null 2>&1; then
        tr -d '\r' < "$file" | openssl dgst -sha256 | awk '{print $NF}'
    else
        echo "ERROR: No SHA-256 tool found (need sha256sum, shasum, or openssl)." >&2
        exit 1
    fi
}

# --- Source commit (best-effort) ---
get_source_commit() {
    if command -v git >/dev/null 2>&1 && [ -e "$REPO_ROOT/.git" ]; then
        git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown"
    else
        echo "unknown"
    fi
}

# --- Tier classification ---
# Returns: core, scaffold, or wrapper
get_tier() {
    local rel_path="$1"
    case "$rel_path" in
        # wrapper — user may customize these delegation scripts
        installers/deploy_brain.sh|installers/deploy_brain.ps1|installers/deploy_brain.cmd) echo "wrapper" ;;

        # scaffold — created once, user expected to modify (or merge framework + project content)
        AGENTS.md|CLAUDE.md|GEMINI.md) echo "scaffold" ;;
        .gitattributes) echo "scaffold" ;;
        .agentcortex/context/current_state.md) echo "scaffold" ;;
        .agentcortex/adr/*) echo "scaffold" ;;
        .agentcortex/templates/*) echo "scaffold" ;;
        .claude/settings.json) echo "scaffold" ;;
        .github/ISSUE_TEMPLATE/*) echo "scaffold" ;;
        .github/PULL_REQUEST_TEMPLATE.md) echo "scaffold" ;;
        .github/copilot-instructions.md) echo "scaffold" ;;

        # scaffold — user may customize advisory hook samples before activating
        .githooks/*) echo "scaffold" ;;

        # scaffold — skill bodies/metadata (ADR-005): skills are advisory
        # instruction extensions (they CANNOT bypass gates), so a user-edited
        # skill is preserved via .acx-incoming instead of being silently
        # overwritten (closes R1). Unmodified skills still force-update (scaffold
        # updates when the manifest hash matches). The reserved custom-* namespace
        # is never shipped by the framework, so it only ever hits the SKIP branch.
        # NOTE: framework-authoritative paths (.agent/rules/*, .agent/workflows/*,
        # .agent/config.yaml, validate.*, deploy.*, platform entries, tools/**,
        # metadata/**) deliberately fall through to core below — they MUST keep
        # force-updating so governance/security fixes always land (no drift).
        .agent/skills/*|.agents/skills/*) echo "scaffold" ;;

        # core — everything else is framework, always overwrite
        *) echo "core" ;;
    esac
}

# --- Inline tier lookup (no subshell) ---
# _get_tier_inline <rel_path> sets _TIER without spawning a subshell.
# Used by _deploy_file_now (hot path) and process_queue to avoid ~187 subshells
# per deploy. get_tier() above uses echo for compatibility with $(get_tier ...).
_TIER=""
_get_tier_inline() {
    local _rel="$1"
    case "$_rel" in
        installers/deploy_brain.sh|installers/deploy_brain.ps1|installers/deploy_brain.cmd) _TIER="wrapper" ;;
        AGENTS.md|CLAUDE.md|GEMINI.md) _TIER="scaffold" ;;
        .gitattributes) _TIER="scaffold" ;;
        .agentcortex/context/current_state.md) _TIER="scaffold" ;;
        .agentcortex/adr/*) _TIER="scaffold" ;;
        .agentcortex/templates/*) _TIER="scaffold" ;;
        .claude/settings.json) _TIER="scaffold" ;;
        .github/ISSUE_TEMPLATE/*) _TIER="scaffold" ;;
        .github/PULL_REQUEST_TEMPLATE.md) _TIER="scaffold" ;;
        .github/copilot-instructions.md) _TIER="scaffold" ;;
        .githooks/*) _TIER="scaffold" ;;
        .agent/skills/*|.agents/skills/*) _TIER="scaffold" ;;
        *) _TIER="core" ;;
    esac
}

# --- Read hash from existing manifest ---
# Returns the sha256 hash for a given path, or empty string if not found
manifest_lookup_hash() {
    local rel_path="$1"
    if [ -f "$MANIFEST_FILE" ]; then
        awk -v path="$rel_path" '$2 == path { sub(/^sha256:/, "", $3); print $3; exit }' "$MANIFEST_FILE"
    fi
}

# --- Track deployed files (append to temp file) ---
DEPLOYED_FILES_TMP=""
record_deployed() {
    local tier="$1" rel_path="$2" hash="$3"
    echo "$tier $rel_path sha256:$hash" >> "$DEPLOYED_FILES_TMP"
}

# --- Deploy-queue temp file (batch path) ---
# When batch hashing is active (Bash 4+ with declare -A), deploy_file appends
# records here instead of hashing per-file.  process_queue flushes it.
_DEPLOY_QUEUE_TMP=""

# --- Clean old .acx-incoming sidecars ---
clean_acx_incoming() {
    local count=0
    while IFS= read -r -d '' f; do
        rm -f "$f"
        count=$((count + 1))
    done < <(find "$TARGET" -name '*.acx-incoming' -print0 2>/dev/null || true)
    if [ "$count" -gt 0 ]; then
        echo "  Cleaned $count old .acx-incoming sidecar(s)"
    fi
}

# --- Smart deploy a single file (internal — called with pre-computed hashes) ---
# _deploy_file_now <src> <rel> <chmod> <src_hash> <dst_hash_or_empty> <old_manifest_hash_or_empty>
#
# All hash arguments are EOL-normalized (LF-stripped) SHA-256 hex digests.
# dst_hash_or_empty: normalized hash of existing $TARGET/$rel, or "" if file absent.
# old_manifest_hash_or_empty: manifest hash for $rel from the OLD manifest, or "" if not found.
#
# This function populates DEPLOYED_FILES_TMP (consumed by the removed-files
# detector ~line 942 and the manifest write ~1040) exactly as the old deploy_file did.
_deploy_file_now() {
    local src="$1"
    local rel="$2"
    local do_chmod="${3:-}"
    local src_hash="$4"
    local dst_hash="$5"        # "" when dst absent
    local old_manifest_hash="$6"

    local dst="$TARGET/$rel"
    # Use inline tier lookup (no subshell) — sets global _TIER.
    _get_tier_inline "$rel"
    local tier="$_TIER"

    local is_update=false
    [ -f "$MANIFEST_FILE" ] && is_update=true

    if [ -n "$dst_hash" ] && $is_update; then
        # Update mode — file exists in target
        if [ "$tier" = "core" ]; then
            # Core: force-update (ADR-005 — governance/security fixes always land,
            # no drift). But if the downstream locally modified this core file,
            # back up their version to a .acx-local sidecar + warn before
            # overwriting, so edits are recoverable instead of silently lost
            # (#173). The force-update invariant is preserved — the new framework
            # version still lands; only the silent-data-loss footgun is closed.
            local locally_modified=false
            if [ -n "$old_manifest_hash" ]; then
                # EOL-normalized comparison: a CRLF-checked-out unmodified file
                # produces the same normalized hash as the LF manifest entry, so
                # it is correctly classified as unmodified (not spuriously flagged).
                [ "$dst_hash" != "$old_manifest_hash" ] && locally_modified=true
            else
                # Pre-manifest/legacy: no baseline to compare against; treat
                # content that differs from the framework version as user content.
                [ "$dst_hash" != "$src_hash" ] && locally_modified=true
            fi
            if $locally_modified && [ "$dst_hash" != "$src_hash" ]; then
                # A backup MUST always overwrite a stale .acx-local. Unlike
                # .acx-incoming (cleaned each run by clean_acx_incoming), the
                # .acx-local backup persists, so a pre-existing one + a user-set
                # CP_FLAG=-n/-i would make `cp` silently skip — losing the newest
                # local edits. Remove first so the backup always lands.
                rm -f "$dst.acx-local"
                cp ${CP_FLAG:+"$CP_FLAG"} "$dst" "$dst.acx-local"
                echo "  [OVERWRITE] $rel (core force-updated; your local edits backed up to $rel.acx-local)"
                COUNT_CORE_OVERWRITTEN=$((COUNT_CORE_OVERWRITTEN + 1))
            fi
            # Skip cp when src and dst already identical (raw bytes match) — pure no-op.
            if [ "$src_hash" != "$dst_hash" ]; then
                cp ${CP_FLAG:+"$CP_FLAG"} "$src" "$dst"
                [ -n "$do_chmod" ] && chmod +x "$dst"
            fi
            COUNT_UPDATED=$((COUNT_UPDATED + 1))
        else
            # Scaffold/wrapper: check if user modified
            if [ -z "$old_manifest_hash" ]; then
                # File exists in target but not in old manifest. The file
                # likely carries user content (legacy migration, pre-manifest
                # era, or content brought in out-of-band). Preserve it via
                # sidecar when content differs from the framework version —
                # never silently overwrite scaffold-tier user content.
                if [ "$src_hash" != "$dst_hash" ]; then
                    cp ${CP_FLAG:+"$CP_FLAG"} "$src" "$dst.acx-incoming"
                    echo "  [SKIP] $rel (pre-existing/migrated; new version at $rel.acx-incoming — merge manually or ask AI agent to merge)"
                    COUNT_SKIPPED=$((COUNT_SKIPPED + 1))
                    # Record the upstream baseline, never the preserved user hash.
                    # Otherwise the next deploy treats unchanged user bytes as
                    # framework-unmodified and overwrites them without a sidecar.
                    record_deployed "$tier" "$rel" "$src_hash"
                    return 0
                fi
                # Same content — no-op; record the matching hash for future runs.
                COUNT_UPDATED=$((COUNT_UPDATED + 1))
            else
                if [ "$dst_hash" = "$old_manifest_hash" ]; then
                    # User didn't modify — safe to update.
                    # Skip cp when src already matches dst (pure no-op copy).
                    if [ "$src_hash" != "$dst_hash" ]; then
                        cp ${CP_FLAG:+"$CP_FLAG"} "$src" "$dst"
                        [ -n "$do_chmod" ] && chmod +x "$dst"
                    fi
                    COUNT_UPDATED=$((COUNT_UPDATED + 1))
                else
                    # User modified — skip and write sidecar
                    if [ "$src_hash" != "$dst_hash" ]; then
                        cp ${CP_FLAG:+"$CP_FLAG"} "$src" "$dst.acx-incoming"
                        echo "  [SKIP] $rel (locally modified; new version at $rel.acx-incoming)"
                        COUNT_SKIPPED=$((COUNT_SKIPPED + 1))
                        # Keep the OLD manifest hash so next deploy still detects modification
                        record_deployed "$tier" "$rel" "$old_manifest_hash"
                        return 0
                    else
                        # User modified but result is same as new version — no action needed
                        COUNT_UPDATED=$((COUNT_UPDATED + 1))
                    fi
                fi
            fi
        fi
    elif [ -n "$dst_hash" ] && ! $is_update; then
        # Fresh install but file already exists (pre-manifest era, or first deploy into existing project).
        # For scaffold/wrapper tiers, preserve the user's file and write a sidecar so nothing is clobbered.
        if [ "$tier" != "core" ]; then
            if [ "$src_hash" != "$dst_hash" ]; then
                cp ${CP_FLAG:+"$CP_FLAG"} "$src" "$dst.acx-incoming"
                echo "  [SKIP] $rel (pre-existing; new version at $rel.acx-incoming — merge manually or ask AI agent to merge)"
                COUNT_SKIPPED=$((COUNT_SKIPPED + 1))
                # Record the upstream baseline, never the preserved user hash.
                # Otherwise the next deploy treats unchanged user bytes as
                # framework-unmodified and overwrites them without a sidecar.
                record_deployed "$tier" "$rel" "$src_hash"
                return 0
            fi
            # Same content — safe to let it be (no cp needed since identical)
        else
            # Skip cp when src already matches dst (pure no-op).
            if [ "$src_hash" != "$dst_hash" ]; then
                cp ${CP_FLAG:+"$CP_FLAG"} "$src" "$dst"
                [ -n "$do_chmod" ] && chmod +x "$dst"
            fi
        fi
    else
        # File doesn't exist in target — always deploy
        cp ${CP_FLAG:+"$CP_FLAG"} "$src" "$dst"
        [ -n "$do_chmod" ] && chmod +x "$dst"
        if $is_update; then
            COUNT_NEW=$((COUNT_NEW + 1))
        fi
    fi

    record_deployed "$tier" "$rel" "$src_hash"
}

# --- Batch-hashing gate (Bash 4+ associative arrays required) ---
# Set to true only when declare -A succeeds. macOS ships Bash 3.2 which does not
# support associative arrays; on those hosts we fall back to the per-file path
# (cheap because macOS fork() is fast). Set ACX_FORCE_PERFILE=1 to always use
# the per-file path (escape hatch for debugging or unusual environments).
_ACX_BATCH_OK=false
if [ -z "${ACX_FORCE_PERFILE:-}" ]; then
    # shellcheck disable=SC2034  # _acx_assoc_test is intentionally unused
    # Requires assoc arrays (4.0) AND namerefs (4.3) — test both in a subshell.
    if (declare -A _acx_assoc_test && _acx_nref_fn() { local -n _r="$1"; }; _acx_nref_fn _acx_assoc_test) 2>/dev/null; then
        _ACX_BATCH_OK=true
    fi
fi

# --- Smart deploy a single file (public API) ---
# deploy_file <source_abs> <target_rel> [chmod]
#
# Batch path (Bash 4.3+, !ACX_FORCE_PERFILE): appends a queue record and returns.
#   All hashing is deferred to process_queue (one single-process pass per list,
#   order-paired hash output — see _batch_hash_normalized).
# Per-file fallback (Bash 3.2 or ACX_FORCE_PERFILE=1): computes hashes inline
#   and calls _deploy_file_now immediately — identical behavior, just slower on
#   high-spawn-cost hosts (MSYS/Windows ~28ms/spawn × ~2600 files = 43-72s).
deploy_file() {
    local src="$1"
    local rel="$2"
    local do_chmod="${3:-}"

    [ -f "$src" ] || return 0

    if $_ACX_BATCH_OK; then
        # Batch path: append tab-separated record to queue.
        # Fields: src <TAB> rel <TAB> do_chmod
        printf '%s\t%s\t%s\n' "$src" "$rel" "$do_chmod" >> "$_DEPLOY_QUEUE_TMP"
    else
        # Per-file fallback (Bash 3.2 / ACX_FORCE_PERFILE=1).
        # Use EOL-normalized hashing so CRLF checkouts do not appear modified.
        local src_hash dst_hash old_manifest_hash
        src_hash="$(compute_sha256_normalized "$src")"
        local dst="$TARGET/$rel"
        dst_hash=""
        [ -f "$dst" ] && dst_hash="$(compute_sha256_normalized "$dst")"
        old_manifest_hash="$(manifest_lookup_hash "$rel")"
        _deploy_file_now "$src" "$rel" "$do_chmod" "$src_hash" "$dst_hash" "$old_manifest_hash"
    fi
}

# --- process_queue: flush the deploy queue using batch normalized hashing ---
# Called once after the last deploy_file call site, before the .gitignore block.
# Reads _DEPLOY_QUEUE_TMP, batch-hashes all src + existing dst files using Python
# (single process, EOL-normalized), loads the old manifest into a lookup array,
# then calls _deploy_file_now for each queued entry with hashes supplied from the
# caches.  Falls back to per-file compute_sha256_normalized when Python is
# unavailable or when Python cannot resolve a path (e.g. MSYS /tmp/ paths).
process_queue() {
    [ -s "$_DEPLOY_QUEUE_TMP" ] || return 0

    # --- Load old manifest into associative array (O(n) lookup) ---
    declare -A _mfst_hash=()
    if [ -f "$MANIFEST_FILE" ]; then
        while IFS= read -r _mline; do
            case "$_mline" in
                core\ *|scaffold\ *|wrapper\ *)
                    _mrel="${_mline#* }"; _mrel="${_mrel%% *}"
                    _mh="${_mline##* }"; _mh="${_mh#sha256:}"
                    _mfst_hash["$_mrel"]="$_mh"
                    ;;
            esac
        done < "$MANIFEST_FILE"
    fi

    # --- Collect src paths and existing dst paths ---
    declare -A _src_hash=()
    declare -A _dst_hash=()

    # Build NUL-delimited lists of src paths and existing dst paths
    local _src_list_tmp _dst_list_tmp
    _src_list_tmp="$(mktemp)"
    _dst_list_tmp="$(mktemp)"

    # First pass: parse queue, enumerate paths
    local _q_src _q_rel _q_chmod _q_dst
    while IFS=$'\t' read -r _q_src _q_rel _q_chmod; do
        printf '%s\0' "$_q_src" >> "$_src_list_tmp"
        _q_dst="$TARGET/$_q_rel"
        [ -f "$_q_dst" ] && printf '%s\0' "$_q_dst" >> "$_dst_list_tmp"
    done < "$_DEPLOY_QUEUE_TMP"

    # --- Batch EOL-normalized hash using Python (when available) ---
    # Python reads each NUL-delimited path, strips bare CRs, and computes
    # SHA-256 in a single process — identical to compute_sha256_normalized.
    # This avoids two MSYS pitfalls:
    #   1. sha256sum outputs "<hash>  *<path>" (binary-mode marker) on MSYS,
    #      corrupting associative-array keys on raw output.
    #   2. grep -P '\r' (or grep -l $'\r') silently strips CRs in MSYS text
    #      mode, making CR-detection unreliable — CRLF files always missed.
    # Output format: ONE line per input path, IN ORDER — the hash hex or MISS.
    # (Hash-only by design: path strings never round-trip through Python.)
    _PYTHON_CMD=""
    for _py_cand in python3 python py; do
        if command -v "$_py_cand" >/dev/null 2>&1; then
            _PYTHON_CMD="$_py_cand"
            break
        fi
    done

    # Emits exactly ONE line per input path, IN ORDER: the normalized sha256 hex,
    # or the sentinel MISS when the file can't be read. Order-pairing (not path-key
    # matching) is load-bearing: path strings never round-trip through Python, so
    # neither CRLF-on-stdout nor MSYS-vs-native path forms can corrupt cache keys —
    # both failure modes were hit in earlier revisions of this function (all 187
    # lookups silently missed and fell back to per-file spawns).
    # Path translation: cygpath -f - batch-translates MSYS paths (/tmp/x, /c/x, …)
    # to native form for Python's open(); on POSIX hosts cygpath is absent and
    # paths are already native. Constraint: paths must not contain newlines
    # (repo-controlled deploy set — none do).
    _batch_hash_normalized() {
        local _list_file="$1"
        [ -s "$_list_file" ] || return 0
        if [ -n "$_PYTHON_CMD" ]; then
            # Translate to a newline-separated temp file (cygpath batch when on
            # MSYS) and hand it to Python as ARGV — the script goes via -c, so
            # neither competes for stdin (a heredoc-fed `python -` clobbered the
            # path pipe in an earlier revision: 0 output lines, full fallback).
            local _xlat_tmp _xlat_arg
            _xlat_tmp="$(mktemp)"
            if command -v cygpath >/dev/null 2>&1; then
                tr '\0' '\n' < "$_list_file" | cygpath -m -f - > "$_xlat_tmp" 2>/dev/null
                _xlat_arg="$(cygpath -m "$_xlat_tmp")"   # the temp path itself needs translating too
            else
                tr '\0' '\n' < "$_list_file" > "$_xlat_tmp"
                _xlat_arg="$_xlat_tmp"
            fi
            "$_PYTHON_CMD" -c '
import sys, hashlib
with open(sys.argv[1], "rb") as f:
    lines = f.read().splitlines()
for raw in lines:
    raw = raw.rstrip(b"\r")
    if not raw:
        sys.stdout.buffer.write(b"MISS\n")
        continue
    try:
        content = open(raw.decode("utf-8", "surrogateescape"), "rb").read()
        content = content.replace(b"\r\n", b"\n").replace(b"\r", b"")
        sys.stdout.buffer.write(hashlib.sha256(content).hexdigest().encode("ascii") + b"\n")
    except Exception:
        sys.stdout.buffer.write(b"MISS\n")
' "$_xlat_arg"
            rm -f "$_xlat_tmp"
        else
            # Python unavailable: per-file normalized hashing via shell (O(n) spawns,
            # last resort; batch path already requires Bash 4+).
            local _p
            while IFS= read -r -d '' _p; do
                if [ -f "$_p" ]; then
                    printf '%s\n' "$(compute_sha256_normalized "$_p")"
                else
                    printf 'MISS\n'
                fi
            done < "$_list_file"
        fi
    }

    # Pair hashes back to paths BY ORDER. If the line count ever disagrees with
    # the key count, discard the whole cache — per-entry inline fallbacks in the
    # second pass keep behavior correct (just slower), never wrong.
    _fill_hash_cache() {
        local _list_file="$1" _cache_name="$2"
        local -n _cache_ref="$_cache_name"
        local _keys=() _p _h _i=0
        while IFS= read -r -d '' _p; do _keys+=("$_p"); done < "$_list_file"
        while IFS= read -r _h; do
            if [ "$_i" -lt "${#_keys[@]}" ] && [ "$_h" != "MISS" ]; then
                _cache_ref["${_keys[$_i]}"]="$_h"
            fi
            _i=$((_i + 1))
        done < <(_batch_hash_normalized "$_list_file")
        if [ "$_i" -ne "${#_keys[@]}" ]; then
            echo "  note: batch hash count mismatch (${_i}/${#_keys[@]}) — using per-file fallback" >&2
            _cache_ref=()
        fi
    }

    _fill_hash_cache "$_src_list_tmp" _src_hash
    _fill_hash_cache "$_dst_list_tmp" _dst_hash

    rm -f "$_src_list_tmp" "$_dst_list_tmp"

    # --- Second pass: call _deploy_file_now for each queued entry ---
    while IFS=$'\t' read -r _q_src _q_rel _q_chmod; do
        _q_dst="$TARGET/$_q_rel"
        local _sh="${_src_hash[$_q_src]:-}"
        # Fallback: if batch hash missed this file (e.g. Python unavailable or path
        # unresolvable), compute inline so behavior degrades gracefully.
        [ -z "$_sh" ] && _sh="$(compute_sha256_normalized "$_q_src")"
        local _dh="${_dst_hash[$_q_dst]:-}"
        # Fallback for dst: if file exists but batch missed it, compute inline.
        [ -z "$_dh" ] && [ -f "$_q_dst" ] && _dh="$(compute_sha256_normalized "$_q_dst")"
        local _omh="${_mfst_hash[$_q_rel]:-}"
        _deploy_file_now "$_q_src" "$_q_rel" "$_q_chmod" "$_sh" "$_dh" "$_omh"
    done < "$_DEPLOY_QUEUE_TMP"
}

# ============================================================
# MAIN
# ============================================================

DEPLOYED_FILES_TMP="$(mktemp)"
_DEPLOY_QUEUE_TMP="$(mktemp)"
trap 'rm -f "$DEPLOYED_FILES_TMP" "$_DEPLOY_QUEUE_TMP" "${_src_list_tmp:-}" "${_dst_list_tmp:-}" "${_xlat_tmp:-}" "${TMP_STRIPPED_GITIGNORE:-}" "${TMP_NORMALIZED_GITIGNORE:-}" "${GITIGNORE:-}.tmp"' EXIT

SOURCE_COMMIT="$(get_source_commit)"
IS_UPDATE=false

if [ -f "$MANIFEST_FILE" ]; then
    IS_UPDATE=true
    echo "Updating Agentic OS v${ACX_VERSION} (${SOURCE_COMMIT}) in $TARGET..."
    clean_acx_incoming
else
    echo "Installing Agentic OS v${ACX_VERSION} (${SOURCE_COMMIT}) to $TARGET..."
fi

# --- Migrate from legacy paths (v5.3 → v6) ---
# If the target has old-style paths, move them to the new locations.
migrate_if_exists() {
    local old_path="$TARGET/$1"
    local new_path="$TARGET/$2"
    if [ -e "$old_path" ] && [ ! -e "$new_path" ]; then
        mkdir -p "$(dirname "$new_path")"
        mv "$old_path" "$new_path"
        echo "  [MIGRATE] $1 → $2"
    elif [ -e "$old_path" ] && [ -e "$new_path" ]; then
        # Both exist — remove old one (new takes precedence from deploy)
        rm -rf "$old_path"
        echo "  [MIGRATE] removed legacy $1 (already at $2)"
    fi
}

# Migration safety: only trigger if we find Agentic OS-specific markers.
# A bare agentcortex/ dir is unambiguously ours. But docs/adr/ or docs/specs/
# could belong to the downstream project. We only migrate docs/ subdirs if
# there is ALSO an old agentcortex/ dir or a prior .agentcortex-manifest
# (proving this repo had a previous Agentic OS install).
_acx_legacy_confirmed=false
if [ -d "$TARGET/agentcortex" ] || [ -f "$TARGET/.agentcortex-manifest" ]; then
    _acx_legacy_confirmed=true
fi

# Banner only when actual legacy ARTIFACTS exist — a bare .agentcortex-manifest
# is the normal installed state, and announcing "Migrating from legacy paths"
# on every routine update was pure noise (sim finding 2026-06-11). The block
# still runs for manifest-only targets (its steps are silent no-ops).
_acx_legacy_artifacts=false
if [ -d "$TARGET/agentcortex" ] || [ -d "$TARGET/docs/context" ] || \
   [ -f "$TARGET/tools/validate.sh" ] || [ -f "$TARGET/tools/validate.ps1" ] || \
   [ -f "$TARGET/tools/validate.cmd" ]; then
    _acx_legacy_artifacts=true
fi

if $_acx_legacy_confirmed || [ -f "$TARGET/tools/validate.sh" ] || \
   [ -f "$TARGET/tools/validate.ps1" ] || [ -f "$TARGET/tools/validate.cmd" ]; then
    if $_acx_legacy_artifacts; then
        echo ""
        echo "Migrating from legacy paths..."
    fi

    # agentcortex/ → .agentcortex/ (unambiguously ours)
    if [ -d "$TARGET/agentcortex" ]; then
        for item in "$TARGET/agentcortex"/*; do
            [ -e "$item" ] || continue
            bname="$(basename "$item")"
            migrate_if_exists "agentcortex/$bname" ".agentcortex/$bname"
        done
        rmdir "$TARGET/agentcortex" 2>/dev/null || true
    fi

    # docs/ subdirs — ONLY migrate if we confirmed this is a legacy ACX install.
    # Without confirmation, docs/adr/ or docs/specs/ might belong to the project.
    if $_acx_legacy_confirmed; then
        # docs/context/ → .agentcortex/context/ (ACX-specific path, safe to migrate)
        migrate_if_exists "docs/context/current_state.md" ".agentcortex/context/current_state.md"
        migrate_if_exists "docs/context/archive" ".agentcortex/context/archive"
        migrate_if_exists "docs/context/work" ".agentcortex/context/work"
        migrate_if_exists "docs/context/private" ".agentcortex/context/private"

        # docs/adr/ is the canonical downstream ADR path (fixed anchor) — do NOT migrate

        # docs/specs/ is the canonical downstream spec path (fixed anchor) — do NOT migrate

        # --- Orphaned spec/ADR recovery (ace7fea victims) ---
        # The ace7fea commit incorrectly wrote downstream specs/ADRs into
        # .agentcortex/specs/ and .agentcortex/adr/. Detect non-framework
        # files and migrate them to the correct docs/ paths.
        _framework_specs="template-import-cleanup.md red-team-skill.md gitignore-full-deploy.md manifest-deploy.md"
        for spec_file in "$TARGET/.agentcortex/specs"/*.md; do
            [ -f "$spec_file" ] || continue
            bname="$(basename "$spec_file")"
            _is_framework=false
            for fw in $_framework_specs; do
                [ "$bname" = "$fw" ] && _is_framework=true && break
            done
            if ! $_is_framework; then
                mkdir -p "$TARGET/docs/specs"
                if [ -e "$TARGET/docs/specs/$bname" ]; then
                    echo "  [SKIP] docs/specs/$bname already exists — orphaned copy left in .agentcortex/specs/$bname (resolve manually)"
                else
                    mv "$spec_file" "$TARGET/docs/specs/$bname"
                    echo "  [MIGRATE] recovered orphaned spec: .agentcortex/specs/$bname → docs/specs/$bname"
                fi
            fi
        done

        # Framework ADRs that historically lived under .agentcortex/adr/ — match
        # by filename so a downstream project's own ADR-001 is never mistaken
        # for the framework's. Keep in sync with .agentcortex/adr/ contents.
        _framework_adrs="ADR-001-vnext-self-managed-architecture.md"
        for adr_file in "$TARGET/.agentcortex/adr"/*.md; do
            [ -f "$adr_file" ] || continue
            bname="$(basename "$adr_file")"
            _is_framework=false
            for fw in $_framework_adrs; do
                [ "$bname" = "$fw" ] && _is_framework=true && break
            done
            $_is_framework && continue
            mkdir -p "$TARGET/docs/adr"
            if [ -e "$TARGET/docs/adr/$bname" ]; then
                echo "  [SKIP] docs/adr/$bname already exists — orphaned copy left in .agentcortex/adr/$bname (resolve manually)"
            else
                mv "$adr_file" "$TARGET/docs/adr/$bname"
                echo "  [MIGRATE] recovered orphaned ADR: .agentcortex/adr/$bname → docs/adr/$bname"
            fi
        done

        # Clean empty legacy dirs (rmdir only removes EMPTY dirs — safe)
        rmdir "$TARGET/docs/context" 2>/dev/null || true
        # NOTE: docs/adr/ and docs/specs/ are fixed anchors — do NOT rmdir
    fi

    # tools/validate.* → removed (no longer deployed as wrappers)
    for ext in sh ps1 cmd; do
        [ -f "$TARGET/tools/validate.$ext" ] && rm -f "$TARGET/tools/validate.$ext" && echo "  [MIGRATE] removed legacy tools/validate.$ext"
    done
    rmdir "$TARGET/tools" 2>/dev/null || true

    if $_acx_legacy_artifacts; then
        echo "  Migration complete."
        echo ""
    fi
fi

# --- Pre-deploy write permission check ---
if [ ! -d "$TARGET" ]; then
    mkdir -p "$TARGET" 2>/dev/null || true
fi
if [ -e "$TARGET" ] && [ ! -d "$TARGET" ]; then
    echo "" >&2
    echo "ERROR: Target path exists but is not a directory: $TARGET" >&2
    echo "Fix: provide a directory path, not a file." >&2
    exit 1
fi
if [ ! -w "$TARGET" ]; then
    echo "" >&2
    echo "ERROR: Target directory is not writable: $TARGET" >&2
    echo "Fix: check permissions or run with appropriate privileges." >&2
    exit 1
fi

DOWNSTREAM_CURRENT_STATE_TEMPLATE="$REPO_ROOT/.agentcortex/templates/current_state.md"
if [ ! -f "$DOWNSTREAM_CURRENT_STATE_TEMPLATE" ]; then
    echo "" >&2
    echo "ERROR: Missing downstream current_state template: .agentcortex/templates/current_state.md" >&2
    echo "Deploy refuses to install the source repository's live .agentcortex/context/current_state.md downstream." >&2
    exit 1
fi

# --- Dry-run mode: preview only ---
if $DRY_RUN; then
    echo ""
    echo "[DRY RUN] Would deploy Agentic OS v${ACX_VERSION} (${SOURCE_COMMIT}) to $TARGET"
    echo ""
    echo "Directories that would be created:"
    for d in \
        ".agent/rules" ".agent/workflows" ".agent/skills" \
        ".antigravity" ".agents/skills" ".claude/commands" ".claude/agents" \
        ".codex" "codex/rules" ".github/ISSUE_TEMPLATE" \
        ".agentcortex/bin" ".agentcortex/metadata" ".agentcortex/tools" \
        ".agentcortex/docs/guides" ".agentcortex/context/work" \
        ".agentcortex/context/archive" \
        ".agentcortex/templates" ".agentcortex/adr" ".agentcortex/specs" \
        "docs/specs" "docs/adr"; do
        [ -d "$TARGET/$d" ] || echo "  [NEW DIR] $d"
    done
    echo ""
    echo "Files that would be deployed (core tier = always overwrite, scaffold = skip if modified):"
    _dry_count=0
    # Enumerate only the files that are actually deployed (mirrors real deploy logic).
    # Runtime Python tools are a whitelist — NOT all *.py in tools/.
    _runtime_tools="guard_context_write.py _yaml_loader.py check_command_sync.py check_text_integrity.py check_text_integrity.ps1 text_integrity_baseline.txt sync_skills.sh lint_governed_writes.py check_lifecycle_frontmatter.py check_lesson_chain.py check_adr_coverage.py append_chain_entry.py append_lesson.py recover_worklog_lock.py lint_spec_drift.py run_governance_eval.py scan_credentials.py credential_floor.sh credential_floor.ps1 generate_safety_nucleus.py validate_downstream_capabilities.py"
    _dry_print_file() {
        local src="$1"
        local rel="$2"
        [ -f "$src" ] || return 0
        _dry_count=$((_dry_count + 1))
        _get_tier_inline "$rel"
        local status="[NEW]   "
        [ -f "$TARGET/$rel" ] && status="[UPDATE]"
        printf '  %s %-10s %s\n' "$status" "($_TIER)" "$rel"
    }
    for f in "$REPO_ROOT"/AGENTS.md "$REPO_ROOT"/CLAUDE.md "$REPO_ROOT"/GEMINI.md \
             "$REPO_ROOT"/.gitattributes \
             "$REPO_ROOT"/installers/deploy_brain.sh "$REPO_ROOT"/installers/deploy_brain.ps1 "$REPO_ROOT"/installers/deploy_brain.cmd \
             "$REPO_ROOT"/.antigravity/rules.md "$REPO_ROOT"/codex/rules/default.rules \
             "$REPO_ROOT"/.agent/rules/*.md "$REPO_ROOT"/.agent/config.yaml \
             "$REPO_ROOT"/.agent/workflows/*.md \
             "$REPO_ROOT"/.agentcortex/bin/deploy.sh "$REPO_ROOT"/.agentcortex/bin/deploy.ps1 \
             "$REPO_ROOT"/.agentcortex/bin/validate.sh "$REPO_ROOT"/.agentcortex/bin/validate.ps1 \
             "$REPO_ROOT"/.agentcortex/metadata/trigger-registry.yaml "$REPO_ROOT"/.agentcortex/metadata/trigger-compact-index.json \
             "$REPO_ROOT"/.agentcortex/templates/* \
             "$REPO_ROOT"/.agentcortex/adr/*.md \
             "$REPO_ROOT"/.claude/settings.json \
             "$REPO_ROOT"/.claude/agents/*.md \
             "$REPO_ROOT"/.codex/INSTALL.md \
             "$REPO_ROOT"/.github/ISSUE_TEMPLATE/*.md "$REPO_ROOT"/.github/PULL_REQUEST_TEMPLATE.md \
             "$REPO_ROOT"/.github/copilot-instructions.md; do
        _dry_print_file "$f" "${f#$REPO_ROOT/}"
    done
    # Generated downstream runtime SSoT: source template installs to context/current_state.md.
    _dry_print_file "$DOWNSTREAM_CURRENT_STATE_TEMPLATE" ".agentcortex/context/current_state.md"
    # Runtime tools (whitelist only — not all *.py)
    for _bname in $_runtime_tools; do
        f="$REPO_ROOT/.agentcortex/tools/$_bname"
        _dry_print_file "$f" ".agentcortex/tools/$_bname"
    done
    # ADR-008 portable safety nucleus (core tier; deployed to .agentcortex/AGENTS.safety.md)
    if [ -f "$REPO_ROOT/.agentcortex/AGENTS.safety.md" ]; then
        _dry_print_file "$REPO_ROOT/.agentcortex/AGENTS.safety.md" ".agentcortex/AGENTS.safety.md"
    fi
    # Skills (summarise counts instead of listing every file)
    _skill_count=0
    for skill_dir in "$REPO_ROOT/.agents/skills"/*/; do
        [ -d "$skill_dir" ] || continue
        while IFS= read -r -d '' sf; do _skill_count=$((_skill_count + 1)); done \
            < <(find "$skill_dir" -type f -print0)
    done
    for sf in "$REPO_ROOT"/.agent/skills/*; do [ -f "$sf" ] && _skill_count=$((_skill_count + 1)); done
    [ "$_skill_count" -gt 0 ] && echo "  [NEW]    (mixed)    ... $_skill_count skill files under .agent/skills/ and .agents/skills/"
    # Docs (summarise)
    _doc_count=0
    for df in "$REPO_ROOT"/.agentcortex/docs/*.md "$REPO_ROOT"/.agentcortex/docs/guides/*.md \
              "$REPO_ROOT"/README.md "$REPO_ROOT"/docs/README_zh-TW.md; do
        [ -f "$df" ] && _doc_count=$((_doc_count + 1))
    done
    [ "$_doc_count" -gt 0 ] && echo "  [NEW]    (mixed)    ... $_doc_count reference docs under .agentcortex/docs/"
    # Claude commands
    _cmd_count=0
    for cf in "$REPO_ROOT"/.claude/commands/*; do [ -f "$cf" ] && _cmd_count=$((_cmd_count + 1)); done
    [ "$_cmd_count" -gt 0 ] && echo "  [NEW]    (core)     ... $_cmd_count Claude slash command adapters under .claude/commands/"
    echo ""
    echo "Total: ~$((_dry_count + _skill_count + _doc_count + _cmd_count)) files would be deployed."
    echo "Run without --dry-run to apply."
    exit 0
fi

# --- Create directory structure ---
mkdir -p "$TARGET/.agent/rules"
mkdir -p "$TARGET/.agent/workflows"
mkdir -p "$TARGET/.agent/skills"
mkdir -p "$TARGET/.antigravity"
mkdir -p "$TARGET/.agents/skills"
mkdir -p "$TARGET/.claude/commands"
mkdir -p "$TARGET/.claude/agents"
mkdir -p "$TARGET/.codex"
mkdir -p "$TARGET/codex/rules"
mkdir -p "$TARGET/.github/ISSUE_TEMPLATE"
mkdir -p "$TARGET/.agentcortex/bin"
mkdir -p "$TARGET/.agentcortex/metadata"
mkdir -p "$TARGET/.agentcortex/tools"
mkdir -p "$TARGET/.agentcortex/docs/guides"
mkdir -p "$TARGET/.agentcortex/context/work"
mkdir -p "$TARGET/.agentcortex/context/archive"
mkdir -p "$TARGET/.agentcortex/context/archive/work"
mkdir -p "$TARGET/.agentcortex/templates"
mkdir -p "$TARGET/.agentcortex/adr"
mkdir -p "$TARGET/.agentcortex/specs"
mkdir -p "$TARGET/docs/specs"
mkdir -p "$TARGET/docs/adr"

# --- Deploy: root governance files (core) ---
deploy_file "$REPO_ROOT/AGENTS.md" "AGENTS.md"
deploy_file "$REPO_ROOT/CLAUDE.md" "CLAUDE.md"
deploy_file "$REPO_ROOT/GEMINI.md" "GEMINI.md"

# --- Deploy: .gitattributes (scaffold — user may extend) ---
deploy_file "$REPO_ROOT/.gitattributes" ".gitattributes"

# --- Deploy: wrapper scripts (into installers/ — not root) ---
mkdir -p "$TARGET/installers"
deploy_file "$REPO_ROOT/installers/deploy_brain.sh" "installers/deploy_brain.sh" "+x"
deploy_file "$REPO_ROOT/installers/deploy_brain.ps1" "installers/deploy_brain.ps1"
deploy_file "$REPO_ROOT/installers/deploy_brain.cmd" "installers/deploy_brain.cmd"

# --- Deploy: platform rules (core) ---
deploy_file "$REPO_ROOT/.antigravity/rules.md" ".antigravity/rules.md"
deploy_file "$REPO_ROOT/codex/rules/default.rules" "codex/rules/default.rules"
# --- Deploy: .agent/rules (core) ---
for f in "$REPO_ROOT"/.agent/rules/*.md; do
    [ -f "$f" ] || continue
    # ${f##*/} avoids a $(basename) subshell (parameter expansion is built-in)
    deploy_file "$f" ".agent/rules/${f##*/}"
done

# --- Deploy: .agent/config.yaml (core) ---
deploy_file "$REPO_ROOT/.agent/config.yaml" ".agent/config.yaml"

# --- Deploy: workflows (core) ---
for f in "$REPO_ROOT"/.agent/workflows/*.md; do
    [ -f "$f" ] || continue
    deploy_file "$f" ".agent/workflows/${f##*/}"
done

# --- Deploy: skills (core) ---
# .agent/skills/ has flat metadata files; .agents/skills/ has directory-based skills.
# Deploy each to its own target — do NOT mirror across since structures differ.

# Flat skill metadata files → .agent/skills/
for skill_file in "$REPO_ROOT"/.agent/skills/*; do
    [ -f "$skill_file" ] || continue
    bname="${skill_file##*/}"
    [ "$bname" = ".gitkeep" ] && continue
    deploy_file "$skill_file" ".agent/skills/$bname"
done

# Directory-based skills → .agents/skills/
if [ -d "$REPO_ROOT/.agents/skills" ]; then
    for skill_dir in "$REPO_ROOT/.agents/skills"/*/; do
        [ -d "$skill_dir" ] || continue
        skill_name="${skill_dir%/}"; skill_name="${skill_name##*/}"
        # Guard: if a legacy flat file exists where a directory is needed, remove it
        if [ -f "$TARGET/.agents/skills/$skill_name" ]; then
            rm -f "$TARGET/.agents/skills/$skill_name"
            echo "  [MIGRATE] removed flat file .agents/skills/$skill_name (now a directory)"
        fi
        mkdir -p "$TARGET/.agents/skills/$skill_name"
        # Deploy all files recursively, preserving subdir structure (e.g. agents/openai.yaml)
        while IFS= read -r -d '' skill_file; do
            rel_to_skill="${skill_file#$skill_dir}"
            # ${path%/*} avoids a $(dirname) subshell
            _parent=".agents/skills/$skill_name/${rel_to_skill%/*}"
            [ "$_parent" = ".agents/skills/$skill_name/$rel_to_skill" ] && _parent=".agents/skills/$skill_name"
            mkdir -p "$TARGET/$_parent"
            deploy_file "$skill_file" ".agents/skills/$skill_name/$rel_to_skill"
        done < <(find "$skill_dir" -type f -print0)
    done
fi

touch "$TARGET/.agent/skills/.gitkeep"
touch "$TARGET/.agents/skills/.gitkeep"

# Ensure directories survive git clone (git doesn't track empty dirs).
# Deploy .gitkeep.md from source if available; fall back to a plain touch.
for _keep_pair in \
    ".agentcortex/context/work/.gitkeep.md" \
    "docs/specs/.gitkeep.md" \
    "docs/adr/.gitkeep.md"; do
    if [ -f "$REPO_ROOT/$_keep_pair" ]; then
        cp ${CP_FLAG:+"$CP_FLAG"} "$REPO_ROOT/$_keep_pair" "$TARGET/$_keep_pair"
    else
        touch "$TARGET/$_keep_pair"
    fi
done

# --- Deploy: .agentcortex/bin (core) ---
for f in deploy.sh deploy.ps1 validate.sh validate.ps1; do
    [ -f "$REPO_ROOT/.agentcortex/bin/$f" ] || continue
    chmod_flag=""
    case "$f" in *.sh) chmod_flag="+x" ;; esac
    deploy_file "$REPO_ROOT/.agentcortex/bin/$f" ".agentcortex/bin/$f" "$chmod_flag"
done

# --- Deploy: .agentcortex/metadata (runtime artifacts only; optional when present in source repo) ---
for f in trigger-registry.yaml trigger-compact-index.json; do
    [ -f "$REPO_ROOT/.agentcortex/metadata/$f" ] || continue
    deploy_file "$REPO_ROOT/.agentcortex/metadata/$f" ".agentcortex/metadata/$f"
done

# --- Deploy: .agentcortex/tools (runtime artifacts only; optional when present in source repo) ---
runtime_tools=(
  guard_context_write.py
  _yaml_loader.py
  check_command_sync.py
  check_text_integrity.py
  check_text_integrity.ps1
  text_integrity_baseline.txt
  sync_skills.sh
  lint_governed_writes.py
  check_lifecycle_frontmatter.py
  check_lesson_chain.py
  check_adr_coverage.py
  append_chain_entry.py
  append_lesson.py
  recover_worklog_lock.py
  lint_spec_drift.py
  run_governance_eval.py
  scan_credentials.py
  credential_floor.sh
  credential_floor.ps1
  generate_safety_nucleus.py
  validate_downstream_capabilities.py
)
for bname in "${runtime_tools[@]}"; do
    f="$REPO_ROOT/.agentcortex/tools/$bname"
    [ -f "$f" ] || continue
    chmod_flag=""
    case "$bname" in *.sh) chmod_flag="+x" ;; esac
    deploy_file "$f" ".agentcortex/tools/$bname" "$chmod_flag"
done

# --- Deploy: .agentcortex/AGENTS.safety.md (core - portable safety nucleus, ADR-008) ---
# Committed generated file (generate_safety_nucleus.py); a non-shim harness injects it
# into every dispatched subagent. Core tier -> reaches all downstream on update.
if [ -f "$REPO_ROOT/.agentcortex/AGENTS.safety.md" ]; then
    deploy_file "$REPO_ROOT/.agentcortex/AGENTS.safety.md" ".agentcortex/AGENTS.safety.md"
fi

# --- Deploy: .agentcortex/context/current_state.md (scaffold) ---
# Use the downstream template (generic placeholders) instead of the
# framework's own SSoT which contains Agentic OS project-specific content.
deploy_file "$DOWNSTREAM_CURRENT_STATE_TEMPLATE" ".agentcortex/context/current_state.md"

# --- Deploy: .agentcortex/templates (scaffold) ---
for f in "$REPO_ROOT"/.agentcortex/templates/*; do
    [ -f "$f" ] || continue
    deploy_file "$f" ".agentcortex/templates/${f##*/}"
done

# --- Deploy: .agentcortex/adr (scaffold) ---
for f in "$REPO_ROOT"/.agentcortex/adr/*.md; do
    [ -f "$f" ] || continue
    deploy_file "$f" ".agentcortex/adr/${f##*/}"
done

# --- Deploy: reference docs to .agentcortex/docs/ (core) ---
for f in \
  "$REPO_ROOT"/README.md \
  "$REPO_ROOT"/docs/README_zh-TW.md \
  "$REPO_ROOT"/docs/AGENT_MODEL_GUIDE*.md \
  "$REPO_ROOT"/.agentcortex/docs/AGENT_PHILOSOPHY*.md \
  "$REPO_ROOT"/.agentcortex/docs/TESTING_PROTOCOL*.md \
  "$REPO_ROOT"/.agentcortex/docs/CODEX_PLATFORM_GUIDE*.md \
  "$REPO_ROOT"/.agentcortex/docs/PROJECT_EXAMPLES*.md \
  "$REPO_ROOT"/.agentcortex/docs/PROJECT_OVERVIEW*.md \
  "$REPO_ROOT"/.agentcortex/docs/NONLINEAR_SCENARIOS*.md \
  "$REPO_ROOT"/.agentcortex/docs/CLAUDE_PLATFORM_GUIDE*.md; do
  [ -f "$f" ] || continue
  deploy_file "$f" ".agentcortex/docs/${f##*/}"
done
for f in "$REPO_ROOT"/.agentcortex/docs/guides/*.md; do
    [ -f "$f" ] || continue
    deploy_file "$f" ".agentcortex/docs/guides/${f##*/}"
done
# Downstream-facing quickstart guides live in framework's docs/guides/ (root-style path).
# Deploy them to .agentcortex/docs/guides/ alongside the framework-internal guides.
for f in "$REPO_ROOT"/docs/guides/token-optimization-quickstart*.md; do
    [ -f "$f" ] || continue
    deploy_file "$f" ".agentcortex/docs/guides/${f##*/}"
done

# --- Deploy: .claude/commands (core) ---
if [ -d "$REPO_ROOT/.claude/commands" ]; then
    for f in "$REPO_ROOT"/.claude/commands/*; do
        [ -f "$f" ] || continue
        deploy_file "$f" ".claude/commands/${f##*/}"
    done
fi

# --- Deploy: .claude/agents (core — acx-* sub-agent shims for native skill injection) ---
if [ -d "$REPO_ROOT/.claude/agents" ]; then
    mkdir -p "$TARGET/.claude/agents"
    for f in "$REPO_ROOT"/.claude/agents/*.md; do
        [ -f "$f" ] || continue
        deploy_file "$f" ".claude/agents/${f##*/}"
    done
fi

# --- Deploy: .claude/settings.json (scaffold — user may extend permissions/env) ---
if [ -f "$REPO_ROOT/.claude/settings.json" ]; then
    mkdir -p "$TARGET/.claude"
    deploy_file "$REPO_ROOT/.claude/settings.json" ".claude/settings.json"
fi

# --- Deploy: .codex/INSTALL.md (core) ---
deploy_file "$REPO_ROOT/.codex/INSTALL.md" ".codex/INSTALL.md"

# --- Deploy: .github/ templates (core) ---
for f in "$REPO_ROOT"/.github/ISSUE_TEMPLATE/*.md; do
    [ -f "$f" ] || continue
    deploy_file "$f" ".github/ISSUE_TEMPLATE/${f##*/}"
done
deploy_file "$REPO_ROOT/.github/PULL_REQUEST_TEMPLATE.md" ".github/PULL_REQUEST_TEMPLATE.md"

# --- Deploy: .github/copilot-instructions.md (scaffold) ---
# GitHub Copilot's repo-wide entry point (points at AGENTS.md). AGENTS.md alone
# only covers Copilot's coding-agent surface; the IDE custom-instructions surface
# reads this file. Scaffold tier so an adopter's own copilot-instructions.md is
# preserved (.acx-incoming) instead of overwritten.
if [ -f "$REPO_ROOT/.github/copilot-instructions.md" ]; then
    deploy_file "$REPO_ROOT/.github/copilot-instructions.md" ".github/copilot-instructions.md"
fi

# --- Deploy: .githooks/ advisory hook samples (scaffold) ---
if [ -f "$REPO_ROOT/.githooks/pre-commit.guard-ssot.sample" ]; then
    mkdir -p "$TARGET/.githooks"
    deploy_file "$REPO_ROOT/.githooks/pre-commit.guard-ssot.sample" ".githooks/pre-commit.guard-ssot.sample"
fi

# --- Flush deploy queue (batch hashing — Bash 4+ path) ---
# All deploy_file calls above have queued their records; process_queue now
# batch-hashes them in two single-process passes (one over src paths, one over
# existing dst paths; order-paired output) and calls _deploy_file_now per entry.
# No-op when _ACX_BATCH_OK=false (per-file path already ran inline above).
if $_ACX_BATCH_OK; then
    process_queue
fi

# ============================================================
# .gitignore management (special — block-managed, not file-level)
# ============================================================

GITIGNORE="$TARGET/.gitignore"
DOWNSTREAM_IGNORE_START="# Agentic OS Template - Downstream Ignore Defaults"
LEGACY_IGNORE_START="# AI Brain OS - Agent System & Local Context"

write_downstream_ignore_block() {
    cat <<'EOT'
# Agentic OS Template - Downstream Ignore Defaults

# Runtime State (work logs are session-local; private is never committed)
.agentcortex/context/work/*.md
.agentcortex/context/work/*.lock.json
!.agentcortex/context/work/.gitkeep.md
.agentcortex/context/.guard_receipt.json
.agentcortex/context/.guard_receipts/
.agentcortex/context/.guard_locks/
.agentcortex/context/private/
.agent/private/

# Deploy Artifacts
.agentcortex-src/
*.acx-incoming
*.acx-local

# Third-party AI Tool Local State
.openrouter/
.claude-chat/
.cursor/
.antigravity/scratch/

# End Agentic OS Template - Downstream Ignore Defaults
EOT
}

strip_managed_ignore_blocks() {
    local source_file="$1"
    local output_file="$2"

    awk '
    BEGIN {
        # Current managed entries
        managed[".agentcortex/context/work/*.md"] = 1
        managed[".agentcortex/context/work/*.lock.json"] = 1
        managed["!.agentcortex/context/work/.gitkeep.md"] = 1
        managed[".agentcortex/context/.guard_receipt.json"] = 1
        managed[".agentcortex/context/.guard_receipts/"] = 1
        managed[".agentcortex/context/.guard_locks/"] = 1
        managed[".agentcortex/context/private/"] = 1
        managed[".agent/private/"] = 1
        managed[".agentcortex-src/"] = 1
        managed["*.acx-incoming"] = 1
        managed["*.acx-local"] = 1
        managed[".openrouter/"] = 1
        managed[".claude-chat/"] = 1
        managed[".cursor/"] = 1
        managed[".antigravity/scratch/"] = 1
        # Legacy paths from older versions (strip during upgrade)
        managed["AGENTS.md"] = 1
        managed["CLAUDE.md"] = 1
        managed["GEMINI.md"] = 1
        managed[".agent/"] = 1
        managed[".agents/"] = 1
        managed[".antigravity/"] = 1
        managed[".claude/"] = 1
        managed[".codex/"] = 1
        managed["codex/"] = 1
        managed["agentcortex/"] = 1
        managed[".agentcortex/"] = 1
        managed["tools/validate.sh"] = 1
        managed["tools/validate.ps1"] = 1
        managed["tools/validate.cmd"] = 1
        managed[".github/ISSUE_TEMPLATE/bug_report.md"] = 1
        managed[".github/ISSUE_TEMPLATE/feature_request.md"] = 1
        managed[".github/PULL_REQUEST_TEMPLATE.md"] = 1
        managed["docs/adr/"] = 1
        managed["docs/context/work/*.md"] = 1
        managed["!docs/context/work/.gitkeep.md"] = 1
        managed["docs/context/private/"] = 1
        managed["docs/context/"] = 1
        managed["docs/context/current_state.md"] = 1
        managed["docs/context/work/"] = 1
        managed["docs/context/archive/"] = 1
        managed["README.md"] = 1
        managed["README_zh-TW.md"] = 1
        managed["AGENT_MODEL_GUIDE.md"] = 1
        managed["AGENT_MODEL_GUIDE_zh-TW.md"] = 1
        managed["CHANGELOG.md"] = 1
        managed["CITATION.cff"] = 1
        managed["CONTRIBUTING.md"] = 1
        managed["docs/AGENT_PHILOSOPHY.md"] = 1
        managed["docs/AGENT_PHILOSOPHY_zh-TW.md"] = 1
        managed["docs/CLAUDE_PLATFORM_GUIDE.md"] = 1
        managed["docs/CLAUDE_PLATFORM_GUIDE_zh-TW.md"] = 1
        managed["docs/CODEX_PLATFORM_GUIDE.md"] = 1
        managed["docs/CODEX_PLATFORM_GUIDE_zh-TW.md"] = 1
        managed["docs/PROJECT_EXAMPLES.md"] = 1
        managed["docs/PROJECT_EXAMPLES_zh-TW.md"] = 1
        managed["docs/TESTING_PROTOCOL.md"] = 1
        managed["docs/TESTING_PROTOCOL_zh-TW.md"] = 1
        managed["docs/guides/antigravity-v5-runtime.md"] = 1
        managed["docs/guides/audit-guardrails.md"] = 1
        managed["docs/guides/audit-guardrails_zh-TW.md"] = 1
        managed["docs/guides/migration.md"] = 1
        managed["docs/guides/migration_zh-TW.md"] = 1
        managed["docs/guides/multi-remote-workflow.md"] = 1
        managed["docs/guides/portable-minimal-kit.md"] = 1
        managed["docs/guides/token-governance.md"] = 1
        managed["docs/guides/token-governance_zh-TW.md"] = 1
        managed["docs/adr/ADR-001-vnext-self-managed-architecture.md"] = 1
        managed["tools/audit_ai_paths.sh"] = 1
    }

    /^# Agentic OS Template - Downstream Ignore Defaults$/ { skip = 1; next }
    /^# AI Brain OS - Agent System & Local Context$/ { skip = 1; next }
    /^# End Agentic OS Template - Downstream Ignore Defaults$/ { skip = 0; next }

    skip {
        if ($0 == "" || ($0 in managed) || $0 ~ /^#/) { next }
        skip = 0
    }

    { print }
    ' "$source_file" > "$output_file"
}

echo ""
echo "Checking .gitignore..."
if [ ! -f "$GITIGNORE" ]; then
    touch "$GITIGNORE"
fi

TMP_STRIPPED_GITIGNORE="$(mktemp)"
TMP_NORMALIZED_GITIGNORE="$(mktemp)"

if grep -Eq "^(${DOWNSTREAM_IGNORE_START}|${LEGACY_IGNORE_START})$" "$GITIGNORE"; then
    echo "Replacing managed downstream ignore defaults in .gitignore..."
else
    echo "Adding Agentic OS downstream ignore defaults to .gitignore..."
fi

strip_managed_ignore_blocks "$GITIGNORE" "$TMP_STRIPPED_GITIGNORE"

awk '
{
    lines[NR] = $0
}
END {
    last = NR
    while (last > 0 && lines[last] == "") {
        last--
    }
    for (i = 1; i <= last; i++) {
        print lines[i]
    }
}
' "$TMP_STRIPPED_GITIGNORE" > "$TMP_NORMALIZED_GITIGNORE"

{
    if [ -s "$TMP_NORMALIZED_GITIGNORE" ]; then
        cat "$TMP_NORMALIZED_GITIGNORE"
        printf '\n\n'
    fi
    write_downstream_ignore_block
    printf '\n'
} > "$GITIGNORE.tmp"
mv "$GITIGNORE.tmp" "$GITIGNORE"

rm -f "$TMP_STRIPPED_GITIGNORE" "$TMP_NORMALIZED_GITIGNORE"

# ============================================================
# Detect removed files (in old manifest but not deployed this run)
# ============================================================

if $IS_UPDATE; then
    # Use awk to diff old manifest vs deployed set in a single pass (O(n) vs O(n²))
    _removed_paths="$(awk '
        NR == FNR { deployed[$2] = 1; next }
        /^(core|scaffold|wrapper) / && !($2 in deployed) { print $2 }
    ' "$DEPLOYED_FILES_TMP" "$MANIFEST_FILE" 2>/dev/null)"
    while IFS= read -r old_path; do
        [ -z "$old_path" ] && continue
        if [ -f "$TARGET/$old_path" ]; then
            echo "  [REMOVED FROM TEMPLATE] $old_path (kept in your project; delete manually if unwanted)"
            COUNT_REMOVED=$((COUNT_REMOVED + 1))
        fi
    done <<< "$_removed_paths"
fi

# ============================================================
# Stale-skill detection (warn-only, no auto-delete)
# ============================================================
# Skills deleted upstream (retired) remain in deployed targets forever because
# the removed-files detector above only sees files tracked in the OLD manifest —
# it cannot fire for skills retired before a downstream's last deploy. This scan
# catches orphaned skills that are no longer part of the framework skill set.
#
# Behavior split (ADR-005 + binding expert design):
#
#   custom-*  → silent (unchanged; reserved project namespace).
#
#   Non-framework skill whose path appears in the OLD manifest (i.e., was once
#   deployed by the framework but is now gone from REPO_ROOT) → STALE SKILL:
#   emit "[STALE SKILL] ... retired upstream; delete it, or rename to custom-<name>"
#   and count in _stale_count / ⚠ block.
#
#   Non-framework skill ABSENT from the old manifest (or no manifest) → user-
#   created skill (the framework never shipped it). Do NOT emit per-skill STALE
#   warning and do NOT say "retired". Collect names and emit ONE aggregated note
#   after the scan.
#
# Manifest lookup for dir skill: any manifest path with prefix ".agents/skills/<name>/"
# Manifest lookup for flat skill: exact manifest path ".agent/skills/<name>"
#
# Reuse the batch-loaded manifest hash table when available (batch path set
# $_mfst_hash during process_queue); otherwise fall back to awk per entry.

_framework_flat_skills=""
for _sf in "$REPO_ROOT"/.agent/skills/*; do
    [ -f "$_sf" ] || continue
    _bname="${_sf##*/}"
    [ "$_bname" = ".gitkeep" ] && continue
    _framework_flat_skills="$_framework_flat_skills $_bname"
done

_framework_dir_skills=""
if [ -d "$REPO_ROOT/.agents/skills" ]; then
    for _sd in "$REPO_ROOT/.agents/skills"/*/; do
        [ -d "$_sd" ] || continue
        _sdname="${_sd%/}"; _sdname="${_sdname##*/}"
        _framework_dir_skills="$_framework_dir_skills $_sdname"
    done
fi

_stale_count=0
_user_skill_names=""   # aggregated list of user-created (non-framework) skill names

# Helper: check if a skill path prefix appears in the OLD manifest.
# $1 = exact rel path (flat skill) or prefix (dir skill, ends with /)
# Returns 0 (true) if found, 1 if not found or no manifest.
_skill_in_old_manifest() {
    local _look="$1"
    [ -f "$MANIFEST_FILE" ] || return 1
    # Dir skills pass ".agents/skills/<name>/" (trailing slash = safe prefix match).
    # Flat skills pass ".agent/skills/<name>" (NO slash) and must match the rel
    # path EXACTLY — an unbounded prefix would let a user-created flat skill
    # named as a strict prefix of a manifested one (e.g. "red-team" vs
    # "red-team-adversarial") be falsely accused as retired-upstream.
    awk -v p="$_look" '
        /^(core|scaffold|wrapper) / {
            n = split($0, a, " ")
            rel = a[2]
            if (p ~ /\/$/) { if (index(rel, p) == 1) { found=1; exit } }
            else            { if (rel == p)           { found=1; exit } }
        }
        END { exit (found ? 0 : 1) }
    ' "$MANIFEST_FILE"
}

# Scan target .agent/skills/ (flat metadata files)
for _tsf in "$TARGET/.agent/skills"/*; do
    [ -f "$_tsf" ] || continue
    _tname="${_tsf##*/}"
    [ "$_tname" = ".gitkeep" ] && continue
    # custom-* namespace: silent
    case "$_tname" in custom-*) continue ;; esac
    # Check if this name is still in the framework
    _found=false
    for _fw in $_framework_flat_skills; do
        [ "$_tname" = "$_fw" ] && _found=true && break
    done
    if ! $_found; then
        # Determine if this was ever framework-managed (present in OLD manifest)
        if _skill_in_old_manifest ".agent/skills/$_tname"; then
            echo "  [STALE SKILL] .agent/skills/$_tname — retired upstream; delete it, or rename to custom-$_tname to keep"
            _stale_count=$((_stale_count + 1))
        else
            # User-created: never in manifest — collect for aggregated note
            _user_skill_names="${_user_skill_names:+$_user_skill_names, }$_tname"
        fi
    fi
done

# Scan target .agents/skills/ (directory-based skills)
for _tsd in "$TARGET/.agents/skills"/*/; do
    [ -d "$_tsd" ] || continue
    _tdname="${_tsd%/}"; _tdname="${_tdname##*/}"
    [ "$_tdname" = ".gitkeep" ] && continue
    # custom-* namespace: silent
    case "$_tdname" in custom-*) continue ;; esac
    # Check if this name is still in the framework
    _found=false
    for _fw in $_framework_dir_skills; do
        [ "$_tdname" = "$_fw" ] && _found=true && break
    done
    if ! $_found; then
        # Determine if this was ever framework-managed (present in OLD manifest)
        if _skill_in_old_manifest ".agents/skills/$_tdname/"; then
            echo "  [STALE SKILL] .agents/skills/$_tdname — retired upstream; delete it, or rename to custom-$_tdname to keep"
            _stale_count=$((_stale_count + 1))
        else
            # User-created: never in manifest — collect for aggregated note
            _user_skill_names="${_user_skill_names:+$_user_skill_names, }$_tdname"
        fi
    fi
done

if [ "$_stale_count" -gt 0 ]; then
    echo ""
    echo "  ⚠ $_stale_count stale skill(s) detected. These were removed from the framework"
    echo "    but remain in your project. Review and delete them, or prefix with 'custom-' to keep."
fi

if [ -n "$_user_skill_names" ]; then
    # Dedupe (a skill present in both flat and dir form would otherwise list twice)
    _user_skill_names="$(printf '%s' "$_user_skill_names" | tr ',' '\n' | sed 's/^ *//' | sort -u | tr '\n' ',' | sed 's/,$//; s/,/, /g')"
    # Count names by counting commas+1 (names are comma-space separated)
    _user_skill_count=1
    _tmp_names="$_user_skill_names"
    while [ "${_tmp_names#*,}" != "$_tmp_names" ]; do
        _user_skill_count=$((_user_skill_count + 1))
        _tmp_names="${_tmp_names#*,}"
    done
    echo "  Note: $_user_skill_count local skill(s) not framework-managed (left as-is): $_user_skill_names"
    echo "    — rename to custom-<name> to mark project-owned, or delete if leftover."
fi

# ============================================================
# Write new manifest
# ============================================================

# --- Resolve source_repo for manifest ---
MANIFEST_SOURCE_REPO="${ACX_SOURCE:-}"
if [ -z "$MANIFEST_SOURCE_REPO" ]; then
    # Try to detect from git remote
    if command -v git >/dev/null 2>&1 && [ -e "$REPO_ROOT/.git" ]; then
        MANIFEST_SOURCE_REPO="$(git -C "$REPO_ROOT" remote get-url origin 2>/dev/null || echo "")"
    fi
fi

{
    echo "# Agentic OS Deploy Manifest"
    echo "# DO NOT EDIT — regenerated on each deploy"
    echo "version: ${ACX_VERSION}"
    echo "source_commit: ${SOURCE_COMMIT}"
    echo "deployed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date +%Y-%m-%dT%H:%M:%S%z)"
    if [ -n "$MANIFEST_SOURCE_REPO" ]; then
        echo "source_repo: ${MANIFEST_SOURCE_REPO}"
    fi
    echo "---"
    sort -k2 "$DEPLOYED_FILES_TMP"
} > "$MANIFEST_FILE.tmp"
mv "$MANIFEST_FILE.tmp" "$MANIFEST_FILE"

# ============================================================
# Summary
# ============================================================

TOTAL_DEPLOYED="$(grep -c 'sha256:' "$DEPLOYED_FILES_TMP" 2>/dev/null || echo 0)"
echo ""
echo "Agentic OS v${ACX_VERSION} (${SOURCE_COMMIT}) deployed successfully!"
echo ""
if $IS_UPDATE; then
    if [ "$COUNT_CORE_OVERWRITTEN" -gt 0 ]; then
        echo "Summary: ${COUNT_UPDATED} updated (${COUNT_CORE_OVERWRITTEN} locally-modified core force-updated) / ${COUNT_SKIPPED} skipped / ${COUNT_NEW} new / ${COUNT_REMOVED} removed"
    else
        echo "Summary: ${COUNT_UPDATED} updated / ${COUNT_SKIPPED} skipped / ${COUNT_NEW} new / ${COUNT_REMOVED} removed"
    fi
else
    echo "Installed ${TOTAL_DEPLOYED} files."
fi
if [ "$COUNT_SKIPPED" -gt 0 ]; then
    echo ""
    echo "⚠ Skipped files detected — your existing files were preserved."
    echo "  New versions are saved as *.acx-incoming sidecars."
    echo ""
    echo "  → Manual merge:  diff each pair, keep your content + adopt framework updates, then re-run deploy."
    echo "  → AI-assisted:   ask your AI agent — \"merge each *.acx-incoming into its target, preserving project-specific content and adopting framework updates, then delete the sidecars\""
fi
if [ "$COUNT_CORE_OVERWRITTEN" -gt 0 ]; then
    echo ""
    echo "⚠ ${COUNT_CORE_OVERWRITTEN} locally-modified core file(s) were force-updated (ADR-005)."
    echo "  Your previous versions were backed up as *.acx-local sidecars."
    echo "  Core files are framework-authoritative — re-apply needed tweaks via"
    echo "  AGENTS.override.md (governance) or custom-* skills, not by editing core in place."
fi
echo ""
echo "Platform Entry Points Ready:"
echo "   .antigravity/rules.md  -> Google Antigravity"
echo "   codex/rules/           -> Codex Web/App"
echo "   CLAUDE.md              -> Claude (manual entry)"
echo "   GEMINI.md              -> Gemini (manual entry)"
echo "   AGENTS.md              -> Cross-platform entry"
echo "   .agentcortex/bin/      -> Canonical Agentic OS implementations"
echo ""
echo "Git:"
echo "   Framework files are git-tracked (available in worktrees and branches)."
echo "   Only work logs and private state are gitignored."
echo "   .agentcortex-manifest tracks deployed files — commit this to your repo."
echo ""
echo "Next steps:"
echo "   1. Validate the installation (optional — Python is NOT required):"
echo "      .agentcortex/bin/validate.sh              # full validation (uses Python if available)"
echo "      .agentcortex/bin/validate.sh --no-python  # lightweight, text-only checks"
echo "   2. Stage framework files for git tracking:"
echo "      git add .agentcortex-manifest AGENTS.md CLAUDE.md GEMINI.md .agent/ .agents/ .agentcortex/ .antigravity/ .codex/ codex/ docs/ installers/"
echo "      # Also add if present: .claude/ .github/"
echo "   3. Tell AI: 'Please run /bootstrap' to start"
echo "   4. Agentic OS reference docs are under .agentcortex/docs/"
echo ""

# Python advisory — framework runs without Python, but guard_context_write.py
# (SSoT optimistic locking) is Python-only; absent Python the AI falls back to
# direct writes. Single-session safe; multi-session loses lock protection.
if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
    echo "Note: Python not on PATH — SSoT multi-session locking disabled (single-session OK). Install Python 3.8+ for full safety."
    echo ""
fi
