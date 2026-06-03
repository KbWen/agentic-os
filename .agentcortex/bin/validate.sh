#!/usr/bin/env bash
set -euo pipefail

# --- CLI flags ---
ACX_NO_PYTHON=0
LIST_CHECKS_ONLY=0
for _arg in "$@"; do
  case "$_arg" in
    --no-python) ACX_NO_PYTHON=1 ;;
    --list-checks|-l) LIST_CHECKS_ONLY=1 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLATFORM_DOC="$ROOT/.agentcortex/docs/CODEX_PLATFORM_GUIDE.md"
CLAUDE_PLATFORM_DOC="$ROOT/.agentcortex/docs/CLAUDE_PLATFORM_GUIDE.md"
EXAMPLES_DOC="$ROOT/.agentcortex/docs/PROJECT_EXAMPLES.md"
PROJECT_AGENTS_FILE="$ROOT/AGENTS.md"
PROJECT_CLAUDE_FILE="$ROOT/CLAUDE.md"
WORKFLOWS_DIR="$ROOT/.agent/workflows"
CLAUDE_COMMANDS_DIR="$ROOT/.claude/commands"
CODEX_INSTALL="$ROOT/.codex/INSTALL.md"
CODEX_RULES="$ROOT/.codex/rules/default.rules"
CANONICAL_DEPLOY_SH="$ROOT/.agentcortex/bin/deploy.sh"

# Source-repo detection (must run before required_files array is built).
# Source repo has canonical deploy but no .agentcortex-manifest.
# Both source and downstream repos keep deploy_brain.* under installers/.
IS_SOURCE_REPO=0
if [[ -f "$CANONICAL_DEPLOY_SH" ]] && [[ ! -f "$ROOT/.agentcortex-manifest" ]]; then
  IS_SOURCE_REPO=1
fi

ROOT_DEPLOY_SH="$ROOT/installers/deploy_brain.sh"
ROOT_DEPLOY_PS1="$ROOT/installers/deploy_brain.ps1"
ROOT_DEPLOY_CMD="$ROOT/installers/deploy_brain.cmd"
CANONICAL_DEPLOY_PS1="$ROOT/.agentcortex/bin/deploy.ps1"
CANONICAL_VALIDATE_SH="$ROOT/.agentcortex/bin/validate.sh"
CANONICAL_VALIDATE_PS1="$ROOT/.agentcortex/bin/validate.ps1"
TEXT_INTEGRITY_CHECK_PY="$ROOT/.agentcortex/tools/check_text_integrity.py"
TEXT_INTEGRITY_CHECK_PS1="$ROOT/.agentcortex/tools/check_text_integrity.ps1"
TEXT_INTEGRITY_BASELINE="$ROOT/.agentcortex/tools/text_integrity_baseline.txt"
TRIGGER_METADATA_VALIDATOR="$ROOT/.agentcortex/tools/validate_trigger_metadata.py"
TRIGGER_COMPACT_INDEX_GENERATOR="$ROOT/.agentcortex/tools/generate_compact_index.py"
GUARD_CONTEXT_WRITE="$ROOT/.agentcortex/tools/guard_context_write.py"
GUARDED_WRITES_LINT="$ROOT/.agentcortex/tools/lint_governed_writes.py"
LIFECYCLE_FRONTMATTER_CHECK="$ROOT/.agentcortex/tools/check_lifecycle_frontmatter.py"
AUDIT_CHAIN_CHECK="$ROOT/.agentcortex/tools/check_audit_chain.py"
ARCHIVE_INDEX_JSONL="$ROOT/.agentcortex/context/archive/INDEX.jsonl"
LESSON_CHAIN_CHECK="$ROOT/.agentcortex/tools/check_lesson_chain.py"
SSOT_CURRENT_STATE="$ROOT/.agentcortex/context/current_state.md"
COMMAND_SYNC_CHECK="$ROOT/.agentcortex/tools/check_command_sync.py"
TRIGGER_REGISTRY="$ROOT/.agentcortex/metadata/trigger-registry.yaml"
TRIGGER_COMPACT_INDEX="$ROOT/.agentcortex/metadata/trigger-compact-index.json"
LIFECYCLE_SCENARIOS="$ROOT/.agentcortex/metadata/lifecycle-scenarios.json"
SKILL_CONFLICT_MATRIX="$ROOT/.agent/rules/skill_conflict_matrix.md"
AGENT_CONFIG_YAML="$ROOT/.agent/config.yaml"
OPTIONAL_GUARD_HOOK="$ROOT/.githooks/pre-commit.guard-ssot.sample"

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

record_result() {
  local level="$1"
  shift
  local message="$*"
  printf '[%s] %s\n' "$level" "$message"
  case "$level" in
    PASS) PASS_COUNT=$((PASS_COUNT + 1)) ;;
    WARN) WARN_COUNT=$((WARN_COUNT + 1)) ;;
    FAIL) FAIL_COUNT=$((FAIL_COUNT + 1)) ;;
    SKIP) SKIP_COUNT=$((SKIP_COUNT + 1)) ;;
  esac
}

print_indented_output() {
  local text="${1:-}"
  [[ -n "$text" ]] || return 0
  while IFS= read -r line; do
    [[ -n "$line" ]] || continue
    printf '  %s\n' "$line"
  done <<< "$text"
}

