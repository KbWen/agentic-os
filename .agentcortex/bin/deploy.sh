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

# --- Argument parsing ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --source) ACX_SOURCE="$2"; shift 2 ;;
        --source=*) ACX_SOURCE="${1#--source=}"; shift ;;
        *) TARGET="$1"; shift ;;
    esac
done
TARGET="${TARGET:-.}"

MANIFEST_FILE="$TARGET/.agentcortex-manifest"
ACX_VERSION="5.4.0"

# --- Counters ---
COUNT_UPDATED=0
COUNT_SKIPPED=0
COUNT_NEW=0
COUNT_REMOVED=0

# --- SHA256 utility (cross-platform) ---
compute_sha256() {
    local file="$1"
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$file" | cut -d' ' -f1
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$file" | cut -d' ' -f1
    else
        # fallback: use openssl if available
        openssl dgst -sha256 "$file" | awk '{print $NF}'
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
        deploy_brain.sh|deploy_brain.ps1|deploy_brain.cmd) echo "wrapper" ;;

        # scaffold — created once, user expected to modify
        .agentcortex/context/current_state.md) echo "scaffold" ;;
        .agentcortex/adr/*) echo "scaffold" ;;

        # core — everything else is framework, always overwrite
        *) echo "core" ;;
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

# --- Smart deploy a single file ---
# deploy_file <source_abs> <target_rel> [chmod]
deploy_file() {
    local src="$1"
    local rel="$2"
    local do_chmod="${3:-}"
    local dst="$TARGET/$rel"
    local tier
    tier="$(get_tier "$rel")"

    [ -f "$src" ] || return 0

    local src_hash
    src_hash="$(compute_sha256 "$src")"

    local is_update=false
    [ -f "$MANIFEST_FILE" ] && is_update=true

    if [ -f "$dst" ] && $is_update; then
        # Update mode — file exists in target
        local old_manifest_hash
        old_manifest_hash="$(manifest_lookup_hash "$rel")"

        if [ "$tier" = "core" ]; then
            # Core: always overwrite
            cp ${CP_FLAG:+"$CP_FLAG"} "$src" "$dst"
            [ -n "$do_chmod" ] && chmod +x "$dst"
            COUNT_UPDATED=$((COUNT_UPDATED + 1))
        else
            # Scaffold/wrapper: check if user modified
            if [ -z "$old_manifest_hash" ]; then
                # File exists in target but not in old manifest — treat as new
                cp ${CP_FLAG:+"$CP_FLAG"} "$src" "$dst"
                [ -n "$do_chmod" ] && chmod +x "$dst"
                COUNT_NEW=$((COUNT_NEW + 1))
            else
                local dst_hash
                dst_hash="$(compute_sha256 "$dst")"
                if [ "$dst_hash" = "$old_manifest_hash" ]; then
                    # User didn't modify — safe to update
                    cp ${CP_FLAG:+"$CP_FLAG"} "$src" "$dst"
                    [ -n "$do_chmod" ] && chmod +x "$dst"
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
    elif [ -f "$dst" ] && ! $is_update; then
        # Fresh install but file already exists (pre-manifest era)
        cp ${CP_FLAG:+"$CP_FLAG"} "$src" "$dst"
        [ -n "$do_chmod" ] && chmod +x "$dst"
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

# ============================================================
# MAIN
# ============================================================

DEPLOYED_FILES_TMP="$(mktemp)"
trap 'rm -f "$DEPLOYED_FILES_TMP" "${TMP_STRIPPED_GITIGNORE:-}" "${TMP_NORMALIZED_GITIGNORE:-}" "${GITIGNORE:-}.tmp"' EXIT

SOURCE_COMMIT="$(get_source_commit)"
IS_UPDATE=false

if [ -f "$MANIFEST_FILE" ]; then
    IS_UPDATE=true
    echo "Updating AgentCortex v${ACX_VERSION} (${SOURCE_COMMIT}) in $TARGET..."
    clean_acx_incoming
else
    echo "Installing AgentCortex v${ACX_VERSION} (${SOURCE_COMMIT}) to $TARGET..."
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

# Migration safety: only trigger if we find AgentCortex-specific markers.
# A bare agentcortex/ dir is unambiguously ours. But docs/adr/ or docs/specs/
# could belong to the downstream project. We only migrate docs/ subdirs if
# there is ALSO an old agentcortex/ dir or a prior .agentcortex-manifest
# (proving this repo had a previous AgentCortex install).
_acx_legacy_confirmed=false
if [ -d "$TARGET/agentcortex" ] || [ -f "$TARGET/.agentcortex-manifest" ]; then
    _acx_legacy_confirmed=true
fi

if $_acx_legacy_confirmed || [ -f "$TARGET/tools/validate.sh" ] || \
   [ -f "$TARGET/tools/validate.ps1" ] || [ -f "$TARGET/tools/validate.cmd" ]; then
    echo ""
    echo "Migrating from legacy paths..."

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

        for adr_file in "$TARGET/.agentcortex/adr"/*.md; do
            [ -f "$adr_file" ] || continue
            bname="$(basename "$adr_file")"
            # ADR-001-* is the framework ADR; everything else is project-owned
            case "$bname" in ADR-001-*) continue ;; esac
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

    echo "  Migration complete."
    echo ""
fi

# --- Create directory structure ---
mkdir -p "$TARGET/.agent/rules"
mkdir -p "$TARGET/.agent/workflows"
mkdir -p "$TARGET/.agent/skills"
mkdir -p "$TARGET/.antigravity"
mkdir -p "$TARGET/.agents/skills"
mkdir -p "$TARGET/.claude/commands"
mkdir -p "$TARGET/.codex"
mkdir -p "$TARGET/codex/rules"
mkdir -p "$TARGET/.github/ISSUE_TEMPLATE"
mkdir -p "$TARGET/.agentcortex/bin"
mkdir -p "$TARGET/.agentcortex/metadata"
mkdir -p "$TARGET/.agentcortex/tools"
mkdir -p "$TARGET/.agentcortex/docs/guides"
mkdir -p "$TARGET/.agentcortex/context/work"
mkdir -p "$TARGET/.agentcortex/context/review"
mkdir -p "$TARGET/.agentcortex/context/archive"
mkdir -p "$TARGET/.agentcortex/adr"
mkdir -p "$TARGET/.agentcortex/specs"
mkdir -p "$TARGET/docs/specs"
mkdir -p "$TARGET/docs/adr"

# --- Deploy: root governance files (core) ---
deploy_file "$REPO_ROOT/AGENTS.md" "AGENTS.md"
deploy_file "$REPO_ROOT/CLAUDE.md" "CLAUDE.md"

# --- Deploy: wrapper scripts ---
deploy_file "$REPO_ROOT/deploy_brain.sh" "deploy_brain.sh" "+x"
deploy_file "$REPO_ROOT/deploy_brain.ps1" "deploy_brain.ps1"
deploy_file "$REPO_ROOT/deploy_brain.cmd" "deploy_brain.cmd"

# --- Deploy: platform rules (core) ---
deploy_file "$REPO_ROOT/.antigravity/rules.md" ".antigravity/rules.md"
deploy_file "$REPO_ROOT/codex/rules/default.rules" "codex/rules/default.rules"
# --- Deploy: .agent/rules (core) ---
for f in "$REPO_ROOT"/.agent/rules/*.md; do
    [ -f "$f" ] || continue
    deploy_file "$f" ".agent/rules/$(basename "$f")"
done

# --- Deploy: .agent/config.yaml (core) ---
deploy_file "$REPO_ROOT/.agent/config.yaml" ".agent/config.yaml"

# --- Deploy: workflows (core) ---
for f in "$REPO_ROOT"/.agent/workflows/*.md; do
    [ -f "$f" ] || continue
    deploy_file "$f" ".agent/workflows/$(basename "$f")"
done

# --- Deploy: skills (core) ---
# .agent/skills/ has flat metadata files; .agents/skills/ has directory-based skills.
# Deploy each to its own target — do NOT mirror across since structures differ.

# Flat skill metadata files → .agent/skills/
for skill_file in "$REPO_ROOT"/.agent/skills/*; do
    [ -f "$skill_file" ] || continue
    bname="$(basename "$skill_file")"
    [ "$bname" = ".gitkeep" ] && continue
    deploy_file "$skill_file" ".agent/skills/$bname"
done

# Directory-based skills → .agents/skills/
if [ -d "$REPO_ROOT/.agents/skills" ]; then
    for skill_dir in "$REPO_ROOT/.agents/skills"/*/; do
        [ -d "$skill_dir" ] || continue
        skill_name="$(basename "$skill_dir")"
        # Guard: if a legacy flat file exists where a directory is needed, remove it
        if [ -f "$TARGET/.agents/skills/$skill_name" ]; then
            rm -f "$TARGET/.agents/skills/$skill_name"
            echo "  [MIGRATE] removed flat file .agents/skills/$skill_name (now a directory)"
        fi
        mkdir -p "$TARGET/.agents/skills/$skill_name"
        for skill_file in "$skill_dir"*; do
            [ -f "$skill_file" ] || continue
            local_name="$(basename "$skill_file")"
            deploy_file "$skill_file" ".agents/skills/$skill_name/$local_name"
        done
    done
