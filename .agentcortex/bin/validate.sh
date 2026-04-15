#!/usr/bin/env bash
set -uo pipefail

# --- CLI flags ---
ACX_NO_PYTHON=0
for _arg in "$@"; do
  case "$_arg" in
    --no-python) ACX_NO_PYTHON=1 ;;
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
  output="$("$PYTHON_BIN" "$script" "$@" 2>&1)"
  local status=$?
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
  "$WORKFLOWS_DIR/new-feature.md"
  "$WORKFLOWS_DIR/medium-feature.md"
  "$WORKFLOWS_DIR/small-fix.md"
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
  "$WORKFLOWS_DIR/claude-cli.md"
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

check_file_group "required framework files present" "${required_files[@]}"

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
  'agentcortex\bin\deploy' \
  "deploy_brain.cmd references canonical deploy entrypoint" \
  "deploy_brain.cmd missing canonical deploy reference"

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
      '從「流程驅動」進化到「自我管理」的專業級 AI Agent 核心架構。' \
      "README_zh-TW.md encoding looks healthy" \
      "README_zh-TW.md appears mojibaked or re-encoded"
  fi
  if [[ -f "$ROOT/README.md" ]]; then
    check_contains_literal \
      "$ROOT/README.md" \
      'governance-first operating system for AI coding agents' \
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
WORKLOG_GATE_EVIDENCE_LEGACY_CUTOFF="${WORKLOG_GATE_EVIDENCE_LEGACY_CUTOFF:-2026-03-25}"
WORKLOG_DIR="$ROOT/.agentcortex/context/work"
if [[ -d "$WORKLOG_DIR" ]]; then
  worklog_warnings=0
  worklog_count=0
  for wl in "$WORKLOG_DIR"/*.md; do
    [[ -f "$wl" ]] || continue
    worklog_count=$((worklog_count + 1))
    wl_lines="$(wc -l < "$wl")"
    wl_kb="$(( $(wc -c < "$wl") / 1024 ))"
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
  if [[ "$worklog_count" -gt "$ACTIVE_WORKLOG_WARN_THRESHOLD" ]]; then
    record_result WARN "active work log count exceeds hygiene threshold (${worklog_count} > ${ACTIVE_WORKLOG_WARN_THRESHOLD})"
  else
    record_result PASS "active work log count is within hygiene threshold"
  fi
  # Work Log integrity marker check — detect truncated writes from interrupted sessions
  worklog_truncated=0
  for wl in "$WORKLOG_DIR"/*.md; do
    [[ -f "$wl" ]] || continue
    wl_content="$(cat "$wl" 2>/dev/null)"
    # A well-formed work log must have at least a Branch header and one ## section.
    # Accept both the current "- Branch:" header and any legacy bolded variant.
    if ! printf '%s' "$wl_content" | grep -Eq '^- (\*\*Branch\*\*|Branch):' || \
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
  phase_summary_missing=0
  for wl in "$WORKLOG_DIR"/*.md; do
    [[ -f "$wl" ]] || continue
    wl_content="$(cat "$wl" 2>/dev/null)"
    created_date="$(printf '%s' "$wl_content" | sed -n 's/^- \*\*Created Date\*\*:[[:space:]]*//p' | head -n 1 | tr -d '\r')"
    legacy_gate_evidence=0
    if [[ -n "$created_date" ]] && [[ "$created_date" < "$WORKLOG_GATE_EVIDENCE_LEGACY_CUTOFF" ]]; then
      legacy_gate_evidence=1
    fi
    # Header field: Current Phase
    if ! printf '%s' "$wl_content" | grep -qE '^- (`Current Phase`|Current Phase):'; then
      phase_field_missing=$((phase_field_missing + 1))
    fi
    # Header field: Checkpoint SHA
    if ! printf '%s' "$wl_content" | grep -qE '^- (`Checkpoint SHA`|Checkpoint SHA):'; then
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
    elif ! printf '%s' "$wl_content" | grep -q '^- Gate:.*Verdict:'; then
      if [[ "$legacy_gate_evidence" -eq 1 ]]; then
        legacy_gate_evidence_missing=$((legacy_gate_evidence_missing + 1))
      else
        gate_evidence_missing=$((gate_evidence_missing + 1))
      fi
    else
      # Parse gate receipts and verify phase progression
      if [[ -n "${py_cmd:-}" ]] || { py_cmd="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)" && [[ -n "$py_cmd" ]]; }; then
        gate_check="$("$py_cmd" -c "