check_file_group() {
  local label="$1"
  shift
  local missing=()
  local f
  for f in "$@"; do
    [[ -f "$f" ]] || missing+=("$f")
  done
  if ((${#missing[@]})); then
    record_result FAIL "$label"
    for f in "${missing[@]}"; do
      printf '  missing: %s\n' "$f"
    done
    printf '  fix: re-run deploy (installers/deploy_brain.sh) to restore missing framework files\n'
  else
    record_result PASS "$label"
  fi
}

check_optional_file_group() {
  local label="$1"
  shift
  local missing=()
  local f
  for f in "$@"; do
    [[ -f "$f" ]] || missing+=("$f")
  done
  if ((${#missing[@]})); then
    record_result WARN "$label"
    for f in "${missing[@]}"; do
      printf '  missing (optional): %s\n' "$f"
    done
  else
    record_result PASS "$label"
  fi
}

check_dir_group() {
  local label="$1"
  shift
  local missing=()
  local d
  for d in "$@"; do
    [[ -d "$d" ]] || missing+=("$d")
  done
  if ((${#missing[@]})); then
    record_result FAIL "$label"
    for d in "${missing[@]}"; do
      printf '  missing: %s\n' "$d"
    done
    printf '  fix: re-run deploy (installers/deploy_brain.sh) to restore missing framework directories\n'
  else
    record_result PASS "$label"
  fi
}

check_contains_literal() {
  local file="$1"
  local pattern="$2"
  local success="$3"
  local failure="$4"
  if grep -F -q -- "$pattern" "$file"; then
    record_result PASS "$success"
  else
    record_result FAIL "$failure"
  fi
}

check_contains_regex() {
  local file="$1"
  local pattern="$2"
  local success="$3"
  local failure="$4"
  if grep -q -- "$pattern" "$file"; then
    record_result PASS "$success"
  else
    record_result FAIL "$failure"
  fi
}

run_python_check() {
  local label="$1"
  local missing_python_level="$2"
  local script="$3"
  shift 3

  if [[ ! -f "$script" ]]; then
    record_result SKIP "$label -- tool not present"
    return 0
  fi

  if [[ -z "${PYTHON_BIN:-}" ]]; then
    if [[ "$ACX_NO_PYTHON" -eq 1 ]]; then
      record_result SKIP "$label -- python checks disabled (--no-python)"
    else
      record_result WARN "$label -- python unavailable (install Python 3.9+ for full validation)"
    fi
    return 0
  fi

  local output
  local status=0
  output="$("$PYTHON_BIN" "$script" "$@" 2>&1)" || status=$?
  if [[ $status -eq 0 ]]; then
    record_result PASS "$label"
  else
    record_result FAIL "$label"
  fi
  print_indented_output "$output"
}

required_files=(
  "$WORKFLOWS_DIR/hotfix.md"
  "$WORKFLOWS_DIR/worktree-first.md"
  "$WORKFLOWS_DIR/govern-docs.md"
  "$WORKFLOWS_DIR/handoff.md"
  "$WORKFLOWS_DIR/bootstrap.md"
  "$WORKFLOWS_DIR/plan.md"
  "$WORKFLOWS_DIR/implement.md"
  "$WORKFLOWS_DIR/review.md"
  "$WORKFLOWS_DIR/help.md"
  "$WORKFLOWS_DIR/test-skeleton.md"
  "$WORKFLOWS_DIR/commands.md"
  "$WORKFLOWS_DIR/routing.md"
  "$WORKFLOWS_DIR/test.md"
  "$WORKFLOWS_DIR/ship.md"
  "$WORKFLOWS_DIR/decide.md"
  "$WORKFLOWS_DIR/test-classify.md"
  "$WORKFLOWS_DIR/spec-intake.md"
  "$WORKFLOWS_DIR/adr.md"
  "$WORKFLOWS_DIR/audit.md"
  "$WORKFLOWS_DIR/brainstorm.md"
  "$WORKFLOWS_DIR/research.md"
  "$WORKFLOWS_DIR/retro.md"
  "$WORKFLOWS_DIR/spec.md"
  "$WORKFLOWS_DIR/sync-docs.md"
  "$SKILL_CONFLICT_MATRIX"
  "$AGENT_CONFIG_YAML"
  "$PLATFORM_DOC"
  "$CLAUDE_PLATFORM_DOC"
  "$EXAMPLES_DOC"
  "$PROJECT_AGENTS_FILE"
  "$PROJECT_CLAUDE_FILE"
  "$ROOT_DEPLOY_SH"
  "$ROOT_DEPLOY_PS1"
  "$ROOT_DEPLOY_CMD"
  "$CANONICAL_DEPLOY_SH"
  "$CANONICAL_DEPLOY_PS1"
  "$CANONICAL_VALIDATE_SH"
  "$CANONICAL_VALIDATE_PS1"
  "$COMMAND_SYNC_CHECK"
  "$TEXT_INTEGRITY_CHECK_PY"
  "$TEXT_INTEGRITY_CHECK_PS1"
  "$TEXT_INTEGRITY_BASELINE"
)

claude_required_files=(
  "$CLAUDE_COMMANDS_DIR/spec-intake.md"
  "$CLAUDE_COMMANDS_DIR/bootstrap.md"
  "$CLAUDE_COMMANDS_DIR/plan.md"
  "$CLAUDE_COMMANDS_DIR/implement.md"
  "$CLAUDE_COMMANDS_DIR/review.md"
  "$CLAUDE_COMMANDS_DIR/test.md"
  "$CLAUDE_COMMANDS_DIR/handoff.md"
  "$CLAUDE_COMMANDS_DIR/ship.md"
  "$CLAUDE_COMMANDS_DIR/decide.md"
  "$CLAUDE_COMMANDS_DIR/test-classify.md"
  "$CLAUDE_COMMANDS_DIR/claude-cli.md"
  "$ROOT/.claude/agents/acx-implementer.md"
  "$ROOT/.claude/agents/acx-reviewer.md"
  "$ROOT/.claude/agents/acx-tester.md"
  "$ROOT/.claude/agents/acx-handoff.md"
  "$ROOT/.claude/agents/acx-shipper.md"
)

required_dirs=(
  "$WORKFLOWS_DIR"
  "$CLAUDE_COMMANDS_DIR"
  "$ROOT/.agents/skills"
  "$ROOT/.agent/skills"
)

if [[ "$ACX_NO_PYTHON" -eq 1 ]]; then
  PYTHON_BIN=
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
else
  PYTHON_BIN=
fi

if [[ "$LIST_CHECKS_ONLY" -eq 1 ]]; then
  grep -oE 'record_result (PASS|FAIL|WARN|SKIP) "[^"]*"' "$0" \
    | sed 's/record_result [A-Z]* "//; s/"$//' \
    | grep -v '^\$' \
    | sort -u
  exit 0
fi

check_file_group "required framework files present" "${required_files[@]}"

check_optional_file_group "optional module workflow files present" \
  "$WORKFLOWS_DIR/ask-openrouter.md" \
  "$WORKFLOWS_DIR/codex-cli.md" \
  "$WORKFLOWS_DIR/claude-cli.md"

deprecated_files=("$WORKFLOWS_DIR/new-feature.md" "$WORKFLOWS_DIR/medium-feature.md" "$WORKFLOWS_DIR/small-fix.md")
deprecated_found=()
for f in "${deprecated_files[@]}"; do
  [[ -f "$f" ]] && deprecated_found+=("$(basename "$f")")
done
if [[ ${#deprecated_found[@]} -gt 0 ]]; then
  record_result FAIL "deprecated workflow files still present (remove them): ${deprecated_found[*]}"
else
  record_result PASS "deprecated workflow files absent (new-feature, medium-feature, small-fix)"
fi

if [[ "$IS_SOURCE_REPO" -eq 1 ]]; then
  record_result SKIP "claude adapter files -- source repo (created by deploy in downstream)"
  # Adjust required_dirs to exclude .claude/commands in source repo
  source_required_dirs=(
    "$WORKFLOWS_DIR"
    "$ROOT/.agents/skills"
    "$ROOT/.agent/skills"
  )
  check_dir_group "required framework directories present" "${source_required_dirs[@]}"
else
  check_file_group "claude adapter files present" "${claude_required_files[@]}"
  check_dir_group "required framework directories present" "${required_dirs[@]}"
fi

run_python_check \
  "text integrity check" \
  FAIL \
  "$TEXT_INTEGRITY_CHECK_PY" \
  --root "$ROOT" \
  --baseline "$TEXT_INTEGRITY_BASELINE"

if [[ -f "$TRIGGER_REGISTRY" ]]; then
  if [[ -f "$TRIGGER_COMPACT_INDEX" ]]; then
    record_result PASS "metadata runtime artifacts present"
  else
    record_result FAIL "metadata runtime incomplete -- missing trigger-compact-index.json"
    echo "  fix: re-run deploy to restore metadata, or regenerate with .agentcortex/tools/generate_compact_index.py"
  fi

  if [[ -f "$TRIGGER_METADATA_VALIDATOR" ]]; then
    if [[ -f "$LIFECYCLE_SCENARIOS" ]]; then
      run_python_check "metadata deep validation" FAIL "$TRIGGER_METADATA_VALIDATOR" --root "$ROOT"
    else
      record_result FAIL "metadata deep validation unavailable -- lifecycle scenarios missing"
      echo "  fix: re-run deploy to restore .agentcortex/metadata/lifecycle-scenarios.json"
    fi
  else
    record_result SKIP "metadata deep checks -- CI-only validator not deployed (safe to ignore downstream)"
  fi

  if [[ -f "$TRIGGER_COMPACT_INDEX_GENERATOR" ]]; then
    run_python_check "compact index freshness" FAIL "$TRIGGER_COMPACT_INDEX_GENERATOR" --root "$ROOT" --check
  else
    record_result SKIP "compact index freshness -- CI-only generator not deployed (safe to ignore downstream)"
  fi
elif [[ -f "$TRIGGER_COMPACT_INDEX" ]]; then
  record_result FAIL "metadata runtime incomplete -- compact index present without trigger registry"
  echo "  fix: re-run deploy to restore .agentcortex/metadata/trigger-registry.yaml"
else
  record_result SKIP "metadata checks -- no trigger registry found (safe to ignore if not using skill metadata)"
fi

run_python_check "command sync check" FAIL "$COMMAND_SYNC_CHECK" --root "$ROOT"

# Guarded-write lint: fail CI on direct file writes against
# .agent/config.yaml §guard_policy.protected_paths. Use guard_context_write.py
# or annotate the line with `guard-exempt: <reason>`.
run_python_check "guarded-write lint (governance paths)" FAIL "$GUARDED_WRITES_LINT" --root "$ROOT"

# Governance docs MUST declare lifecycle: frontmatter
# {owner, review_cadence, review_trigger, supersedes, superseded_by}.
# Files dated before 2026-04-25 are grandfathered (WARN); newer files FAIL.
run_python_check "lifecycle frontmatter (governance docs)" FAIL "$LIFECYCLE_FRONTMATTER_CHECK" --root "$ROOT"

# Verify the hash chain on the archive INDEX.jsonl. A broken chain means an
# entry was retroactively rewritten without going through
# .agentcortex/tools/append_chain_entry.py. Capability-by-presence: file
# absent or empty → no-op (PASS). External observer for an otherwise
# honor-system rule on archive integrity.
if [[ -f "$ARCHIVE_INDEX_JSONL" ]]; then
  run_python_check "audit chain integrity (INDEX.jsonl)" FAIL "$AUDIT_CHAIN_CHECK" --path "$ARCHIVE_INDEX_JSONL" --quiet
else
  record_result SKIP "audit chain integrity -- archive INDEX.jsonl not present"
fi

# C1: git append-only WITNESS for INDEX.jsonl (ADR-003 amendment; spec
# audit-chain-tamper-evidence AC-4/5/6). The back-linked chain above cannot
# detect TAIL-TRUNCATION (deleting the most recent entries leaves a chain that
# still validates). Git is used as an EXTERNAL append-only witness: the
# INDEX.jsonl committed at the merge-base with origin/main MUST be a line-prefix
# of the working copy. merge-base (not the origin tip) avoids false FAILs on
# stale feature branches while still catching any deletion/edit of an entry that
# existed when this branch diverged. Tamper-EVIDENCE, not prevention: a truncation
# becomes a visible removed-lines diff that must survive PR review. Degrades to
# WARN (never silent PASS) when git / origin/main / baseline is unavailable.
INDEX_REL=".agentcortex/context/archive/INDEX.jsonl"
if [[ -f "$ARCHIVE_INDEX_JSONL" ]]; then
  if ! command -v git >/dev/null 2>&1 || ! git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
    record_result WARN "INDEX.jsonl append-only witness -- git unavailable or not a git repo"
  else
    # Best-effort: make origin/main available (no-op when offline / no remote).
    if ! git -C "$ROOT" rev-parse --verify -q origin/main >/dev/null 2>&1; then
      git -C "$ROOT" fetch -q --depth=1 origin main >/dev/null 2>&1 || true
    fi
    witness_base="$(git -C "$ROOT" merge-base origin/main HEAD 2>/dev/null || true)"
    if [[ -z "$witness_base" ]]; then
      record_result WARN "INDEX.jsonl append-only witness -- no merge-base with origin/main (offline, no remote, or unrelated history)"
    elif ! git -C "$ROOT" cat-file -e "$witness_base:$INDEX_REL" 2>/dev/null; then
      record_result WARN "INDEX.jsonl append-only witness -- not present at merge-base (new log surface)"
    else
      # Normalize both sides identically before comparing, so this check is
      # byte-for-byte equivalent to the validate.ps1 mirror (parity, spec AC-6):
      #   1. tr -d '\r' — the working copy may be CRLF (git autocrlf on Windows)
      #      while `git show` emits LF; an un-normalized diff false-FAILs every
      #      line. (`tr` is portable; diff --strip-trailing-cr is GNU-only.)
      #   2. grep '.' — drop blank lines, matching the PowerShell mirror's
      #      `Where-Object { $_ -ne '' }`, so a stray blank line cannot make the
      #      two validators disagree.
      witness_base_count="$(git -C "$ROOT" show "$witness_base:$INDEX_REL" | tr -d '\r' | grep -c '.' || true)"
      witness_local_count="$(tr -d '\r' < "$ARCHIVE_INDEX_JSONL" | grep -c '.' || true)"
      if [[ "$witness_local_count" -lt "$witness_base_count" ]]; then
        record_result FAIL "INDEX.jsonl append-only witness -- local has $witness_local_count entries, fewer than baseline $witness_base_count at merge-base (tail-truncation?)"
      elif ! diff -q <(git -C "$ROOT" show "$witness_base:$INDEX_REL" | tr -d '\r' | grep '.') <(tr -d '\r' < "$ARCHIVE_INDEX_JSONL" | grep '.' | head -n "$witness_base_count") >/dev/null 2>&1; then
        record_result FAIL "INDEX.jsonl append-only witness -- committed baseline is not a prefix of local (a previously-published audit entry was edited or deleted)"
      else
        record_result PASS "INDEX.jsonl append-only witness -- baseline is a prefix of local (append-only invariant holds)"
      fi
    fi
  fi
fi

# Global Lessons hash chain. Without a chain, an agent could silently delete
# an inconvenient lesson that constrains its own future behaviour. Tamper-
# evident chain on §Global Lessons closes that gap.
if [[ -f "$SSOT_CURRENT_STATE" ]]; then
  run_python_check "lesson chain integrity (Global Lessons)" FAIL "$LESSON_CHAIN_CHECK" --path "$SSOT_CURRENT_STATE" --quiet
else
  record_result SKIP "lesson chain integrity -- current_state.md not present"
fi

# Unresolved merge-conflict markers in tracked files. A squash-merge collision
# between two PRs that both edit the same section (e.g. SSoT Ship History) can
# leave conflict markers committed to a tracked file -- git's own merge blocks
# this, but GitHub squash-merge does not (current_state.md reached main this way
# on 2026-05-31; fixed in PR #130). Match only the unambiguous opening/closing
# marker forms ("<<<<<<< " / ">>>>>>> " at line start); a bare "=======" is
# deliberately NOT matched because it collides with markdown setext H2 underlines.
# The validator pair self-excludes (it contains the pattern literally). git grep
# -I skips binary; the verdict is byte-identical to the validate.ps1 mirror.
if command -v git >/dev/null 2>&1 && git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  conflict_marker_hits="$(git -C "$ROOT" grep -I -n -E '^(<<<<<<< |>>>>>>> )' -- . \
    ':(exclude).agentcortex/bin/validate.sh' \
    ':(exclude).agentcortex/bin/validate.ps1' \
    ':(exclude)tests/guard/test_conflict_markers.py' 2>/dev/null || true)"
  if [[ -n "$conflict_marker_hits" ]]; then
    record_result FAIL "unresolved merge-conflict markers in tracked files"
    print_indented_output "$conflict_marker_hits"
  else
    record_result PASS "no unresolved merge-conflict markers in tracked files"
  fi
else
  record_result WARN "merge-conflict marker scan -- git unavailable or not a git repo"
fi

if [[ -f "$ROOT/tools/audit_ai_paths.sh" ]]; then
  record_result FAIL "legacy audit helper should move under .agentcortex/tools/: $ROOT/tools/audit_ai_paths.sh"
else
  record_result PASS "legacy audit helper not present at tools/audit_ai_paths.sh"
fi

skill_errors=0
for skill_file in "$ROOT"/.agent/skills/*; do
  [[ -f "$skill_file" ]] || continue
  skill_name="$(basename "$skill_file")"
  [[ "$skill_name" == ".gitkeep" ]] && continue
  codex_skill_path="$ROOT/.agents/skills/$skill_name"
  if [[ ! -s "$skill_file" ]]; then
    printf '  empty skill metadata: %s\n' "$skill_file"
    skill_errors=$((skill_errors + 1))
  fi
  if [[ ! -d "$codex_skill_path" ]]; then
    printf '  missing codex skill dir: %s\n' "$codex_skill_path"
    skill_errors=$((skill_errors + 1))
  elif [[ ! -f "$codex_skill_path/SKILL.md" ]]; then
    printf '  missing skill definition: %s/SKILL.md\n' "$codex_skill_path"
    skill_errors=$((skill_errors + 1))
  fi
done
if [[ "$skill_errors" -gt 0 ]]; then
  record_result FAIL "skill metadata mirrors out of sync"
else
  record_result PASS "skill metadata mirrors are consistent"
fi

if [[ "$IS_SOURCE_REPO" -eq 1 ]]; then
  record_result SKIP "legacy rule surfaces -- source repo (adapter surfaces created by deploy)"
else
  check_file_group "legacy rule surfaces present" \
    "$ROOT/.antigravity/rules.md" \
    "$ROOT/.agent/rules/rules.md" \
    "$CODEX_INSTALL"

  check_contains_regex \
    "$ROOT/.agent/rules/rules.md" \
    '\.antigravity/rules\.md' \
    "legacy rules redirect to canonical antigravity rules" \
    "legacy rules missing canonical redirect"
  check_contains_literal \
    "$ROOT/.agent/rules/rules.md" \
    'legacy compatibility' \
    "legacy rules include compatibility marker" \
    "legacy rules missing compatibility marker"
  check_contains_literal \
    "$ROOT/.antigravity/rules.md" \
    'docker system prune -a' \
    "antigravity rules include docker system prune guard" \
    "antigravity rules missing docker system prune guard"
  check_contains_literal \
    "$ROOT/.antigravity/rules.md" \
    'chown -R' \
    "antigravity rules include chown -R guard" \
    "antigravity rules missing chown -R guard"
  check_contains_literal \
    "$ROOT/.antigravity/rules.md" \
    'rollback' \
    "antigravity rules include rollback reminder" \
    "antigravity rules missing rollback reminder"
fi

# ADR-004: bootstrap MUST ship the override-layer load step. Structural
# enforcement only — the framework ships the instruction; per-agent compliance
# ("did this agent actually read the override") is honor-system like the
# Sentinel and is NOT falsely claimed as test-enforced.
check_contains_literal \
  "$WORKFLOWS_DIR/bootstrap.md" \
  'Load Override Layer' \
  "bootstrap ships override-layer load step (ADR-004 §1a)" \
  "bootstrap missing override-layer load step (ADR-004 §1a)"

ACTIVE_CODEX_RULES="$ROOT/codex/rules/default.rules"
[[ -f "$ACTIVE_CODEX_RULES" ]] || ACTIVE_CODEX_RULES="$CODEX_RULES"
if [[ -f "$ACTIVE_CODEX_RULES" ]]; then
  check_contains_literal \
    "$ACTIVE_CODEX_RULES" \
    'prefix_rule(' \
    "codex rules include prefix_rule()" \
    "codex rules missing prefix_rule()"
  check_contains_literal \
    "$ACTIVE_CODEX_RULES" \
    'docker system prune -a' \
    "codex rules include docker system prune guard" \
    "codex rules missing docker system prune guard"
  check_contains_literal \
    "$ACTIVE_CODEX_RULES" \
    'chown -R' \
    "codex rules include chown -R guard" \
    "codex rules missing chown -R guard"
else
  record_result FAIL "codex rules file missing: $ACTIVE_CODEX_RULES"
fi

check_contains_literal \
  "$ROOT_DEPLOY_SH" \
  '.agentcortex/bin/deploy.sh' \
  "deploy_brain.sh references canonical deploy script" \
  "deploy_brain.sh missing canonical deploy reference"
check_contains_literal \
  "$ROOT_DEPLOY_PS1" \
  "'.agentcortex', 'bin', 'deploy.sh'" \
  "deploy_brain.ps1 references canonical deploy script" \
  "deploy_brain.ps1 missing canonical deploy reference"
check_contains_literal \
  "$ROOT_DEPLOY_CMD" \
  'deploy_brain.ps1' \
  "deploy_brain.cmd delegates to sibling wrapper" \
  "deploy_brain.cmd missing sibling-wrapper delegation"

worklog_contract_files=(
  "$ROOT/AGENTS.md"
  "$ROOT/.agent/rules/engineering_guardrails.md"
  "$ROOT/.agent/rules/security_guardrails.md"
  "$ROOT/.agent/rules/state_machine.md"
  "$ROOT/.agent/workflows/bootstrap.md"
  "$ROOT/.agent/workflows/plan.md"
  "$ROOT/.agent/workflows/handoff.md"
  "$ROOT/.agent/workflows/ship.md"
  "$PLATFORM_DOC"
  "$ROOT/.agentcortex/docs/NONLINEAR_SCENARIOS.md"
  "$ROOT/.agentcortex/docs/guides/antigravity-v5-runtime.md"
)
worklog_contract_errors=0
for f in "${worklog_contract_files[@]}"; do
  if [[ ! -f "$f" ]]; then
    printf '  worklog contract file not found: %s\n' "$f"
    worklog_contract_errors=$((worklog_contract_errors + 1))
    continue
  fi
  if ! grep -F -q -- '<worklog-key>' "$f"; then
    printf '  worklog contract missing normalized key reference: %s\n' "$f"
    worklog_contract_errors=$((worklog_contract_errors + 1))
  fi
  if grep -F -q -- 'docs/context/work/<branch-name>.md' "$f"; then
    printf '  stale branch-name worklog path contract: %s\n' "$f"
    worklog_contract_errors=$((worklog_contract_errors + 1))
  fi
  if grep -F -q -- 'docs/context/work/<branch>.md' "$f"; then
    printf '  stale raw branch worklog path contract: %s\n' "$f"
    worklog_contract_errors=$((worklog_contract_errors + 1))
  fi
done
if [[ "$worklog_contract_errors" -gt 0 ]]; then
  record_result FAIL "work log contract references are stale"
else
  record_result PASS "work log contract references use normalized keys"
fi

archive_contract_files=(
  "$ROOT/.agent/workflows/handoff.md"
  "$ROOT/.agentcortex/docs/guides/token-governance.md"
  "$ROOT/.agentcortex/docs/guides/portable-minimal-kit.md"
)
archive_contract_errors=0
for f in "${archive_contract_files[@]}"; do
  if [[ ! -f "$f" ]]; then
    printf '  archive contract file not found: %s\n' "$f"
    archive_contract_errors=$((archive_contract_errors + 1))
    continue
  fi
  if ! grep -F -q -- '<worklog-key>-<YYYYMMDD>' "$f"; then
    printf '  archive contract missing normalized key reference: %s\n' "$f"
    archive_contract_errors=$((archive_contract_errors + 1))
  fi
  if grep -F -q -- 'docs/context/archive/work/<branch>-<YYYYMMDD>.md' "$f"; then
    printf '  stale archive branch worklog path contract: %s\n' "$f"
    archive_contract_errors=$((archive_contract_errors + 1))
  fi
done
if [[ "$archive_contract_errors" -gt 0 ]]; then
  record_result FAIL "archive contract references are stale"
else
  record_result PASS "archive contract references use normalized keys"
fi

check_contains_literal \
  "$WORKFLOWS_DIR/bootstrap.md" \
  'Recommended Skills' \
  "bootstrap includes Recommended Skills contract" \
  "bootstrap missing Recommended Skills contract"
phase_skill_files=(
  "$WORKFLOWS_DIR/plan.md"
  "$WORKFLOWS_DIR/implement.md"
  "$WORKFLOWS_DIR/review.md"
  "$WORKFLOWS_DIR/test.md"
  "$WORKFLOWS_DIR/handoff.md"
  "$WORKFLOWS_DIR/ship.md"
)
phase_skill_errors=0
for f in "${phase_skill_files[@]}"; do
  if [[ ! -f "$f" ]]; then
    printf '  phase skill file not found: %s\n' "$f"
    phase_skill_errors=$((phase_skill_errors + 1))
    continue
  fi
  if ! grep -F -q -- 'Recommended Skills' "$f"; then
    printf '  missing Recommended Skills phase hook: %s\n' "$f"
    phase_skill_errors=$((phase_skill_errors + 1))
  fi
done
if [[ "$phase_skill_errors" -gt 0 ]]; then
  record_result FAIL "phase workflows missing Recommended Skills hooks"
else
  record_result PASS "phase workflows include Recommended Skills hooks"
fi
check_contains_literal \
  "$WORKFLOWS_DIR/ship.md" \
  '## Ship Checklist' \
  "ship workflow includes mandatory ship checklist" \
  "ship workflow missing mandatory ship checklist"
check_contains_literal \
  "$WORKFLOWS_DIR/ship.md" \
  'Active Work Log archived to `.agentcortex/context/archive/`' \
  "ship workflow checklist includes archive step" \
  "ship workflow checklist missing archive step"

# Phase verification contract: gated workflows must reference bootstrap §2a
phase_verify_files=(
  "$WORKFLOWS_DIR/plan.md"
  "$WORKFLOWS_DIR/implement.md"
  "$WORKFLOWS_DIR/review.md"
  "$WORKFLOWS_DIR/test.md"
  "$WORKFLOWS_DIR/handoff.md"
  "$WORKFLOWS_DIR/ship.md"
)
phase_verify_errors=0
for f in "${phase_verify_files[@]}"; do
  if ! grep -q -i 'Phase Verification' "$f" 2>/dev/null; then
    printf '  missing Phase Verification section: %s\n' "$(basename "$f")"
    phase_verify_errors=$((phase_verify_errors + 1))
  fi
done
if [[ "$phase_verify_errors" -gt 0 ]]; then
  record_result FAIL "phase workflows missing Phase Verification sections"
else
  record_result PASS "phase workflows include Phase Verification sections"
fi

# Gate evidence contract: bootstrap template must include Gate Evidence section
check_contains_literal \
  "$WORKFLOWS_DIR/bootstrap.md" \
  '## Gate Evidence' \
  "bootstrap template includes Gate Evidence section" \
  "bootstrap template missing Gate Evidence section"
check_contains_literal \
  "$WORKFLOWS_DIR/app-init.md" \
  'merge-safe retrofit guidance' \
  "app-init includes merge-safe docs retrofit guidance" \
  "app-init missing merge-safe docs retrofit guidance"
check_contains_literal \
  "$WORKFLOWS_DIR/bootstrap.md" \
  'Partial adoption advisory' \
  "bootstrap includes bounded partial adoption advisory" \
  "bootstrap missing bounded partial adoption advisory"
check_contains_literal \
  "$WORKFLOWS_DIR/bootstrap.md" \
  'status: living' \
  "bootstrap requires status: living before L1 authority reads" \
  "bootstrap missing L1 status: living gate"
check_contains_literal \
  "$WORKFLOWS_DIR/bootstrap.md" \
  'BOTH `status: living` and `domain:`' \
  "bootstrap requires full L1 contract before authority reads" \
  "bootstrap missing full L1 contract gate"
check_contains_literal \
  "$WORKFLOWS_DIR/bootstrap.md" \
  'External authority rule' \
  "bootstrap forces external specs through spec-intake" \
  "bootstrap missing external authority routing rule"
check_contains_literal \
  "$WORKFLOWS_DIR/bootstrap.md" \
  'background context' \
  "bootstrap treats substantial background material as spec-intake input" \
  "bootstrap missing substantial-background intake rule"
check_contains_literal \
  "$WORKFLOWS_DIR/bootstrap.md" \
  'Primary Domain Snapshot' \
  "bootstrap records primary_domain snapshot" \
  "bootstrap missing primary_domain snapshot contract"
check_contains_literal \
  "$WORKFLOWS_DIR/spec-intake.md" \
  'Domain Doc L1 conflict check' \
  "spec-intake includes L1 conflict check for external specs" \
  "spec-intake missing L1 conflict check for external specs"
check_contains_literal \
  "$WORKFLOWS_DIR/ship.md" \
  'structured `routing_actions` blocks' \
  "ship workflow scopes routing_actions to structured blocks" \
  "ship workflow missing structured routing_actions wording"
check_contains_literal \
  "$WORKFLOWS_DIR/ship.md" \
  'Generic skip text is invalid' \
  "ship workflow hardens primary_domain skip justification" \
  "ship workflow missing primary_domain skip-hardening wording"
check_contains_literal \
  "$WORKFLOWS_DIR/ship.md" \
  'Primary Domain Snapshot' \
  "ship workflow cross-checks bootstrap primary_domain snapshot" \
  "ship workflow missing primary_domain snapshot cross-check"
check_contains_literal \
  "$WORKFLOWS_DIR/ship.md" \
  'Acceptable examples:' \
  "ship workflow gives acceptable skip examples" \
  "ship workflow missing acceptable skip examples"
if [[ -f "$ROOT/.agentcortex/templates/docs-readme.md" ]]; then
  check_contains_literal \
    "$ROOT/.agentcortex/templates/docs-readme.md" \
    '## Retrofit Note' \
    "docs README template includes retrofit note" \
    "docs README template missing retrofit note"
else
  record_result SKIP "docs README template retrofit note -- template not deployed"
fi

document_governance_spec_errors=0
document_governance_partial_warn=0
domain_doc_frontmatter_warn=0
shopt -s nullglob
for spec in "$ROOT"/docs/specs/*.md; do
  [[ -f "$spec" ]] || continue
  if grep -Eq '^primary_domain:\s*[^[:space:]]+' "$spec"; then
    if ! grep -F -q '## Domain Decisions' "$spec"; then
      printf '  spec with primary_domain missing Domain Decisions: %s\n' "$spec"
      document_governance_spec_errors=$((document_governance_spec_errors + 1))
    fi
    if [[ ! -d "$ROOT/docs/architecture" ]]; then
      printf '  partial document-governance adoption: %s declares primary_domain but docs/architecture/ is missing\n' "$spec"
      document_governance_partial_warn=$((document_governance_partial_warn + 1))
    fi
  fi
done
if [[ "$document_governance_spec_errors" -gt 0 ]]; then
  record_result FAIL "document-governance spec contract violations detected"
else
  record_result PASS "document-governance specs preserve primary_domain and Domain Decisions contract"
fi
if [[ "$document_governance_partial_warn" -gt 0 ]]; then
  record_result WARN "partial document-governance adoption advisories detected: ${document_governance_partial_warn}"
fi

if [[ -d "$ROOT/docs/architecture" ]]; then
  for domain_doc in "$ROOT"/docs/architecture/*.md; do
    [[ -f "$domain_doc" ]] || continue
    [[ "$domain_doc" == *.log.md ]] && continue
    if ! grep -Eq '^status:\s*living$' "$domain_doc" || ! grep -Eq '^domain:\s*[^[:space:]]+' "$domain_doc"; then
      printf '  domain doc candidate missing full L1 contract (status: living + domain:): %s\n' "$domain_doc"
      domain_doc_frontmatter_warn=$((domain_doc_frontmatter_warn + 1))
    fi
  done
fi
if [[ "$domain_doc_frontmatter_warn" -gt 0 ]]; then
  record_result WARN "legacy domain doc candidates were skipped as L1 authority (missing full L1 contract: status: living + domain:): ${domain_doc_frontmatter_warn}. Do not add frontmatter directly; use /govern-docs when promoting them."
else
  record_result PASS "domain doc candidates declare the full L1 contract when present"
fi

routing_action_errors=0
routing_action_warnings=0
for review in "$ROOT"/docs/reviews/*.md; do
  [[ -f "$review" ]] || continue
  if grep -F -q 'routing_actions:' "$review"; then
    for required in 'finding:' 'target_doc:' 'status:' 'owner:'; do
      if ! grep -F -q "$required" "$review"; then
        printf '  review snapshot missing routing_actions field %s: %s\n' "$required" "$review"
        routing_action_errors=$((routing_action_errors + 1))
      fi
    done
    while IFS= read -r target; do
      [[ -z "$target" ]] && continue
      if [[ ! "$target" =~ ^docs/(architecture|specs)/.+\.md$ ]]; then
        printf '  routing_actions target_doc must point to docs/architecture/*.md or docs/specs/*.md: %s (%s)\n' "$review" "$target"
        routing_action_errors=$((routing_action_errors + 1))
      elif [[ ! -f "$ROOT/$target" ]]; then
        printf '  routing_actions target_doc does not exist yet: %s (%s)\n' "$review" "$target"
        routing_action_warnings=$((routing_action_warnings + 1))
      fi
    done < <(sed -n 's/^[[:space:]]*target_doc:[[:space:]]*"\{0,1\}\([^"]*\)"\{0,1\}$/\1/p' "$review")
    while IFS= read -r status; do
      [[ -z "$status" ]] && continue
      case "$status" in
        pending|merged|rejected) ;;
        *)
          printf '  routing_actions status must be pending, merged, or rejected: %s (%s)\n' "$review" "$status"
          routing_action_errors=$((routing_action_errors + 1))
          ;;
      esac
    done < <(sed -n 's/^[[:space:]]*status:[[:space:]]*\([a-z]*\).*$/\1/p' "$review")
  fi
done
if [[ "$routing_action_errors" -gt 0 ]]; then
  record_result FAIL "routing_actions contract violations detected"
else
  record_result PASS "routing_actions contract is structurally valid when present"
fi
if [[ "$routing_action_warnings" -gt 0 ]]; then
  record_result WARN "routing_actions target docs need follow-up: ${routing_action_warnings}"
fi
shopt -u nullglob

check_contains_literal \
  "$CANONICAL_DEPLOY_SH" \
  'LEGACY_IGNORE_START="# AI Brain OS - Agent System & Local Context"' \
  "deploy script supports legacy ignore marker migration" \
  "deploy script missing legacy ignore marker support"
check_contains_literal \
  "$CANONICAL_DEPLOY_SH" \
  'strip_managed_ignore_blocks() {' \
  "deploy script includes managed ignore block replacement helper" \
  "deploy script missing managed ignore replacement helper"
check_contains_literal \
  "$CANONICAL_DEPLOY_SH" \
  '.agentcortex/bin/' \
  "deploy script targets canonical .agentcortex/bin namespace" \
  "deploy script missing canonical namespace deployment path"

DEPLOY_IGNORE_BLOCK="$(awk '
/^# Agentic OS Template - Downstream Ignore Defaults$/ { capture = 1 }
capture { print }
/^# End Agentic OS Template - Downstream Ignore Defaults$/ {
  if (capture) {
    exit
  }
}
' "$CANONICAL_DEPLOY_SH")"

if [[ -z "$DEPLOY_IGNORE_BLOCK" ]]; then
  record_result FAIL "deploy ignore block missing from deploy script"
else
  missing_patterns=0
  for pattern in \
    '# Agentic OS Template - Downstream Ignore Defaults' \
    '.agentcortex/context/work/*.md' \
    '.agentcortex/context/private/' \
    '.agentcortex/context/.guard_receipt.json' \
    '.agentcortex/context/.guard_locks/' \
    '.agent/private/' \
    '.agentcortex-src/' \
    '*.acx-incoming' \
    '.openrouter/' \
    '.claude-chat/' \
    '.cursor/' \
    '.antigravity/scratch/' \
    '# End Agentic OS Template - Downstream Ignore Defaults'; do
    if ! printf '%s\n' "$DEPLOY_IGNORE_BLOCK" | grep -x -F -q -- "$pattern"; then
      printf '  deploy ignore block missing required pattern: %s\n' "$pattern"
      missing_patterns=$((missing_patterns + 1))
    fi
  done
  if ! printf '%s\n' "$DEPLOY_IGNORE_BLOCK" | grep -F -q '.agentcortex/context/work/.gitkeep.md'; then
    printf '  deploy ignore block missing .gitkeep.md negation pattern\n'
    missing_patterns=$((missing_patterns + 1))
  fi
  for forbidden_downstream_pattern in \
    '.agentcortex/context/current_state.md' \
    '.agentcortex/context/archive/' \
    'deploy_brain.sh' \
    'deploy_brain.ps1' \
    'deploy_brain.cmd' \
    '.agentcortex-manifest'; do
    if printf '%s\n' "$DEPLOY_IGNORE_BLOCK" | grep -x -F -q -- "$forbidden_downstream_pattern"; then
      printf '  deploy ignore block must not include tracked file: %s\n' "$forbidden_downstream_pattern"
      missing_patterns=$((missing_patterns + 1))
    fi
  done
  if [[ "$missing_patterns" -gt 0 ]]; then
    record_result FAIL "deploy ignore block contents are invalid"
  else
    record_result PASS "deploy ignore block contents are valid"
  fi
fi

if [[ "$IS_SOURCE_REPO" -eq 1 ]]; then
  if [[ -f "$ROOT/docs/README_zh-TW.md" ]]; then
    check_contains_literal \
      "$ROOT/docs/README_zh-TW.md" \
      '用工作流程、交付閘門與工程護欄' \
      "README_zh-TW.md encoding looks healthy" \
      "README_zh-TW.md appears mojibaked or re-encoded"
  fi
  if [[ -f "$ROOT/README.md" ]]; then
    check_contains_literal \
      "$ROOT/README.md" \
      'governance-first layer for AI coding agents' \
      "README.md encoding looks healthy" \
      "README.md appears mojibaked or re-encoded"
  fi
fi
if [[ -f "$ROOT/.agentcortex/docs/TESTING_PROTOCOL_zh-TW.md" ]]; then
  check_contains_literal \
    "$ROOT/.agentcortex/docs/TESTING_PROTOCOL_zh-TW.md" \
    '測試教戰守則' \
    "TESTING_PROTOCOL_zh-TW.md encoding looks healthy" \
    "TESTING_PROTOCOL_zh-TW.md appears mojibaked or re-encoded"
fi
if [[ -f "$ROOT/.agentcortex/docs/guides/audit-guardrails.md" ]]; then
  check_contains_literal \
    "$ROOT/.agentcortex/docs/guides/audit-guardrails.md" \
    'Test 1: Invisible Assistant Check (.gitignore Automation)' \
    "audit-guardrails.md encoding looks healthy" \
    "audit-guardrails.md appears mojibaked or re-encoded"
fi
if [[ -f "$ROOT/.agentcortex/docs/guides/audit-guardrails_zh-TW.md" ]]; then
  check_contains_literal \
    "$ROOT/.agentcortex/docs/guides/audit-guardrails_zh-TW.md" \
    '為什麼不寫成自動化 Shell Script？' \
    "audit-guardrails_zh-TW.md encoding looks healthy" \
    "audit-guardrails_zh-TW.md appears mojibaked or re-encoded"
fi

WORKLOG_MAX_LINES="${WORKLOG_MAX_LINES:-300}"
WORKLOG_MAX_KB="${WORKLOG_MAX_KB:-12}"
ACTIVE_WORKLOG_WARN_THRESHOLD="${ACTIVE_WORKLOG_WARN_THRESHOLD:-8}"
ACTIVE_WORKLOG_FAIL_THRESHOLD="${ACTIVE_WORKLOG_FAIL_THRESHOLD:-12}"
ARCHIVE_SIZE_WARN_KB="${ARCHIVE_SIZE_WARN_KB:-10240}"
WORKLOG_GATE_EVIDENCE_LEGACY_CUTOFF="${WORKLOG_GATE_EVIDENCE_LEGACY_CUTOFF:-2026-03-25}"
WORKLOG_DIR="$ROOT/.agentcortex/context/work"
if [[ -d "$WORKLOG_DIR" ]]; then
  worklog_warnings=0
  worklog_count=0
  for wl in "$WORKLOG_DIR"/*.md; do
    [[ -f "$wl" ]] || continue
    worklog_count=$((worklog_count + 1))
    wl_lines="$(wc -l < "$wl" 2>/dev/null)" || true
    wl_bytes="$(wc -c < "$wl" 2>/dev/null)" || true
    wl_kb=$(( ${wl_bytes:-0} / 1024 ))
    if [[ "$wl_lines" -gt "$WORKLOG_MAX_LINES" ]] || [[ "$wl_kb" -gt "$WORKLOG_MAX_KB" ]]; then
      printf '  work log needs compaction: %s (%s lines, %sKB)\n' "$(basename "$wl")" "$wl_lines" "$wl_kb"
      worklog_warnings=$((worklog_warnings + 1))
    fi
  done
  if [[ "$worklog_warnings" -gt 0 ]]; then
    record_result FAIL "work log compaction warnings detected"
  else
    record_result PASS "active work log sizes are within compaction thresholds"
  fi
  if [[ "$worklog_count" -gt "$ACTIVE_WORKLOG_FAIL_THRESHOLD" ]]; then
    record_result FAIL "active work log count exceeds hard limit (${worklog_count} > ${ACTIVE_WORKLOG_FAIL_THRESHOLD}); archive completed branches via /handoff or rm"
  elif [[ "$worklog_count" -gt "$ACTIVE_WORKLOG_WARN_THRESHOLD" ]]; then
    record_result WARN "active work log count exceeds hygiene threshold (${worklog_count} > ${ACTIVE_WORKLOG_WARN_THRESHOLD}; hard limit ${ACTIVE_WORKLOG_FAIL_THRESHOLD})"
  else
    record_result PASS "active work log count is within hygiene threshold"
  fi
  # Archive directory size — surface unbounded growth before it becomes an
  # ingestion-time hazard. WARN-only; opt-out via ARCHIVE_SIZE_WARN_KB=0.
  ARCHIVE_DIR="$ROOT/.agentcortex/context/archive"
  if [[ -d "$ARCHIVE_DIR" ]] && [[ "$ARCHIVE_SIZE_WARN_KB" -gt 0 ]]; then
    archive_kb="$(du -sk "$ARCHIVE_DIR" 2>/dev/null | awk '{print $1}')" || true
    if [[ -n "$archive_kb" ]] && [[ "$archive_kb" -gt "$ARCHIVE_SIZE_WARN_KB" ]]; then
      record_result WARN "archive size ${archive_kb}KB exceeds threshold ${ARCHIVE_SIZE_WARN_KB}KB; consider /retro-driven cold-tier rotation"
    else
      record_result PASS "archive size within threshold (${archive_kb:-0}KB / ${ARCHIVE_SIZE_WARN_KB}KB)"
    fi
  fi
  # Work Log integrity marker check — detect truncated writes from interrupted sessions
  worklog_truncated=0
  for wl in "$WORKLOG_DIR"/*.md; do
    [[ -f "$wl" ]] || continue
    wl_content="$(cat "$wl" 2>/dev/null)"
    # A well-formed work log must have at least a Branch header and one ## section.
    # Accept list form ("- Branch:" or "- **Branch**:") AND table form
    # ("| Branch | ... |") — the canonical template at .agentcortex/templates/worklog.md
    # uses a table for readability; earlier versions only matched list form.
    if ! printf '%s' "$wl_content" | grep -Eq '(^- (\*\*Branch\*\*|Branch):|^\| (\*\*Branch\*\*|Branch) +\|)' || \
       ! printf '%s' "$wl_content" | grep -q '^## '; then
      printf '  possibly truncated work log: %s\n' "$(basename "$wl")"
      worklog_truncated=$((worklog_truncated + 1))
    fi
  done
  if [[ "$worklog_truncated" -gt 0 ]]; then
    record_result WARN "possibly truncated work logs detected: ${worklog_truncated}"
  else
    record_result PASS "active work logs pass structural integrity check"
  fi

  # Work Log evidence chain check (per AGENTS.md Work Log Contract)
  phase_field_missing=0
  checkpoint_missing=0
  gate_evidence_missing=0
  legacy_gate_evidence_missing=0
  gate_progression_illegal=0
  gate_progression_skipped=0
  phase_summary_missing=0
  sentinel_marker_missing=0
  test_gate_results_missing=0
  current_phase_incoherent=0
  shipped_not_archived=0
  evidence_placeholder_only=0
  review_pass_with_unproven=0
  reclassify_header_not_reset=0
  handoff_resume_incomplete=0
  hotfix_ship_no_evidence=0
  adr_coverage_undocumented=0
  for wl in "$WORKLOG_DIR"/*.md; do
    [[ -f "$wl" ]] || continue
    wl_content="$(cat "$wl" 2>/dev/null)"
    created_date="$(printf '%s' "$wl_content" | sed -n 's/^- \*\*Created Date\*\*:[[:space:]]*//p' | head -n 1 | tr -d '\r')"
    legacy_gate_evidence=0
    if [[ -n "$created_date" ]] && [[ "$created_date" < "$WORKLOG_GATE_EVIDENCE_LEGACY_CUTOFF" ]]; then
      legacy_gate_evidence=1
    fi
    # Header field: Current Phase — accept list OR table form (see template/worklog.md)
    if ! printf '%s' "$wl_content" | grep -qE '(^- (`Current Phase`|Current Phase):|^\| (`Current Phase`|Current Phase) +\|)'; then
      phase_field_missing=$((phase_field_missing + 1))
    fi
    # Header field: Checkpoint SHA — accept list OR table form
    if ! printf '%s' "$wl_content" | grep -qE '(^- (`Checkpoint SHA`|Checkpoint SHA):|^\| (`Checkpoint SHA`|Checkpoint SHA) +\|)'; then
      checkpoint_missing=$((checkpoint_missing + 1))
    fi
    # Runtime section: ## Gate Evidence — check existence, receipt format,
    # AND phase progression legality. Illegal progression = FAIL.
    if ! printf '%s' "$wl_content" | grep -q '^## Gate Evidence'; then
      if [[ "$legacy_gate_evidence" -eq 1 ]]; then
        legacy_gate_evidence_missing=$((legacy_gate_evidence_missing + 1))
      else
        gate_evidence_missing=$((gate_evidence_missing + 1))
      fi
    elif ! printf '%s' "$wl_content" | grep -qiE '^(`?- )?gate:.*verdict:'; then
      if [[ "$legacy_gate_evidence" -eq 1 ]]; then
        legacy_gate_evidence_missing=$((legacy_gate_evidence_missing + 1))
      else
        gate_evidence_missing=$((gate_evidence_missing + 1))
      fi
    else
      # Parse gate receipts and verify phase progression. Use PYTHON_BIN
      # (set in the preamble) so the SKIP path is consistent with
      # run_python_check — silent skips here previously produced PASS by
      # accident when Python was unavailable.
      if [[ -n "$PYTHON_BIN" ]]; then
        # Python source passed via single-quoted heredoc → variable so that
        # shell-special characters in the code (", `, $, ->) are NOT interpreted
        # by bash. Previously this was an inline -c "..." double-quoted string;
        # the embedded `"` and `->` leaked to the shell (created a stray file and
        # corrupted the -c argument), silently disabling this entire check.
        _acx_gate_py=$(cat <<'PYEOF'
import sys, re
# quick-win / unknown: implement can go directly to ship (fast path)
LEGAL_DEFAULT = {
    'bootstrap': ['plan'],
    'plan':      ['implement'],
    'implement': ['review','test','ship'],
    'review':    ['implement','test','ship'],
    'test':      ['ship','implement'],
    'handoff':   ['ship','retro'],
    'ship':      [],
}
# feature / architecture-change: must go through review+test+handoff; no shortcuts
LEGAL_STRICT = {
    'bootstrap': ['plan'],
    'plan':      ['implement'],
    'implement': ['review','test'],
    'review':    ['implement','test'],
    'test':      ['handoff','implement'],
    'handoff':   ['ship','retro'],
    'ship':      [],
}
# hotfix: must review+test but handoff is optional (goes test->ship directly)
# plan is always required per engineering_guardrails.md §10.2 — no implement shortcut
LEGAL_HOTFIX = {
    'bootstrap': ['plan'],
    'plan':      ['implement'],
    'implement': ['review','test'],
    'review':    ['implement','test'],
    'test':      ['ship','implement'],
    'ship':      [],
}
content = sys.stdin.read()
lines = content.splitlines()
wl_class = ''
for l in lines:
    m = re.match(r'^-\s+(?:\*\*)?[Cc]lassification(?:\*\*)?\s*:\s+\`?([a-zA-Z][\w-]*)', l)
    if not m:
        # table form: | Classification | `feature` |
        m = re.match(r'^\|\s*(?:\*\*)?[Cc]lassification(?:\*\*)?\s*\|\s*\`?([a-zA-Z][\w-]*)', l)
    if m:
        wl_class = m.group(1).lower()
        break
if wl_class in ('feature', 'architecture-change'):
    LEGAL = LEGAL_STRICT
elif wl_class == 'hotfix':
    LEGAL = LEGAL_HOTFIX
elif wl_class in ('quick-win', 'tiny-fix'):
    LEGAL = LEGAL_DEFAULT
else:
    # H1: fail-closed for unknown/misspelled classification — use strictest transitions
    # (mirrors the completeness check which also treats unknown as feature-level)
    LEGAL = LEGAL_STRICT
# H4: count STRUCTURED reclassification records in Drift Log (count-based, not position-based)
# Requires format: Reclassif* <sep> ... <arrow> — rejects prose mentions like "considered but rejected"
# e.g. "Reclassification: quick-win -> feature" matches; "reclassification considered" does not
# Count-based: allows one reset per record; normal drift entries after reclassif do NOT invalidate it
in_drift = False
reclassify_count = 0
for l in lines:
    if re.match(r'^## Drift Log', l):
        in_drift = True
        continue
    elif in_drift and re.match(r'^## ', l):
        break
    elif in_drift:
        _rm = re.search(r'\bReclassif\w*\s*[:\-]\s*([\w-]+)\s*->\s*([\w-]+)', l)
        if _rm and _rm.group(1).lower() != _rm.group(2).lower():
            reclassify_count += 1
# T48: section-scope gate parsing to ## Gate Evidence section only
# T154: only the FIRST ## Gate Evidence section is authoritative
# T175/T178/T241: fenced code blocks (backtick/tilde, 0-3 space indent per CommonMark)
# T181/T242: HTML comment blocks (order-aware finditer left-to-right)
# T243: fail-closed — if heading exists but suppressed, emit error
# T244: run fence/comment tracking on EVERY line (was: only outside section)
#   Prevents fenced content inside ## Gate Evidence from being collected as real receipts
#   and prevents fence-parity leakage across the section boundary (opener inside → closer outside)
# T247: track masked receipt-format lines inside the section during the main loop
#   (replaces post-loop raw-rescan which had false-positives and false-negatives)
RECEIPT_RE = re.compile(r'^(?:\x60?- )?gate:\s*\w+\s*\|', re.IGNORECASE)
# Inside fences, lines may be indented; allow leading whitespace for masked-receipt detection
MASKED_RECEIPT_RE = re.compile(r'^\s*(?:\x60?- )?gate:\s*\w+\s*\|', re.IGNORECASE)
in_gate_evidence_section = False
gate_evidence_seen = False
gate_lines = []
masked_receipt_in_section = False  # T247: receipt-format line was present but masked
in_code_fence = False
in_html_comment = False
for l in lines:
    was_in_fence = in_code_fence
    if re.match(r'^ {0,3}(\x60{3,}|~{3,})', l):
        in_code_fence = not in_code_fence
    was_in_comment = in_html_comment
    for _m in re.finditer(r'<!--|-->', l):
        in_html_comment = (_m.group() == '<!--')
    # masked: line is/was inside a fence or comment (fence marker lines are also masked)
    masked = (was_in_fence or in_code_fence) or (was_in_comment or in_html_comment)
    if re.match(r'^## Gate Evidence', l) and not gate_evidence_seen and not in_code_fence and not in_html_comment:
        in_gate_evidence_section = True
        gate_evidence_seen = True
        continue
    if in_gate_evidence_section and re.match(r'^## ', l) and not masked:
        in_gate_evidence_section = False
        continue
    if in_gate_evidence_section:
        if masked:
            if MASKED_RECEIPT_RE.match(l):
                masked_receipt_in_section = True  # T247: real receipt hidden in fence/comment
        else:
            gate_lines.append(l)
# T243: fail-closed if heading exists but was suppressed (fence/comment blocked recognition)
if not gate_evidence_seen:
    if any(re.match(r'^## Gate Evidence', l) for l in lines):
        print('incomplete:gate-evidence-suppressed (unclosed fence or HTML comment above ## Gate Evidence -- validate manually)')
        sys.exit(0)
# T245: fail-closed if fence/comment was left unclosed INSIDE Gate Evidence
# (receipts inside the unclosed block are silently masked — signal rather than returning ok)
if in_code_fence or in_html_comment:
    print('incomplete:unterminated-fence-or-comment (unclosed code fence or HTML comment in ## Gate Evidence -- validate manually)')
    sys.exit(0)
# T247: no unmasked receipt collected but at least one was masked — targeted error
# Uses main-loop masking state (no separate rescan), so it correctly respects
# the first-section guard, fence/comment state, and masked ## headings.
unmasked_receipt = any(RECEIPT_RE.match(l) for l in gate_lines)
if gate_evidence_seen and not unmasked_receipt and masked_receipt_in_section:
    print('incomplete:receipts-in-fence (Gate Evidence has receipt-format lines but all are inside code fences or HTML comments -- move receipts out of code blocks)')
    sys.exit(0)
gates = []
has_ship_receipt = False  # H3: track ANY ship receipt regardless of verdict
review_not_ready = False  # track pending re-review requirement after NOT READY reverse edge
resets_used = 0  # H4: track consumed reclassification records
for l in gate_lines:
    m = re.match(r'^(?:\x60?- )?gate:\s*(\w+)\s*\|', l, re.IGNORECASE)
    if m:
        phase = m.group(1).lower()
        # H3: record ship presence BEFORE the verdict filter
        if phase == 'ship':
            has_ship_receipt = True
        # supporting workflows are out-of-band; exclude to avoid false illegal-transition flags
        if phase in ('retro', 'research', 'brainstorm', 'decide', 'audit'):
            continue
        # Only count PASS verdicts; NOT READY / FAIL are reverse edges, not forward progress
        v = re.search(r'\|[^|]*verdict:\s*([A-Za-z _]+?)(\s*\||$)', l, re.IGNORECASE)
        if v and v.group(1).strip().upper() != 'PASS':
            # NOT READY / FAIL review is a reverse edge — discard the preceding
            # implement to avoid a false-positive implement→implement pair after
            # re-implementation (test.md §Step 5 reverse-edge; review.md §NOT READY)
            if phase == 'review' and gates and gates[-1] == 'implement':
                gates.pop()
                review_not_ready = True  # flag: re-review required before test/ship
            continue
        # PASS verdict: if review PASS, clear the pending re-review flag
        if phase == 'review':
            review_not_ready = False
        # H4: Reclassification reset — one reset per structured drift record; count-based
        if phase == 'bootstrap' and gates and reclassify_count > resets_used:
            gates = []
            resets_used += 1
        gates.append(phase)
# Completeness check first — valid even with 1 gate (avoids early-return bypass)
gate_set = set(gates)
# H3: completeness triggers on ANY ship receipt, not just PASS ones
if has_ship_receipt or 'ship' in gate_set:
    if wl_class in ('feature', 'architecture-change'):
        required = {'bootstrap','plan','implement','review','test','handoff'}
    elif wl_class == 'hotfix':
        required = {'bootstrap','plan','implement','review','test'}
    elif wl_class == 'quick-win':
        # H1: quick-win has real required phases — not an empty set
        required = {'bootstrap','plan','implement'}
    elif wl_class == 'tiny-fix':
        # tiny-fix is exempt from gate ceremony (AGENTS.md §tiny-fix fast path)
        required = set()
    else:
        # H1: fail-closed for unknown/misspelled classification — treat as feature
        required = {'bootstrap','plan','implement','review','test','handoff'}
    missing_phases = required - gate_set
    if missing_phases:
        print(f'incomplete:{",".join(sorted(missing_phases))} (classification:{wl_class or "unknown"})')
        sys.exit(0)
# NOT READY reverse-edge check: if review_not_ready is still set (no subsequent review
# PASS cleared it), any test/handoff/ship in gates = re-review was skipped
if review_not_ready and any(g in ('test','handoff','ship') for g in gates):
    bad_next = next(g for g in gates if g in ('test','handoff','ship'))
    print(f'illegal:NOT_READY-review->{bad_next} (re-review skipped after NOT READY — implement→review required per review.md)')
    sys.exit(0)
# Progression check requires 2+ gates; tiny-fix has no required phase sequence
if len(gates) < 2 or wl_class == 'tiny-fix':
    print('ok')
    sys.exit(0)
for i in range(1, len(gates)):
    prev, curr = gates[i-1], gates[i]
    allowed = LEGAL.get(prev, [])
    if curr not in allowed:
        print(f'illegal:{prev}->{curr} (classification:{wl_class or "unknown"})')
        sys.exit(0)
# M10: stale-review check — if most recent implement follows most recent review,
# then test/handoff/ship without a new review = stale review violation
# (test.md §Step 5 reverse edge: implement-after-review MUST re-review before test)
# quick-win and tiny-fix treat review as optional — re-review is NOT required.
# Unknown/H1 fail-closed classifications follow feature rules, so M10 applies.
if wl_class not in ('quick-win', 'tiny-fix'):
    last_review_idx = max((i for i, g in enumerate(gates) if g == 'review'), default=-1)
    last_impl_idx   = max((i for i, g in enumerate(gates) if g == 'implement'), default=-1)
    if last_review_idx >= 0 and last_impl_idx > last_review_idx:
        post_impl = gates[last_impl_idx + 1:]
        if any(g in ('test', 'handoff', 'ship') for g in post_impl):
            bad_next = next(g for g in post_impl if g in ('test', 'handoff', 'ship'))
            print(f'illegal:implement-after-review->{bad_next} (stale review: implement occurred after last review PASS; re-review required)')
            sys.exit(0)
print('ok')
PYEOF
)
        gate_check="$("$PYTHON_BIN" -c "$_acx_gate_py" <<< "$wl_content" 2>/dev/null)"
        if [[ "$gate_check" == illegal:* ]]; then
          printf '  illegal gate progression in %s: %s\n' "$(basename "$wl")" "${gate_check#illegal:}"
          gate_progression_illegal=$((gate_progression_illegal + 1))
        elif [[ "$gate_check" == incomplete:* ]]; then
          printf '  incomplete gate receipts in %s: missing %s\n' "$(basename "$wl")" "${gate_check#incomplete:}"
          gate_progression_illegal=$((gate_progression_illegal + 1))
        fi
      else
        gate_progression_skipped=1
        # Bash-only fallback (M9): even without Python, catch ship receipts missing
        # minimum prerequisite gates (plan + implement). Cannot verify legal ordering
        # but can detect obvious bypasses. Increments gate_progression_illegal so FAIL
        # is recorded — a shipped log without plan/implement is always a violation.
        if printf '%s' "$wl_content" | grep -qiE 'Gate:[[:space:]]*ship[[:space:]]*\|[^|]*Verdict:[[:space:]]*PASS'; then
          has_plan=$(printf '%s' "$wl_content" | grep -ciE 'Gate:[[:space:]]*plan[[:space:]]*\|[^|]*Verdict:[[:space:]]*PASS') || true
          has_impl=$(printf '%s' "$wl_content" | grep -ciE 'Gate:[[:space:]]*implement[[:space:]]*\|[^|]*Verdict:[[:space:]]*PASS') || true
          if [[ "$has_plan" -eq 0 ]] || [[ "$has_impl" -eq 0 ]]; then
            printf '  [bash-fallback] shipped without plan/implement gate in %s\n' "$(basename "$wl")"
            gate_progression_illegal=$((gate_progression_illegal + 1))
          fi
        fi
      fi
    fi
    # Runtime section: ## Phase Summary
    if ! printf '%s' "$wl_content" | grep -q '^## Phase Summary'; then
      phase_summary_missing=$((phase_summary_missing + 1))
    fi
    # Sentinel marker discoverability — Work Log Phase Summary SHOULD contain
    # ⚡ ACX at least once so the AGENTS.md Sentinel Check has a persistent
    # audit trail (chat output is ephemeral). WARN-only — does not break ship.
    # Accept either the emoji form "⚡ ACX" or the plain "ACX" tag for
    # terminals that strip non-ASCII.
    if printf '%s' "$wl_content" | grep -q '^## Phase Summary' \
       && ! printf '%s' "$wl_content" | grep -qE '(⚡[[:space:]]?ACX|[[:space:]]ACX([[:space:]]|$))'; then
      sentinel_marker_missing=$((sentinel_marker_missing + 1))
    fi
    # Test Gate Results — engineering_guardrails.md §12.2 requires evidence be recorded
    # under "Test Gate Results" for feature/architecture-change work logs that have
    # reached the implement or later phase. WARN-only: converts §12.2 from honor-system
    # to auditable evidence requirement.
    # Parse classification from list form ("- Classification:") or table form ("| Classification |")
    if [[ -n "$PYTHON_BIN" ]]; then
      # Python via single-quoted heredoc -> variable (verbatim; no bash metachar parsing)
      _acx_wlclass_py=$(cat <<'PYEOF'
import re,sys
for l in sys.stdin:
    m=re.match(r'^-\s+\*{0,2}[Cc]lassification\*{0,2}\s*:\s*\x60?([a-zA-Z][\w-]*)',l)
    if not m: m=re.match(r'^\|\s*\*{0,2}[Cc]lassification\*{0,2}\s*\|\s*\x60?([a-zA-Z][\w-]*)',l)
    if m: print(m.group(1).lower()); break
PYEOF
)
      wl_class="$(printf '%s' "$wl_content" | "$PYTHON_BIN" -c "$_acx_wlclass_py" 2>/dev/null)"
    else
      # Python unavailable: list-form-only fallback
      wl_class="$(printf '%s' "$wl_content" | sed -n 's/^- \(**\)\?Classification\1\?:[[:space:]]*//p' | head -n 1 | tr -d '\r\`')"
    fi
    if [[ "$wl_class" == "feature" || "$wl_class" == "architecture-change" ]]; then
      if printf '%s' "$wl_content" | grep -q 'Gate: implement'; then
        if ! printf '%s' "$wl_content" | grep -qiE '^#+[[:space:]]+Test Gate Results'; then
          test_gate_results_missing=$((test_gate_results_missing + 1))
        fi
      fi
    fi
    # MEDIUM-1 (review PASS with UNPROVEN rows): check for review PASS receipt alongside
    # unresolved UNPROVEN table rows — review.md §Burden of Proof requires NOT READY in this case.
    # Direct approach: flag if review PASS co-exists with any UNPROVEN row not tagged [NEEDS_HUMAN].
    # (The prior ! grep -qvE condition was always false because header/gate lines don't match
    # the UNPROVEN pattern, causing grep -qvE to succeed and the check to be permanently skipped.)
    if printf '%s' "$wl_content" | grep -qiE 'Gate:[[:space:]]*review[[:space:]]*\|.*Verdict:[[:space:]]*PASS'; then
      unproven_untagged="$(printf '%s' "$wl_content" | grep '✗ UNPROVEN' | grep -v '\[NEEDS_HUMAN\]' | head -1)" || true
      if [[ -n "$unproven_untagged" ]]; then
        review_pass_with_unproven=$((review_pass_with_unproven + 1))
      fi
    fi
    # MEDIUM-3 (M5): evidence non-empty check for shipped feature/arch-change/quick-win logs.
    # The bootstrap placeholder "Pending: bootstrap only" is not real evidence.
    if [[ "$wl_class" == "feature" || "$wl_class" == "architecture-change" || "$wl_class" == "quick-win" ]]; then
      if printf '%s' "$wl_content" | grep -qiE 'Gate:[[:space:]]*ship[[:space:]]*\|.*Verdict:[[:space:]]*PASS'; then
        evidence_body="$(printf '%s' "$wl_content" | sed -n '/^## Evidence/,/^## /p' | tail -n +2 | grep -v '^## ' | grep -v '^$' | head -5)" || true
        if [[ -z "$evidence_body" || "$evidence_body" == *"Pending: bootstrap only"* ]]; then
          evidence_placeholder_only=$((evidence_placeholder_only + 1))
        fi
      fi
    fi
    # Current Phase consistency (HIGH-2): if a ship PASS receipt exists,
    # Current Phase should be 'ship'. Divergence means the header was not updated.
    if printf '%s' "$wl_content" | grep -qiE 'Gate:[[:space:]]*ship[[:space:]]*\|.*Verdict:[[:space:]]*PASS'; then
      cp_val="$(printf '%s' "$wl_content" | grep -m1 -iE '^-[[:space:]]*\*?\*?Current Phase\*?\*?:' \
        | sed 's/.*Current Phase[^:]*:[[:space:]]*//' | tr -d '`\r' | tr '[:upper:]' '[:lower:]' | xargs)" || true
      if [[ -n "$cp_val" && "$cp_val" != "ship" ]]; then
        current_phase_incoherent=$((current_phase_incoherent + 1))
      fi
      # Archival check (Item 1): if Current Phase is 'ship' and ship PASS receipt exists,
      # this Work Log should have been archived. Presence in work/ means /ship step 3 was skipped.
      if [[ -z "$cp_val" || "$cp_val" == "ship" ]]; then
        shipped_not_archived=$((shipped_not_archived + 1))
      fi
    fi
    # Finding 9 (HIGH): Reclassification state inconsistency — Drift Log records
    # "Reclassification:" but Classification header was never reset to CLASSIFIED,
    # leaving downstream agents with a stale classification tier.
    if printf '%s' "$wl_content" | grep -q '## Drift Log' \
       && printf '%s' "$wl_content" | grep -qiE '^\s*-\s+Reclassif'; then
      cls_hdr="$(printf '%s' "$wl_content" | grep -m1 -iE '^-[[:space:]]*\*?\*?Classification\*?\*?:' \
        | sed 's/.*Classification[^:]*:[[:space:]]*//' | tr -d '`\r' | tr '[:upper:]' '[:lower:]' | xargs)" || true
      if [[ -n "$cls_hdr" && "$cls_hdr" != "classified" ]]; then
        reclassify_header_not_reset=$((reclassify_header_not_reset + 1))
      fi
    fi
    # Finding 5 (MEDIUM): Handoff Resume Block completeness — prose rule (handoff.md §1a)
    # requires all sub-sections. Warn when ## Resume section exists but is missing
    # any of the mandatory headings: Read Map, Skip List, Context Snapshot.
    if printf '%s' "$wl_content" | grep -q '^## Resume'; then
      resume_body="$(printf '%s' "$wl_content" | sed -n '/^## Resume/,/^## /p')"
      missing_subsections=0
      for subsec in "Read Map" "Skip List" "Context Snapshot"; do
        if ! printf '%s' "$resume_body" | grep -qiE "^###[[:space:]]+${subsec}"; then
          missing_subsections=$((missing_subsections + 1))
        fi
      done
      if [[ "$missing_subsections" -gt 0 ]]; then
        handoff_resume_incomplete=$((handoff_resume_incomplete + 1))
      fi
    fi
    # Finding 13 (MEDIUM): hotfix fast-path evidence check — hotfix is exempt from
    # /handoff but MUST provide evidence. Warn when a hotfix reaches ship phase
    # but ## Evidence section is missing or contains only the bootstrap placeholder.
    if [[ "$wl_class" == "hotfix" ]]; then
      if printf '%s' "$wl_content" | grep -qiE 'Gate:[[:space:]]*ship[[:space:]]*\|.*Verdict:[[:space:]]*PASS'; then
        hotfix_evidence="$(printf '%s' "$wl_content" | sed -n '/^## Evidence/,/^## /p' | tail -n +2 | grep -v '^## ' | grep -v '^$' | head -5)" || true
        if [[ -z "$hotfix_evidence" || "$hotfix_evidence" == *"Pending: bootstrap only"* ]]; then
          hotfix_ship_no_evidence=$((hotfix_ship_no_evidence + 1))
        fi
      fi
    fi
    # Finding 14 (MEDIUM): ADR Coverage gap — for feature/architecture-change Work Logs,
    # bootstrap should have run the ADR Coverage Check and recorded the result (yes/skip)
    # in ## Drift Log. Missing record means the check was silently bypassed.
    if [[ "$wl_class" == "feature" || "$wl_class" == "architecture-change" ]]; then
      if printf '%s' "$wl_content" | grep -q 'Gate: plan\|Gate: implement'; then
        if ! printf '%s' "$wl_content" | grep -qiE 'ADR.*[Cc]overage|[Cc]overage.*ADR|adr.*check|no.*adr.*found'; then
          adr_coverage_undocumented=$((adr_coverage_undocumented + 1))
        fi
      fi
    fi
  done
  if [[ "$phase_field_missing" -gt 0 ]]; then
    record_result WARN "work logs missing Current Phase field: ${phase_field_missing}"
  elif [[ "$worklog_count" -gt 0 ]]; then
    record_result PASS "all active work logs have Current Phase field"
  fi
  if [[ "$checkpoint_missing" -gt 0 ]]; then
    record_result WARN "work logs missing Checkpoint SHA field: ${checkpoint_missing}"
  elif [[ "$worklog_count" -gt 0 ]]; then
    record_result PASS "all active work logs have Checkpoint SHA field"
  fi
  if [[ "$gate_evidence_missing" -gt 0 ]]; then
    record_result FAIL "work logs missing gate evidence receipts: ${gate_evidence_missing}"
  elif [[ "$worklog_count" -gt 0 ]] && [[ "$legacy_gate_evidence_missing" -eq 0 ]]; then
    record_result PASS "all active work logs have gate evidence receipts"
  fi
  if [[ "$legacy_gate_evidence_missing" -gt 0 ]]; then
    record_result WARN "legacy work logs missing gate evidence receipts: ${legacy_gate_evidence_missing} (created before ${WORKLOG_GATE_EVIDENCE_LEGACY_CUTOFF})"
  fi
  if [[ "$gate_progression_illegal" -gt 0 ]]; then
    record_result FAIL "work logs with illegal gate phase progression: ${gate_progression_illegal}"
  elif [[ "$gate_progression_skipped" -eq 1 ]]; then
    if [[ "$ACX_NO_PYTHON" -eq 1 ]]; then
      record_result SKIP "gate evidence phase progression -- python checks disabled (--no-python)"
    else
      record_result WARN "gate evidence phase progression -- python unavailable (install Python 3.9+ for full validation)"
    fi
  elif [[ "$worklog_count" -gt 0 ]] && [[ "$gate_evidence_missing" -eq 0 ]] && [[ "$legacy_gate_evidence_missing" -eq 0 ]]; then
    record_result PASS "gate evidence phase progression is legal"
  fi
  if [[ "$phase_summary_missing" -gt 0 ]]; then
    record_result WARN "work logs missing Phase Summary section: ${phase_summary_missing}"
  elif [[ "$worklog_count" -gt 0 ]]; then
    record_result PASS "all active work logs have Phase Summary section"
  fi
  if [[ "$sentinel_marker_missing" -gt 0 ]]; then
    record_result WARN "work logs missing sentinel marker (⚡ ACX) in Phase Summary: ${sentinel_marker_missing}"
  elif [[ "$worklog_count" -gt 0 ]] && [[ "$phase_summary_missing" -eq 0 ]]; then
    record_result PASS "all active work logs carry sentinel marker for audit trail"
  fi
  if [[ "$test_gate_results_missing" -gt 0 ]]; then
    record_result WARN "feature/architecture-change work logs missing Test Gate Results section (engineering_guardrails.md §12.2): ${test_gate_results_missing}"
  elif [[ "$worklog_count" -gt 0 ]]; then
    record_result PASS "test gate results evidence present in applicable work logs"
  fi
  if [[ "$current_phase_incoherent" -gt 0 ]]; then
    record_result WARN "work logs with ship PASS receipt but Current Phase != ship (header not updated): ${current_phase_incoherent}"
  elif [[ "$worklog_count" -gt 0 ]]; then
    record_result PASS "Current Phase field is consistent with last gate receipt in all work logs"
  fi
  if [[ "$shipped_not_archived" -gt 0 ]]; then
    record_result WARN "shipped work logs still in active work/ directory (archival incomplete — /ship step 3 skipped?): ${shipped_not_archived}"
  elif [[ "$worklog_count" -gt 0 ]]; then
    record_result PASS "no shipped work logs found in active work/ directory"
  fi
  if [[ "$evidence_placeholder_only" -gt 0 ]]; then
    record_result FAIL "feature/arch-change/quick-win shipped work logs with bootstrap-placeholder ## Evidence (NO EVIDENCE = NO SHIP per AGENTS.md §Delivery Gates): ${evidence_placeholder_only}"
  elif [[ "$worklog_count" -gt 0 ]]; then
    record_result PASS "shipped feature/arch-change work logs have non-placeholder Evidence sections"
  fi
  if [[ "$review_pass_with_unproven" -gt 0 ]]; then
    record_result WARN "work logs with review PASS receipt but unresolved UNPROVEN rows (receipt should be NOT READY per review.md §Burden of Proof): ${review_pass_with_unproven}"
  elif [[ "$worklog_count" -gt 0 ]]; then
    record_result PASS "no review PASS receipts with unresolved UNPROVEN rows detected"
  fi
  if [[ "$reclassify_header_not_reset" -gt 0 ]]; then
    record_result WARN "work logs with Reclassification in Drift Log but Classification header not reset to CLASSIFIED (implement.md §Mid-Execution Guard step c incomplete): ${reclassify_header_not_reset}"
  elif [[ "$worklog_count" -gt 0 ]]; then
    record_result PASS "no reclassification header inconsistency detected"
  fi
  if [[ "$handoff_resume_incomplete" -gt 0 ]]; then
    record_result WARN "work logs with ## Resume section missing required sub-sections (handoff.md §1a — Read Map, Skip List, Context Snapshot required): ${handoff_resume_incomplete}"
  elif [[ "$worklog_count" -gt 0 ]]; then
    record_result PASS "handoff Resume Blocks have required sub-sections where present"
  fi
  if [[ "$hotfix_ship_no_evidence" -gt 0 ]]; then
    record_result WARN "hotfix work logs shipped without ## Evidence (hotfix fast-path still requires diff + behavior verification per handoff.md §Trigger Conditions): ${hotfix_ship_no_evidence}"
  elif [[ "$worklog_count" -gt 0 ]]; then
    record_result PASS "hotfix shipped work logs carry evidence where present"
  fi
  if [[ "$adr_coverage_undocumented" -gt 0 ]]; then
    record_result WARN "feature/architecture-change work logs past plan phase with no ADR Coverage Check record in Drift Log (bootstrap.md §ADR Coverage Check result should be logged): ${adr_coverage_undocumented}"
  elif [[ "$worklog_count" -gt 0 ]]; then
    record_result PASS "ADR Coverage Check records present in applicable work logs"
  fi
  # Gate receipt schema validation (§4.5 structural check) — every pipe-format gate
  # receipt in ## Gate Evidence must include Verdict: and Classification: fields.
  # WARN not FAIL: archived Work Logs may predate this check; active logs with partial
  # receipts are a process gap, not a ship-blocking error.
  gate_schema_violations=0
  gate_schema_violation_list=""
  for wl in "$WORKLOG_DIR"/*.md; do
    [[ -f "$wl" ]] || continue
    wl_name="$(basename "$wl")"
    # Extract gate evidence section lines (pipe-format receipts starting with "- Gate:")
    while IFS= read -r receipt_line; do
      # Each receipt must contain Verdict: (case-insensitive) and Classification: (case-insensitive)
      if ! printf '%s' "$receipt_line" | grep -qiE '[Vv]erdict[[:space:]]*:'; then
        gate_schema_violations=$((gate_schema_violations + 1))
        gate_schema_violation_list="${gate_schema_violation_list}  malformed gate receipt (missing Verdict:) in ${wl_name}\n"
        break
      fi
      if ! printf '%s' "$receipt_line" | grep -qiE '[Cc]lassification[[:space:]]*:'; then
        gate_schema_violations=$((gate_schema_violations + 1))
        gate_schema_violation_list="${gate_schema_violation_list}  malformed gate receipt (missing Classification:) in ${wl_name}\n"
        break
      fi
    done < <(grep -iE '^\-[[:space:]]+[Gg]ate[[:space:]]*:' "$wl" 2>/dev/null || true)
  done
  if [[ "$gate_schema_violations" -gt 0 ]]; then
    record_result WARN "active work log gate receipts missing required fields (Verdict/Classification): ${gate_schema_violations}"
    printf '%b' "$gate_schema_violation_list"
  elif [[ "$worklog_count" -gt 0 ]]; then
    record_result PASS "all active work log gate receipts have required fields (gate/verdict/classification)"
  fi
  # Advisory lock staleness check — reads JSON fields per config.yaml §worklog_lock.
  # All JSON parsing and stale logic stays inside Python to avoid eval/injection.
  stale_locks=0
  lock_files_present=0
  for lockf in "$WORKLOG_DIR"/*.lock.json; do
    [[ -f "$lockf" ]] || continue
    lock_files_present=1
    if [[ -n "$PYTHON_BIN" ]]; then
      # Python via single-quoted heredoc -> variable (verbatim; no bash metachar parsing)
      _acx_stale_py=$(cat <<'PYEOF'
import json, sys, datetime
try:
    with open(sys.argv[1]) as f:
        d = json.load(f)
    ua = d.get('updated_at', '')
    tm = int(d.get('stale_timeout_minutes', 60))
    if not ua:
        print('unreadable')
        sys.exit(0)
    dt = datetime.datetime.fromisoformat(ua)
    now = datetime.datetime.now(dt.tzinfo or datetime.timezone.utc)
    age_min = (now - dt).total_seconds() / 60
    print('stale' if age_min > tm else 'fresh')
except Exception:
    print('unreadable')
PYEOF
)
      stale_verdict="$("$PYTHON_BIN" -c "$_acx_stale_py" "$lockf" 2>/dev/null)"
      case "$stale_verdict" in
        stale)
          printf '  stale advisory lock: %s\n' "$(basename "$lockf")"
          stale_locks=$((stale_locks + 1))
          ;;
        unreadable)
          printf '  unreadable advisory lock: %s\n' "$(basename "$lockf")"
          stale_locks=$((stale_locks + 1))
          ;;
      esac
    fi
  done
  if [[ "$stale_locks" -gt 0 ]]; then
    record_result WARN "stale advisory work log locks detected: ${stale_locks}"
  elif [[ "$lock_files_present" -eq 1 ]] && [[ -z "$PYTHON_BIN" ]]; then
    if [[ "$ACX_NO_PYTHON" -eq 1 ]]; then
      record_result SKIP "advisory lock staleness check -- python checks disabled (--no-python)"
    else
      record_result WARN "advisory lock staleness check -- python unavailable (install Python 3.9+ for full validation)"
    fi
  fi
else
  record_result SKIP "active work log directory not present"
fi

if [[ -f "$GUARD_CONTEXT_WRITE" ]]; then
  record_result PASS "guarded write capability installed"
else
  record_result SKIP "guard capability not installed"
fi

GUARD_RECEIPT="$ROOT/.agentcortex/context/.guard_receipt.json"
if [[ -f "$GUARD_RECEIPT" ]]; then
  record_result PASS "guard receipt present"
else
  record_result WARN "no guard receipt found at $GUARD_RECEIPT; guarded writes remain advisory"
fi

if [[ -f "$OPTIONAL_GUARD_HOOK" ]]; then
  record_result PASS "optional guard hook sample present"
else
  record_result WARN "optional guard hook sample is not present; guarded-write checks remain advisory only"
fi

# Work Log Phase Summary audit — pure bash, no Python hooks.
# Sentinel (⚡ ACX) and PreCompact enforcement is model self-attestation per
# AGENTS.md. Audit happens here at validate-time on archived Work Logs:
# every archived non-tiny-fix Work Log MUST have a non-empty `## Phase
# Summary` section (replaces the runtime PreCompact hook intent).
ARCHIVE_DIR="$ROOT/.agentcortex/context/archive"
phase_summary_violations=0
phase_summary_violation_list=""
if [[ -d "$ARCHIVE_DIR" ]]; then
  while IFS= read -r -d '' wl; do
    classification="$(grep -m1 -E '^- \*?\*?Classification\*?\*?:' "$wl" 2>/dev/null | sed -E 's/.*Classification[^:]*:\s*`?//; s/`.*//; s/\s*$//')" || true
    [[ "$classification" == "tiny-fix" ]] && continue
    summary_body="$(awk '/^## Phase Summary/{found=1; next} found && /^## /{exit} found{print}' "$wl" 2>/dev/null | tr -d '[:space:]')"
    if [[ -z "$summary_body" || "$summary_body" == "none" ]]; then
      phase_summary_violations=$((phase_summary_violations + 1))
      phase_summary_violation_list="${phase_summary_violation_list}  empty Phase Summary: ${wl#$ROOT/}\n"
    fi
  # Exclude ship-history-*.md (case-insensitive `-iname` for parity with the PS
  # `-notlike` filter): compacted ship-history archives are not Work Logs and
  # carry no `## Phase Summary` contract (#171).
  done < <(find "$ARCHIVE_DIR" -name '*.md' -not -name '.gitkeep*' -not -iname 'ship-history-*' -print0 2>/dev/null || true)
fi
if [[ "$phase_summary_violations" -gt 0 ]]; then
  record_result WARN "archived Work Logs with empty Phase Summary: ${phase_summary_violations}"
  printf '%b' "$phase_summary_violation_list"
else
  record_result PASS "archived Work Logs have non-empty Phase Summary (or none archived yet)"
fi

# M7: Gate completeness audit for archived Work Logs (bash-only, WARN — historical records).
# Checks that ship receipts are preceded by minimum required gates. WARN not FAIL
# because archives are immutable historical records; violations indicate past governance gaps.
archive_gate_violations=0
archive_gate_violation_list=""
if [[ -d "$ARCHIVE_DIR" ]]; then
  while IFS= read -r -d '' wl; do
    wl_content="$(cat "$wl" 2>/dev/null)"
    [[ -z "$wl_content" ]] && continue
    arc_class="$(printf '%s' "$wl_content" | grep -m1 -E '^- \*?\*?[Cc]lassification\*?\*?:' | sed -E 's/.*[Cc]lassification[^:]*:\s*`?//; s/`.*//; s/\s*$//' | tr '[:upper:]' '[:lower:]')" || true
    [[ "$arc_class" == "tiny-fix" ]] && continue
    if printf '%s' "$wl_content" | grep -qiE 'Gate:[[:space:]]*ship[[:space:]]*\|[^|]*Verdict:[[:space:]]*PASS'; then
      arc_has_plan=$(printf '%s' "$wl_content" | grep -ciE 'Gate:[[:space:]]*plan[[:space:]]*\|[^|]*Verdict:[[:space:]]*PASS') || true
      arc_has_impl=$(printf '%s' "$wl_content" | grep -ciE 'Gate:[[:space:]]*implement[[:space:]]*\|[^|]*Verdict:[[:space:]]*PASS') || true
      if [[ "$arc_has_plan" -eq 0 ]] || [[ "$arc_has_impl" -eq 0 ]]; then
        archive_gate_violations=$((archive_gate_violations + 1))
        archive_gate_violation_list="${archive_gate_violation_list}  archived gate bypass: ${wl#$ROOT/}\n"
      fi
    fi
  done < <(find "$ARCHIVE_DIR" -name '*.md' -not -name '.gitkeep*' -print0 2>/dev/null || true)
fi
if [[ "$archive_gate_violations" -gt 0 ]]; then
  record_result WARN "archived Work Logs with ship receipt but missing plan/implement gates (historical governance gap): ${archive_gate_violations}"
  printf '%b' "$archive_gate_violation_list"
else
  record_result PASS "archived Work Logs gate completeness ok (or none archived yet)"
fi

# Gate receipt schema validation for archived Work Logs — same §4.5 structural check.
# WARN only: archives are immutable historical records.
archive_gate_schema_violations=0
archive_gate_schema_violation_list=""
if [[ -d "$ARCHIVE_DIR" ]]; then
  while IFS= read -r -d '' wl; do
    wl_name="$(basename "$wl")"
    while IFS= read -r receipt_line; do
      if ! printf '%s' "$receipt_line" | grep -qiE '[Vv]erdict[[:space:]]*:'; then
        archive_gate_schema_violations=$((archive_gate_schema_violations + 1))
        archive_gate_schema_violation_list="${archive_gate_schema_violation_list}  malformed gate receipt (missing Verdict:) in ${wl_name}\n"
        break
      fi
      if ! printf '%s' "$receipt_line" | grep -qiE '[Cc]lassification[[:space:]]*:'; then
        archive_gate_schema_violations=$((archive_gate_schema_violations + 1))
        archive_gate_schema_violation_list="${archive_gate_schema_violation_list}  malformed gate receipt (missing Classification:) in ${wl_name}\n"
        break
      fi
    done < <(grep -iE '^\-[[:space:]]+[Gg]ate[[:space:]]*:' "$wl" 2>/dev/null || true)
  done < <(find "$ARCHIVE_DIR" -name '*.md' -not -name '.gitkeep*' -print0 2>/dev/null || true)
fi
if [[ "$archive_gate_schema_violations" -gt 0 ]]; then
  record_result WARN "archived Work Log gate receipts missing required fields (Verdict/Classification): ${archive_gate_schema_violations}"
  printf '%b' "$archive_gate_schema_violation_list"
else
  record_result PASS "archived Work Log gate receipts have required fields (or none archived yet)"
fi

# M8: Relative-link depth check for archived markdown files.
# Content copy-pasted from current_state.md (at depth 2) into archive/ (depth 3)
# keeps the original relative paths, which silently break one directory level deeper.
# Scan all archive/*.md for relative links (not http/https, not anchor-only #...) and
# verify the resolved target exists. WARN-only — historical archives are immutable.
if [[ -z "$PYTHON_BIN" ]]; then
  record_result SKIP "M8 archive relative-link check -- python unavailable"
elif [[ ! -d "$ARCHIVE_DIR" ]]; then
  record_result PASS "archived markdown files: no archive directory yet (fresh deploy)"
elif [[ -n "$PYTHON_BIN" ]] && [[ -d "$ARCHIVE_DIR" ]]; then
  archive_broken_links=0
  archive_broken_link_list=""
  while IFS= read -r -d '' arch_file; do
    # Python via single-quoted heredoc -> variable (verbatim; no bash metachar parsing)
    _acx_brokenlink_py=$(cat <<'PYEOF'
import re, sys
from pathlib import Path
f = Path(sys.argv[1])
try:
    text = f.read_text(encoding='utf-8', errors='replace')
except Exception:
    print(0)
    sys.exit(0)
# Match [label](target) where target is not http/https and not anchor-only
link_re = re.compile(r'\[(?:[^\]]*)\]\(([^)]+)\)')
count = 0
for m in link_re.finditer(text):
    tgt = m.group(1).strip()
    # Skip external URLs and pure anchors
    if tgt.startswith(('http://', 'https://')) or tgt.startswith('#'):
        continue
    # Strip inline anchor from path
    path_part = tgt.split('#')[0]
    if not path_part:
        continue
    resolved = (f.parent / path_part).resolve()
    if not resolved.exists():
        print(f'  broken relative link in {str(f)}: {tgt}')
        count += 1
# Print count as last line so caller reads from stdout (exit-code wraps at 256)
print(count)
PYEOF
)
    broken_output="$("$PYTHON_BIN" -c "$_acx_brokenlink_py" "$arch_file" 2>/dev/null)"
    file_count=$(printf '%s\n' "$broken_output" | tail -1)
    file_count=${file_count:-0}
    if [[ "$file_count" =~ ^[0-9]+$ ]] && [[ "$file_count" -gt 0 ]]; then
      archive_broken_links=$((archive_broken_links + file_count))
      diagnostic=$(printf '%s\n' "$broken_output" | head -n -1)
      [[ -n "$diagnostic" ]] && archive_broken_link_list="${archive_broken_link_list}${diagnostic}\n"
    fi
  done < <(find "$ARCHIVE_DIR" -maxdepth 2 -name '*.md' -not -name '.gitkeep*' -print0 2>/dev/null)
  if [[ "$archive_broken_links" -gt 0 ]]; then
    record_result WARN "archived markdown files contain broken relative links (depth mismatch — strip or fix links when archiving from current_state.md): ${archive_broken_links}"
    printf '%b' "$archive_broken_link_list"
  else
    record_result PASS "archived markdown files: no broken relative links detected"
  fi
fi

GITIGNORE="$ROOT/.gitignore"
if [[ -f "$GITIGNORE" ]]; then
  gitignore_errors=0
  for must_track in \
    '.agentcortex/context/current_state.md' \
    '.agentcortex/context/archive/' \
    '.agentcortex/specs/' \
    '.agentcortex/adr/' \
    'docs/specs/' \
    'docs/adr/'; do
    if grep -x -F -q -- "$must_track" "$GITIGNORE"; then
      printf '  .gitignore must NOT ignore persistent SSoT artifact: %s\n' "$must_track"
      gitignore_errors=$((gitignore_errors + 1))
    fi
  done
  if [[ "$gitignore_errors" -gt 0 ]]; then
    record_result FAIL ".gitignore blocks persistent SSoT artifacts"
  else
    record_result PASS ".gitignore preserves persistent SSoT artifacts"
  fi
else
  record_result PASS ".gitignore absent -- no persistent SSoT artifacts are ignored"
fi

# SSoT completeness checks — verify current_state.md indexes match disk reality
# Always run when current_state.md exists. Projects may legitimately have no ADRs
# (bootstrap allows skipping /app-init) but still own specs and backlog entries.
CURRENT_STATE="$ROOT/.agentcortex/context/current_state.md"
if [[ -f "$CURRENT_STATE" ]]; then
  cs_content="$(cat "$CURRENT_STATE" 2>/dev/null)" || { record_result WARN "cannot read current_state.md — skipping state checks"; }

  # ADR Index completeness
  # NOTE: feed awk via here-string, NOT `printf | awk`. awk's `exit` closes the
  # pipe early; with set -o pipefail the upstream printf's SIGPIPE (141) would
  # fail the whole script intermittently when $cs_content is large. <<< reads a
  # temp file, so early exit cannot break a pipe.
  adr_index_section="$(awk '/\*\*ADR Index\*\*:/{found=1; next} found && /^- \*\*/{exit} found{print}' <<<"$cs_content")"
  adr_missing_count=0
  adr_missing_list=""
  adr_phantom_count=0
  adr_phantom_list=""
  for adr_dir in "$ROOT/docs/adr" "$ROOT/.agentcortex/adr"; do
    if [[ -d "$adr_dir" ]]; then
      for adr_file in "$adr_dir"/ADR-*.md; do
        [[ -f "$adr_file" ]] || continue
        rel_path="${adr_file#$ROOT/}"
        if ! printf '%s' "$adr_index_section" | grep -qF "$rel_path"; then
          adr_missing_count=$((adr_missing_count + 1))
          adr_missing_list="$adr_missing_list  not indexed: $rel_path\n"
        fi
      done
    fi
  done
  # Reverse check: indexed ADR paths that no longer exist on disk
  while IFS= read -r indexed_adr; do
    [[ -z "$indexed_adr" ]] && continue
    if [[ ! -f "$ROOT/$indexed_adr" ]]; then
      adr_phantom_count=$((adr_phantom_count + 1))
      adr_phantom_list="$adr_phantom_list  phantom index entry: $indexed_adr\n"
    fi
  done < <(printf '%s' "$adr_index_section" | grep -oE '[^ ]+\.md' | grep -i 'ADR-')
  if [[ "$adr_missing_count" -gt 0 || "$adr_phantom_count" -gt 0 ]]; then
    adr_msg=""
    [[ "$adr_missing_count" -gt 0 ]] && adr_msg="${adr_missing_count} disk ADR(s) not in index"
    if [[ "$adr_phantom_count" -gt 0 ]]; then
      [[ -n "$adr_msg" ]] && adr_msg="$adr_msg; "
      adr_msg="${adr_msg}${adr_phantom_count} indexed ADR(s) not on disk"
    fi
    record_result FAIL "SSoT ADR Index completeness: $adr_msg"
    printf '%b' "$adr_missing_list"
    printf '%b' "$adr_phantom_list"
    echo "  fix: update ADR Index in .agentcortex/context/current_state.md via /ship"
  else
    record_result PASS "SSoT ADR Index completeness: all disk ADRs are indexed"
  fi

  # Spec Index completeness
  spec_index_section="$(awk '/\*\*Spec Index\*\*/{found=1; next} found && /^- \*\*/{exit} found{print}' <<<"$cs_content")"
  spec_missing_count=0
  spec_missing_list=""
  for spec_dir in "$ROOT/docs/specs" "$ROOT/.agentcortex/specs"; do
    if [[ -d "$spec_dir" ]]; then
      for spec_file in "$spec_dir"/*.md; do
        [[ -f "$spec_file" ]] || continue
        basename_spec="$(basename "$spec_file")"
        # Skip files starting with _
        [[ "$basename_spec" == _* ]] && continue
        # Skip files with status: draft in frontmatter
        if grep -qm1 '^status:[[:space:]]*draft' "$spec_file" 2>/dev/null; then
          continue
        fi
        rel_path="${spec_file#$ROOT/}"
        if ! printf '%s' "$spec_index_section" | grep -qF "$rel_path"; then
          spec_missing_count=$((spec_missing_count + 1))
          spec_missing_list="$spec_missing_list  not indexed: $rel_path\n"
        fi
      done
    fi
  done
  # Reverse check: indexed spec paths that no longer exist on disk
  spec_phantom_count=0
  spec_phantom_list=""
  while IFS= read -r indexed_spec; do
    [[ -z "$indexed_spec" ]] && continue
    if [[ ! -f "$ROOT/$indexed_spec" ]]; then
      spec_phantom_count=$((spec_phantom_count + 1))
      spec_phantom_list="$spec_phantom_list  phantom index entry: $indexed_spec\n"
    fi
  done < <(printf '%s' "$spec_index_section" | sed -n 's/.*\] \([^ ]*\.md\) .*/\1/p')
  if [[ "$spec_missing_count" -gt 0 || "$spec_phantom_count" -gt 0 ]]; then
    spec_msg=""
    [[ "$spec_missing_count" -gt 0 ]] && spec_msg="${spec_missing_count} non-draft spec(s) not in index"
    if [[ "$spec_phantom_count" -gt 0 ]]; then
      [[ -n "$spec_msg" ]] && spec_msg="$spec_msg; "
      spec_msg="${spec_msg}${spec_phantom_count} indexed spec(s) not on disk"
    fi
    record_result FAIL "SSoT Spec Index completeness: $spec_msg"
    printf '%b' "$spec_missing_list"
    printf '%b' "$spec_phantom_list"
    echo "  fix: update Spec Index in .agentcortex/context/current_state.md via /ship"
  else
    record_result PASS "SSoT Spec Index completeness: all non-draft specs are indexed"
  fi

  # Active Backlog consistency
  PRODUCT_BACKLOG="$ROOT/docs/specs/_product-backlog.md"
  if [[ -f "$PRODUCT_BACKLOG" ]]; then
    if printf '%s' "$cs_content" | grep -qE '^- \*\*Active Backlog\*\*:[[:space:]]*none'; then
      record_result FAIL 'SSoT Active Backlog consistency: _product-backlog.md exists but SSoT Active Backlog is "none"'
      echo '  fix: set Active Backlog to `docs/specs/_product-backlog.md` in current_state.md via /ship'
    else
      # Path-value mismatch check: SSoT must reference docs/specs/_product-backlog.md
      backlog_ref_actual="$(printf '%s' "$cs_content" | sed -n 's/^- \*\*Active Backlog\*\*:[[:space:]]*`\([^`]*\)`.*/\1/p')"
      if [[ -n "$backlog_ref_actual" && "$backlog_ref_actual" != "docs/specs/_product-backlog.md" ]]; then
        record_result FAIL "SSoT Active Backlog consistency: SSoT Active Backlog references '$backlog_ref_actual' but actual backlog is at docs/specs/_product-backlog.md"
        echo '  fix: set Active Backlog to `docs/specs/_product-backlog.md` in current_state.md via /ship'
      else
        record_result PASS "SSoT Active Backlog consistency: backlog file and SSoT are consistent"
      fi
    fi
  else
    # Reverse check: SSoT references a backlog file that doesn't exist
    backlog_ref="$(printf '%s' "$cs_content" | sed -n 's/^- \*\*Active Backlog\*\*:[[:space:]]*`\([^`]*\)`.*/\1/p')"
    if [[ -n "$backlog_ref" && ! -f "$ROOT/$backlog_ref" ]]; then
      record_result FAIL "SSoT Active Backlog consistency: SSoT references '$backlog_ref' but file does not exist"
      echo "  fix: update Active Backlog in current_state.md via /ship or create the missing file"
    else
      record_result PASS "SSoT Active Backlog consistency: no backlog file on disk"
    fi
  fi
else
  record_result WARN "SSoT completeness checks skipped: current_state.md not found"
fi

# Backlog Feature Inventory check (MEDIUM-2): spec-intake multi-feature decomposition gate
# requires a ## Feature Inventory section per AGENTS.md §Delivery Gates.
BACKLOG_FILE="$ROOT/docs/specs/_product-backlog.md"
if [[ -f "$BACKLOG_FILE" ]]; then
  if ! grep -qiE '^#+[[:space:]]+Feature Inventory' "$BACKLOG_FILE" 2>/dev/null; then
    record_result WARN "backlog missing Feature Inventory section: _product-backlog.md exists but has no '## Feature Inventory' heading -- spec-intake multi-feature decomposition gate may have been skipped"
  else
    record_result PASS "backlog Feature Inventory section present"
  fi
fi

# Backlog schema check: verify Kind/Labels/Priority columns present when backlog exists
if [[ -f "$BACKLOG_FILE" ]]; then
  backlog_header="$(grep -m1 '|.*Feature.*|' "$BACKLOG_FILE" 2>/dev/null || true)"
  missing_cols=()
  echo "$backlog_header" | grep -q 'Kind'     || missing_cols+=("Kind")
  echo "$backlog_header" | grep -q 'Labels'   || missing_cols+=("Labels")
  echo "$backlog_header" | grep -q 'Priority' || missing_cols+=("Priority")
  if [[ ${#missing_cols[@]} -eq 0 ]]; then
    record_result PASS "backlog schema: Kind/Labels/Priority columns present"

    # L-1: P0 ratio lint — warn if >20% of pending items are P0
    # NOTE: grep -c outputs "0" + exit 1 when no matches; `|| echo 0` then appends
    # another "0" → `total_pending="0\n0"` breaks `[[ ]]`. tr -d '\n' coalesces.
    total_pending=$(grep -c '| Pending' "$BACKLOG_FILE" 2>/dev/null | tr -d '\n' || echo 0)
    p0_pending=$(grep '| Pending' "$BACKLOG_FILE" 2>/dev/null | grep -c '| P0 |' | tr -d '\n' || echo 0)
    total_pending="${total_pending:-0}"
    p0_pending="${p0_pending:-0}"
    if [[ "$total_pending" -gt 4 && "$p0_pending" -gt 0 ]]; then
      p0_ratio=$(( p0_pending * 100 / total_pending ))
      if [[ "$p0_ratio" -gt 20 ]]; then
        record_result WARN "backlog P0 ratio: ${p0_pending}/${total_pending} pending items are P0 (${p0_ratio}% > 20% threshold — consider downgrading some)"
      else
        record_result PASS "backlog P0 ratio: ${p0_pending}/${total_pending} pending items are P0 (${p0_ratio}%)"
      fi
    fi

    # L-3: Kind distribution sanity — warn if all non-— rows have Kind=feature (no review-finding/hotfix-spawn ever written)
    if [[ "$total_pending" -gt 9 ]]; then
      kind_variety=$(grep '| Pending' "$BACKLOG_FILE" 2>/dev/null | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $4); print $4}' | grep -vE '^\s*(—)?\s*$' | sort -u | wc -l | tr -d '[:space:]')
      kind_variety=${kind_variety:-0}
      if [[ "$kind_variety" -eq 1 ]]; then
        record_result WARN "backlog Kind diversity: all assigned pending items share the same Kind value — review-finding and hotfix-spawn entries may not be reaching the backlog"
      else
        record_result PASS "backlog Kind diversity: ${kind_variety} distinct Kind values in use"
      fi
    fi

    # L-3b: schema-zero guard — L-3 silently PASSes when ALL pending items have Kind=—
    # (kind_variety=0 ≠ 1, so falls to the PASS branch without surfacing the empty schema).
    if [[ "$total_pending" -gt 5 ]]; then
      kind_assigned=$(grep '| Pending' "$BACKLOG_FILE" 2>/dev/null | awk -F'|' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $4); if ($4 != "—" && $4 != "") print}' | wc -l | tr -d '[:space:]')
      kind_assigned=${kind_assigned:-0}
      if [[ "$kind_assigned" -eq 0 ]]; then
        record_result WARN "backlog Kind schema-zero: all ${total_pending} pending items have Kind=— — populate Kind column to enable cluster routing and L-3 diversity checks"
      fi
    fi

    # L-2: label vocabulary drift — warn if distinct label count exceeds max_distinct_labels (default 15)
    distinct_labels=$(grep '| Pending\|In Progress' "$BACKLOG_FILE" 2>/dev/null | awk -F'|' '{print $5}' | tr ',' '\n' | sed 's/[[:space:]]//g' | grep -v '^—$' | grep -v '^$' | sort -u | wc -l | tr -d '[:space:]')
    distinct_labels=${distinct_labels:-0}
    if [[ "$distinct_labels" -gt 15 ]]; then
      record_result WARN "backlog label vocabulary: ${distinct_labels} distinct labels (>15) — possible drift across sessions; review and consolidate via /spec-intake"
    elif [[ "$distinct_labels" -gt 0 ]]; then
      record_result PASS "backlog label vocabulary: ${distinct_labels} distinct labels"
    fi

    # L-4: cluster-declined marker GC — warn if too many suppressions accumulated
    declined_count=$(grep -c 'cluster-declined:' "$BACKLOG_FILE" 2>/dev/null | tr -d '[:space:]') || true
    declined_count=${declined_count:-0}
    if [[ "$declined_count" -gt 5 ]]; then
      record_result WARN "backlog cluster-declined: ${declined_count} suppression markers (>5) — review expired/stale suppressions in _product-backlog.md ## Source Summary"
    elif [[ "$declined_count" -gt 0 ]]; then
      record_result PASS "backlog cluster-declined: ${declined_count} suppression marker(s)"
    fi
  else
    record_result WARN "backlog schema: missing column(s): ${missing_cols[*]}"
    echo "  fix: run /spec-intake to trigger merge-guard backfill, or add columns manually"
    echo "  manual fix: add columns to Feature Inventory header row and backfill existing rows with —"
  fi
fi

# Backlog structure validation (#18): frontmatter fields, structural columns, Status enum, spec links.
# Catches structural corruption that would break /spec-intake feature matching but is invisible
# to the existence-only checks above.
if [[ -f "$BACKLOG_FILE" ]]; then
  # (1) YAML frontmatter required fields: title, created, status
  backlog_fm="$(awk 'NR==1 && /^---[[:space:]]*$/ {infm=1; next} infm && /^---[[:space:]]*$/ {exit} infm {print}' "$BACKLOG_FILE")"
  fm_missing=()
  printf '%s\n' "$backlog_fm" | grep -qE '^title:'   || fm_missing+=("title")
  printf '%s\n' "$backlog_fm" | grep -qE '^created:' || fm_missing+=("created")
  printf '%s\n' "$backlog_fm" | grep -qE '^status:'  || fm_missing+=("status")
  if [[ ${#fm_missing[@]} -eq 0 ]]; then
    record_result PASS "backlog frontmatter: required fields (title, created, status) present"
  else
    record_result FAIL "backlog frontmatter: missing required field(s): ${fm_missing[*]}"
    echo "  fix: add the missing field(s) to the YAML frontmatter of _product-backlog.md"
  fi

  # (2) Feature Inventory structural columns: #, Status, Tier (complements Kind/Labels/Priority above)
  backlog_hdr="$(grep -m1 '|.*Feature.*|' "$BACKLOG_FILE" 2>/dev/null || true)"
  struct_missing=()
  echo "$backlog_hdr" | grep -qE '\|[[:space:]]*#[[:space:]]*\|' || struct_missing+=("#")
  echo "$backlog_hdr" | grep -q 'Status' || struct_missing+=("Status")
  echo "$backlog_hdr" | grep -q 'Tier'   || struct_missing+=("Tier")
  if [[ ${#struct_missing[@]} -eq 0 ]]; then
    record_result PASS "backlog structure: #/Status/Tier columns present"
  else
    record_result WARN "backlog structure: missing column(s): ${struct_missing[*]}"
  fi

  # (3) Status enum compliance: every numbered Feature Inventory row uses a known Status value.
  # The enum token is matched as an isolated `| <status> |` cell anywhere in the row rather than
  # by fixed column index — safe because no other column holds a bare enum word as an isolated
  # cell (Dependencies use —/#N/dates, Spec File holds paths, Feature holds prose).
  bad_status=""
  while IFS= read -r brow; do
    echo "$brow" | grep -qE '^\|[[:space:]]*[0-9]+[[:space:]]*\|' || continue
    if ! echo "$brow" | grep -qE '\|[[:space:]]*(Pending|In Progress|Shipped|Deferred|Cancelled)[[:space:]]*\|'; then
      bnum="$(echo "$brow" | sed -E 's/^\|[[:space:]]*([0-9]+).*/\1/')"
      bad_status="${bad_status} #${bnum}"
    fi
  done < "$BACKLOG_FILE"
  if [[ -n "$bad_status" ]]; then
    record_result FAIL "backlog Status enum: row(s)${bad_status} have a Status not in {Pending, In Progress, Shipped, Deferred, Cancelled}"
    echo "  fix: correct the Status cell to a valid enum value in _product-backlog.md"
  else
    record_result PASS "backlog Status enum: all Feature Inventory rows use valid Status values"
  fi

  # (4) Spec link existence: referenced docs/specs/*.md files should exist on disk
  missing_specs=""
  while IFS= read -r sref; do
    [[ -z "$sref" ]] && continue
    if [[ ! -f "$ROOT/$sref" ]]; then
      case " $missing_specs " in *" $sref "*) ;; *) missing_specs="${missing_specs} $sref";; esac
    fi
  done < <(grep -oE 'docs/specs/[A-Za-z0-9._/-]+\.md' "$BACKLOG_FILE" 2>/dev/null | sort -u)
  if [[ -n "$missing_specs" ]]; then
    record_result WARN "backlog spec links: referenced spec file(s) not found:${missing_specs} (pending features may not have specs yet)"
  else
    record_result PASS "backlog spec links: all referenced spec files exist"
  fi
fi

# Routing index governance split checks
ROUTING_INDEX="$WORKFLOWS_DIR/routing.md"
if [[ -f "$ROUTING_INDEX" ]]; then
  record_result PASS "routing index present at .agent/workflows/routing.md"
  check_contains_literal \
    "$ROUTING_INDEX" \
    'canonical: true' \
    "routing index declares canonical authority" \
    "routing index missing canonical authority marker"
  check_contains_literal \
    "$ROUTING_INDEX" \
    'AGENTS.md outranks' \
    "routing index acknowledges AGENTS.md precedence" \
    "routing index missing AGENTS.md precedence acknowledgment"
else
  record_result FAIL "routing index missing at .agent/workflows/routing.md"
fi
check_contains_literal \
  "$PROJECT_AGENTS_FILE" \
  '.agent/workflows/routing.md' \
  "AGENTS.md references routing index (authority handoff present)" \
  "AGENTS.md missing routing index reference (authority handoff absent)"
check_contains_literal \
  "$WORKFLOWS_DIR/commands.md" \
  '.agent/workflows/routing.md' \
  "commands.md points to canonical routing index" \
  "commands.md missing canonical routing index reference"

# Security scanning workflow presence check (AC-8 of ci-security-scanning spec)
# Only relevant for repos using GitHub Actions (skip for non-Actions repos)
SECURITY_WORKFLOW="$ROOT/.github/workflows/security.yml"
if [[ -d "$ROOT/.github/workflows" ]]; then
  if [[ -f "$SECURITY_WORKFLOW" ]]; then
    record_result PASS "security scanning workflow present at .github/workflows/security.yml"
  else
    record_result WARN "security scanning workflow absent — .github/workflows/security.yml not found (add SAST + secret detection + dependency audit to protect this repo)"
  fi
fi

# Document lifecycle bloat checks
GLOBAL_LESSONS_MAX="${GLOBAL_LESSONS_MAX:-20}"
if [[ -f "$CURRENT_STATE" ]]; then
  lessons_count="$(grep -c '^\- \[Category:' "$CURRENT_STATE" 2>/dev/null || true)"
  if [[ "$lessons_count" -gt "$GLOBAL_LESSONS_MAX" ]]; then
    record_result WARN "Global Lessons exceeds cap (${lessons_count} > ${GLOBAL_LESSONS_MAX}); run /retro to archive LOW-severity entries"
  elif [[ "$lessons_count" -gt 0 ]]; then
    record_result PASS "Global Lessons count within cap (${lessons_count}/${GLOBAL_LESSONS_MAX})"
  fi
fi

# Ship History pending-SHA guard: commit references must be resolved SHAs.
# "pending" is a valid placeholder only during the ship branch; after merge
# it must be replaced with the real SHA. Warn so CI surfaces the gap.
if [[ -f "$CURRENT_STATE" ]]; then
  pending_sha_count="$(grep -c '^- Commits: pending' "$CURRENT_STATE" 2>/dev/null | tr -d '\n' || echo 0)"
  pending_sha_count="${pending_sha_count:-0}"
  if [[ "$pending_sha_count" -gt 0 ]]; then
    record_result WARN "Ship History has ${pending_sha_count} unresolved 'pending' commit reference(s) — replace with real SHAs after merge"
  else
    record_result PASS "Ship History commit references are all resolved"
  fi
fi

# Stale _raw-intake check: if a backlog exists with all features Shipped/Cancelled
# but _raw-intake*.md files still linger, that's dead data.
if [[ -d "$ROOT/docs/specs" ]]; then
  stale_raw_intake=0
  for ri in "$ROOT"/docs/specs/_raw-intake*.md; do
    [[ -f "$ri" ]] || continue
    stale_raw_intake=$((stale_raw_intake + 1))
  done
  if [[ "$stale_raw_intake" -gt 0 ]]; then
    record_result WARN "stale _raw-intake files detected: ${stale_raw_intake} — /ship should clean these up"
  fi
fi

# Project spec template check (#172): detect a genuine downstream app that has
# run /app-init by the presence of its project-architecture ADR
# (docs/adr/ADR-00N-project-architecture.md, created by app-init.md §4). The
# framework's own governance ADRs (ADR-001-governance-friction-tuning, ..) do
# NOT match this pattern, so these app-init-derived checks never false-fire on
# the framework repo itself. This signal is deploy-independent, so it also
# covers fork/clone adopters (README §Additive Fork) that never run deploy.sh.
# If app-init ran but the template / Project Name is missing, WARN.
app_init_adr_count=0
for adr_dir in "$ROOT/docs/adr" "$ROOT/.agentcortex/adr"; do
  if [[ -d "$adr_dir" ]]; then
    for f in "$adr_dir"/*-project-architecture.md; do [[ -f "$f" ]] && app_init_adr_count=$((app_init_adr_count + 1)); done
  fi
done
if [[ "$app_init_adr_count" -gt 0 ]]; then
  has_project_template=0
  for tmpl in "$ROOT"/.agentcortex/templates/spec-app-feature-*.md; do
    [[ -f "$tmpl" ]] && has_project_template=1 && break
  done
  if [[ "$has_project_template" -eq 0 ]]; then
    record_result WARN "project spec template missing: docs/adr/ has ADR(s) but no .agentcortex/templates/spec-app-feature-<project>.md found — run /app-init to create one, or spec-intake will use the generic template"
  else
    record_result PASS "project spec template present alongside ADR(s)"
  fi
  # Round-15 Finding 1/10: Project Name SSoT presence check — if /app-init ran,
  # current_state.md must have a non-empty, non-placeholder Project Name field.
  cs_file="$ROOT/.agentcortex/context/current_state.md"
  if [[ -f "$cs_file" ]]; then
    proj_name="$(grep -m1 -i '\*\*Project Name\*\*:' "$cs_file" | sed 's/.*Project Name\*\*:[[:space:]]*//' | tr -d '\r' | xargs)" || true
    if [[ -z "$proj_name" || "$proj_name" == "(set by /app-init)" ]]; then
      record_result WARN "Project Name field absent or placeholder in current_state.md — /app-init has run (ADRs exist) but SSoT Project Name was not set; spec-intake will fall back to glob template resolution"
    else
      record_result PASS "SSoT Project Name is set: ${proj_name}"
    fi
  fi
fi

# Round-16 Finding 7: Domain Decisions entry cap — spec.md §8 hard cap is 10 entries.
# Each [DECISION], [TRADEOFF], or [CONSTRAINT] line counts toward the cap.
domain_decisions_exceeded=0
if [[ -d "$ROOT/docs/specs" ]]; then
  shopt -s nullglob
  for spec in "$ROOT/docs/specs"/*.md; do
    [[ -f "$spec" ]] || continue
    [[ "$(basename "$spec")" == ".gitkeep.md" ]] && continue
    if grep -q '^## Domain Decisions' "$spec"; then
      entry_count="$(awk '/^## Domain Decisions/{found=1;next} found && /^## /{exit} found && /\[(DECISION|TRADEOFF|CONSTRAINT)\]/{c++} END{print c+0}' "$spec")"
      if [[ "$entry_count" -gt 10 ]]; then
        printf '  spec Domain Decisions cap exceeded: %s (%d entries > 10)\n' "$(basename "$spec")" "$entry_count"
        domain_decisions_exceeded=$((domain_decisions_exceeded + 1))
      fi
    fi
  done
  shopt -u nullglob
fi
if [[ "$domain_decisions_exceeded" -gt 0 ]]; then
  record_result WARN "docs/specs/ files with Domain Decisions exceeding 10-entry cap (spec.md §8 — requires user acknowledgment): ${domain_decisions_exceeded}"
else
  spec_dd_count=0
  for f in "$ROOT/docs/specs"/*.md; do grep -q '^## Domain Decisions' "$f" 2>/dev/null && spec_dd_count=$((spec_dd_count + 1)); done
  [[ "$spec_dd_count" -gt 0 ]] && record_result PASS "all specs with Domain Decisions sections are within 10-entry cap"
fi

# Round-15 Finding 7: Spec frontmatter status validation — each docs/specs/*.md
# must have YAML frontmatter with a recognized 'status:' value.
VALID_SPEC_STATUSES="draft|frozen|shipped|cancelled|living"
spec_bad_status=0
spec_missing_frontmatter=0
if [[ -d "$ROOT/docs/specs" ]]; then
  shopt -s nullglob
  for spec in "$ROOT/docs/specs"/*.md; do
    [[ -f "$spec" ]] || continue
    # Skip .gitkeep.md placeholder files
    [[ "$(basename "$spec")" == ".gitkeep.md" ]] && continue
    # Skip underscore-prefixed meta/index files (_product-backlog*, _research-*):
    # not governed specs; they use their own lifecycle states (archive/research)
    # and are exempt from the spec-status enum, matching the `_*` skip convention
    # already used for the Spec Index completeness check above (#170).
    [[ "$(basename "$spec")" == _* ]] && continue
    # Check YAML frontmatter presence (first line must be ---)
    first_line="$(head -n1 "$spec" 2>/dev/null | tr -d '\r')"
    if [[ "$first_line" != "---" ]]; then
      spec_missing_frontmatter=$((spec_missing_frontmatter + 1))
      continue
    fi
    # Extract status: value from frontmatter
    status_val="$(awk '/^---/{if(n++) exit} /^status:/{print}' "$spec" | sed 's/status:[[:space:]]*//' | tr -d '\r' | xargs)"
    if [[ -z "$status_val" ]]; then
      spec_missing_frontmatter=$((spec_missing_frontmatter + 1))
    elif ! printf '%s' "$status_val" | grep -qE "^(${VALID_SPEC_STATUSES})$"; then
      spec_bad_status=$((spec_bad_status + 1))
    fi
  done
  shopt -u nullglob
fi
if [[ "$spec_missing_frontmatter" -gt 0 ]]; then
  record_result WARN "docs/specs/ files missing YAML frontmatter or status field: ${spec_missing_frontmatter} (engineering_guardrails.md §4.2 requires status: draft|frozen|shipped|cancelled)"
elif [[ "$spec_bad_status" -gt 0 ]]; then
  record_result WARN "docs/specs/ files with unrecognized status value: ${spec_bad_status} (valid: draft, frozen, shipped, cancelled, living)"
else
  # Only emit PASS when specs directory has files to check
  spec_file_count=0
  for f in "$ROOT/docs/specs"/*.md; do [[ -f "$f" ]] && spec_file_count=$((spec_file_count + 1)); done
  [[ "$spec_file_count" -gt 0 ]] && record_result PASS "all docs/specs/ files have valid status frontmatter"
fi

# ACX phase shim skill-existence check: for each .claude/agents/acx-*.md,
# verify that any skill name listed under skills: which maps to a .agent/skills/
# stub file actually has a SKILL.md body in .agents/skills/. Claude Code
# built-in skills (no corresponding stub file) are silently skipped.
AGENTS_DIR="$ROOT/.claude/agents"
if [[ -d "$AGENTS_DIR" ]]; then
  shim_skill_errors=0
  shim_count=0
  shopt -s nullglob
  for shim in "$AGENTS_DIR"/acx-*.md; do
    [[ -f "$shim" ]] || continue
    shim_count=$((shim_count + 1))
    in_frontmatter=0
    in_skills=0
    while IFS= read -r line; do
      line="${line%$'\r'}"
      [[ "$line" == "---" ]] && { in_frontmatter=$(( 1 - in_frontmatter )); in_skills=0; continue; }
      [[ "$in_frontmatter" -eq 0 ]] && break
      if [[ "$line" =~ ^skills: ]]; then in_skills=1; continue; fi
      if [[ "$in_skills" -eq 1 ]]; then
        if [[ "$line" =~ ^[[:space:]]+-[[:space:]]+(.+)$ ]]; then
          skill_name="${BASH_REMATCH[1]%$'\r'}"
          skill_dir="$ROOT/.agent/skills/$skill_name"
          if [[ -f "$skill_dir" ]]; then
            if [[ ! -f "$ROOT/.agents/skills/$skill_name/SKILL.md" ]]; then
              printf '  shim skill missing SKILL.md: %s (referenced in %s)\n' "$skill_name" "$(basename "$shim")"
              shim_skill_errors=$((shim_skill_errors + 1))
            fi
          fi
        elif [[ ! "$line" =~ ^[[:space:]] ]]; then
          in_skills=0
        fi
      fi
    done < "$shim"
  done
  shopt -u nullglob
  if [[ "$shim_count" -eq 0 ]]; then
    record_result SKIP "acx phase shim skill check -- no acx-*.md shims found in .claude/agents/"
  elif [[ "$shim_skill_errors" -gt 0 ]]; then
    record_result FAIL "acx phase shim skill references are broken: ${shim_skill_errors} missing SKILL.md"
  else
    record_result PASS "acx phase shim skill references are all valid (${shim_count} shims checked)"
  fi
else
  record_result SKIP "acx phase shim skill check -- .claude/agents/ not present"
fi

echo ""
printf 'Summary: pass=%s warn=%s fail=%s skip=%s\n' "$PASS_COUNT" "$WARN_COUNT" "$FAIL_COUNT" "$SKIP_COUNT"
if [[ "$FAIL_COUNT" -gt 0 ]]; then
  echo "Agentic OS integrity check failed"
  exit 1
fi

echo "Agentic OS integrity check passed"