fi

touch "$TARGET/.agent/skills/.gitkeep"
touch "$TARGET/.agents/skills/.gitkeep"

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
  check_command_sync.py
  check_text_integrity.py
  check_text_integrity.ps1
  text_integrity_baseline.txt
  sync_skills.sh
)
for bname in "${runtime_tools[@]}"; do
    f="$REPO_ROOT/.agentcortex/tools/$bname"
    [ -f "$f" ] || continue
    chmod_flag=""
    case "$bname" in *.sh) chmod_flag="+x" ;; esac
    deploy_file "$f" ".agentcortex/tools/$bname" "$chmod_flag"
done

# --- Deploy: .agentcortex/context/current_state.md (scaffold) ---
deploy_file "$REPO_ROOT/.agentcortex/context/current_state.md" ".agentcortex/context/current_state.md"

# --- Deploy: .agentcortex/adr (scaffold) ---
for f in "$REPO_ROOT"/.agentcortex/adr/*.md; do
    [ -f "$f" ] || continue
    deploy_file "$f" ".agentcortex/adr/$(basename "$f")"
done

# --- Deploy: reference docs to .agentcortex/docs/ (core) ---
for f in \
  "$REPO_ROOT"/README*.md \
  "$REPO_ROOT"/AGENT_MODEL_GUIDE*.md \
  "$REPO_ROOT"/.agentcortex/docs/AGENT_PHILOSOPHY*.md \
  "$REPO_ROOT"/.agentcortex/docs/TESTING_PROTOCOL*.md \
  "$REPO_ROOT"/.agentcortex/docs/CODEX_PLATFORM_GUIDE*.md \
  "$REPO_ROOT"/.agentcortex/docs/PROJECT_EXAMPLES*.md \
  "$REPO_ROOT"/.agentcortex/docs/PROJECT_OVERVIEW*.md \
  "$REPO_ROOT"/.agentcortex/docs/NONLINEAR_SCENARIOS*.md \
  "$REPO_ROOT"/.agentcortex/docs/CLAUDE_PLATFORM_GUIDE.md; do
  [ -f "$f" ] || continue
  deploy_file "$f" ".agentcortex/docs/$(basename "$f")"
done
for f in "$REPO_ROOT"/.agentcortex/docs/guides/*.md; do
    [ -f "$f" ] || continue
    deploy_file "$f" ".agentcortex/docs/guides/$(basename "$f")"
done

# --- Deploy: .claude/commands (core) ---
if [ -d "$REPO_ROOT/.claude/commands" ]; then
    for f in "$REPO_ROOT"/.claude/commands/*; do
        [ -f "$f" ] || continue
        deploy_file "$f" ".claude/commands/$(basename "$f")"
    done
fi

# --- Deploy: .codex/INSTALL.md (core) ---
deploy_file "$REPO_ROOT/.codex/INSTALL.md" ".codex/INSTALL.md"

# --- Deploy: .github/ templates (core) ---
for f in "$REPO_ROOT"/.github/ISSUE_TEMPLATE/*.md; do
    [ -f "$f" ] || continue
    deploy_file "$f" ".github/ISSUE_TEMPLATE/$(basename "$f")"
done
deploy_file "$REPO_ROOT/.github/PULL_REQUEST_TEMPLATE.md" ".github/PULL_REQUEST_TEMPLATE.md"

# ============================================================
# .gitignore management (special — block-managed, not file-level)
# ============================================================

GITIGNORE="$TARGET/.gitignore"
DOWNSTREAM_IGNORE_START="# AgentCortex Template - Downstream Ignore Defaults"
LEGACY_IGNORE_START="# AI Brain OS - Agent System & Local Context"

write_downstream_ignore_block() {
    cat <<'EOT'
# AgentCortex Template - Downstream Ignore Defaults

# Runtime State (work logs are session-local; private is never committed)
.agentcortex/context/work/*.md
!.agentcortex/context/work/.gitkeep
.agentcortex/context/.guard_receipt.json
.agentcortex/context/.guard_locks/
.agentcortex/context/private/
.agent/private/

# Deploy Artifacts
.agentcortex-src/
*.acx-incoming

# Third-party AI Tool Local State
.openrouter/
.claude-chat/
.cursor/
.antigravity/scratch/

# End AgentCortex Template - Downstream Ignore Defaults
EOT
}

strip_managed_ignore_blocks() {
    local source_file="$1"
    local output_file="$2"

    awk '
    BEGIN {
        # Current managed entries
        managed[".agentcortex/context/work/*.md"] = 1
        managed["!.agentcortex/context/work/.gitkeep"] = 1
        managed[".agentcortex/context/.guard_receipt.json"] = 1
        managed[".agentcortex/context/.guard_locks/"] = 1
        managed[".agentcortex/context/private/"] = 1
        managed[".agent/private/"] = 1
        managed[".agentcortex-src/"] = 1
        managed["*.acx-incoming"] = 1
        managed[".openrouter/"] = 1
        managed[".claude-chat/"] = 1
        managed[".cursor/"] = 1
        managed[".antigravity/scratch/"] = 1
        # Legacy paths from older versions (strip during upgrade)
        managed["AGENTS.md"] = 1
        managed["CLAUDE.md"] = 1
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
        managed[".github/ISSUE_TEMPLATE/agent_issue.md"] = 1
        managed[".github/PULL_REQUEST_TEMPLATE.md"] = 1
        managed["docs/adr/"] = 1
        managed["docs/context/work/*.md"] = 1
        managed["!docs/context/work/.gitkeep"] = 1
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

    /^# AgentCortex Template - Downstream Ignore Defaults$/ { skip = 1; next }
    /^# AI Brain OS - Agent System & Local Context$/ { skip = 1; next }
    /^# End AgentCortex Template - Downstream Ignore Defaults$/ { skip = 0; next }

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
    echo "Adding AgentCortex downstream ignore defaults to .gitignore..."
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
    echo "# AgentCortex Deploy Manifest"
    echo "# DO NOT EDIT — regenerated on each deploy"
    echo "version: ${ACX_VERSION}"
    echo "source_commit: ${SOURCE_COMMIT}"
    echo "deployed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date +%Y-%m-%dT%H:%M:%S%z)"
    if [ -n "$MANIFEST_SOURCE_REPO" ]; then
        echo "source_repo: ${MANIFEST_SOURCE_REPO}"
    fi
    echo "---"
    sort -k2 "$DEPLOYED_FILES_TMP"
} > "$MANIFEST_FILE"

# ============================================================
# Summary
# ============================================================

TOTAL_DEPLOYED="$(grep -c 'sha256:' "$DEPLOYED_FILES_TMP" 2>/dev/null || echo 0)"
echo ""
echo "AgentCortex v${ACX_VERSION} (${SOURCE_COMMIT}) deployed successfully!"
echo ""
if $IS_UPDATE; then
    echo "Summary: ${COUNT_UPDATED} updated / ${COUNT_SKIPPED} skipped / ${COUNT_NEW} new / ${COUNT_REMOVED} removed"
    if [ "$COUNT_SKIPPED" -gt 0 ]; then
        echo ""
        echo "Skipped files have .acx-incoming sidecars with the new version."
        echo "Review and merge manually, then re-run deploy to update the manifest."
    fi
else
    echo "Installed ${TOTAL_DEPLOYED} files."
fi
echo ""
echo "Platform Entry Points Ready:"
echo "   .antigravity/rules.md  -> Google Antigravity"
echo "   codex/rules/           -> Codex Web/App"
echo "   CLAUDE.md              -> Claude (manual entry)"
echo "   AGENTS.md              -> Cross-platform entry"
echo "   .agentcortex/bin/      -> Canonical AgentCortex implementations"
echo ""
echo "Git:"
echo "   Framework files are git-tracked (available in worktrees and branches)."
echo "   Only work logs and private state are gitignored."
echo "   PR review mirrors under .agentcortex/context/review/ are optional; upstream repos may track them, downstream repos can opt in."
echo "   .agentcortex-manifest tracks deployed files — commit this to your repo."
echo ""
echo "Next steps:"
echo "   1. Stage framework files for git tracking:"
echo "      git add .agentcortex-manifest AGENTS.md CLAUDE.md .agent/ .agents/ .agentcortex/ .claude/ .codex/ codex/ .antigravity/ .github/"
echo "   2. Tell AI: 'Please run /bootstrap' to start"
echo "   3. AgentCortex reference docs are under .agentcortex/docs/"
echo ""