import sys, re
LEGAL = {
    'bootstrap': ['plan'],
    'plan':      ['implement'],
    'implement': ['review','test','ship'],
    'review':    ['implement','test','ship'],
    'test':      ['handoff','ship','implement'],
    'handoff':   ['ship','retro'],
    'ship':      [],
}
lines = sys.stdin.read().splitlines()
gates = []
for l in lines:
    m = re.match(r'^- Gate:\s*(\w+)\s*\|', l)
    if m:
        gates.append(m.group(1))
if len(gates) < 2:
    print('ok')
    sys.exit(0)
for i in range(1, len(gates)):
    prev, curr = gates[i-1], gates[i]
    allowed = LEGAL.get(prev, [])
    if curr not in allowed:
        print(f'illegal:{prev}->{curr}')
        sys.exit(0)
print('ok')
" <<< "$wl_content" 2>/dev/null)"
        if [[ "$gate_check" == illegal:* ]]; then
          printf '  illegal gate progression in %s: %s\n' "$(basename "$wl")" "${gate_check#illegal:}"
          gate_progression_illegal=$((gate_progression_illegal + 1))
        fi
      fi
    fi
    # Runtime section: ## Phase Summary
    if ! printf '%s' "$wl_content" | grep -q '^## Phase Summary'; then
      phase_summary_missing=$((phase_summary_missing + 1))
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
  elif [[ "$worklog_count" -gt 0 ]] && [[ "$gate_evidence_missing" -eq 0 ]] && [[ "$legacy_gate_evidence_missing" -eq 0 ]]; then
    record_result PASS "gate evidence phase progression is legal"
  fi
  if [[ "$phase_summary_missing" -gt 0 ]]; then
    record_result WARN "work logs missing Phase Summary section: ${phase_summary_missing}"
  elif [[ "$worklog_count" -gt 0 ]]; then
    record_result PASS "all active work logs have Phase Summary section"
  fi
  # Advisory lock staleness check — reads JSON fields per config.yaml §worklog_lock.
  # All JSON parsing and stale logic stays inside Python to avoid eval/injection.
  stale_locks=0
  py_cmd="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)"
  for lockf in "$WORKLOG_DIR"/*.lock.json; do
    [[ -f "$lockf" ]] || continue
    if [[ -n "$py_cmd" ]]; then
      stale_verdict="$("$py_cmd" -c "
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
" "$lockf" 2>/dev/null)"
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
  cs_content="$(cat "$CURRENT_STATE")"

  # ADR Index completeness
  adr_index_section="$(printf '%s' "$cs_content" | awk '/\*\*ADR Index\*\*:/{found=1; next} found && /^- \*\*/{exit} found{print}')"
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
  spec_index_section="$(printf '%s' "$cs_content" | awk '/\*\*Spec Index\*\*/{found=1; next} found && /^- \*\*/{exit} found{print}')"
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

echo ""
printf 'Summary: pass=%s warn=%s fail=%s skip=%s\n' "$PASS_COUNT" "$WARN_COUNT" "$FAIL_COUNT" "$SKIP_COUNT"
if [[ "$FAIL_COUNT" -gt 0 ]]; then
  echo "Agentic OS integrity check failed"
  exit 1
fi

echo "Agentic OS integrity check passed"
