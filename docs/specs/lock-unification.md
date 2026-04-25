---
status: frozen
frozen_date: 2026-04-25
title: "Guarded Governance Writes — Lock Unification + CI Lint + Lifecycle Frontmatter"
created: 2026-04-25
goal: "Implement ADR-002: extend guard_context_write.py to cover all governance file paths via policy-driven scope, add CI lint to enforce guard usage, and require lifecycle frontmatter on governance docs."
adr_ref: docs/adr/ADR-002-guarded-governance-writes.md
primary_domain: document-governance
secondary_domains: []
lifecycle:
  owner: "/govern-docs"
  review_cadence: on-event
  review_trigger: "When validate.sh adds new governance-write checks OR a regression slips through the lint OR a downstream fork hits a CI failure attributable to this spec"
  supersedes: none
  superseded_by: none
---

# Spec: Guarded Governance Writes

## 1. Objective

Implement ADR-002 in three coupled but independently testable sub-systems:
1. **D2.1** — generalize `guard_context_write.py` to write any policy-allowed path with append support, per-target receipts, configurable lock TTL, and process-liveness check
2. **D2.2** — `tools/lint_governed_writes.py` enforced by `validate.sh`/`validate.ps1` to catch direct file IO against governed paths
3. **D2.3** — `lifecycle:` frontmatter contract for governance docs, enforced by `tools/check_lifecycle_frontmatter.py`

End goal: **every governance file write either uses the guard or is explicitly exempted in code with a reason**, AND **every governance doc carries its own owner + review trigger**.

## 2. Acceptance Criteria

Each AC has a stable ID for spec-test traceability per `engineering_guardrails.md` §5.3 + `test.md §Spec-Test Traceability`.

### D2.1 — Lock generalization

- **AC-1** `.agent/config.yaml` contains `guard_policy.protected_paths` with the default 9-glob list from ADR §D1.
- **AC-2** `guard_context_write.py write` rejects targets that match no `protected_paths` glob with exit code 1 unless `--allow-outside` is passed AND `guard_policy.allow_outside_paths: true`.
- **AC-3** `guard_context_write.py write --mode append` writes a single line via `O_WRONLY|O_CREAT|O_APPEND`; raises if `--expected-sha` is also provided (programmer-error catch).
- **AC-4** Two concurrent `--mode append` invocations against the same target produce two non-interleaved lines (count == 2, every line is valid JSON when input is JSON).
- **AC-5** Per-target receipts written to `<receipt_dir>/<sha256(rel_posix)[:16]>.json`; legacy `.guard_receipt.json` mirror written when `legacy_receipt_mirror: true` (default Phase 1).
- **AC-6** `clear_stale_lock` reads `pid` from the lock JSON; if `pid` exists and is alive (verified via `os.kill(pid, 0)` on POSIX, `OpenProcess` on Windows), do NOT clear regardless of age. If pid is dead OR age > `lock_stale_seconds`, clear.
- **AC-7** `lock_stale_seconds` honors `.agent/config.yaml §guard_policy.lock_stale_seconds` (default 900); env var `ACX_GUARD_STALE_SECONDS` still overrides per existing behavior.
- **AC-8** `lock_group(paths)` exposed as importable function; single-path invocation works identically to existing `file_lock`; multi-path stub raises `NotImplementedError("multi-path lock_group reserved for ADR-003 D3")`.

### D2.2 — CI lint

- **AC-9** `tools/lint_governed_writes.py --root .` scans tracked `.py`, `.sh`, `.ps1`, `.js`, `.ts`, `.mjs`, `.cjs` files (skips `.md`).
- **AC-10** Detects write patterns: Python `open(..., 'w'|'a'|'x')`, `Path(..).write_text/_bytes`, `shutil.copyfile/move`; Shell `> path`, `>> path`, `tee`; PowerShell `Set-Content`/`Out-File`/`Add-Content`; JS/TS `fs.writeFile(Sync)?`/`fs.appendFile(Sync)?`/`fs.createWriteStream`.
- **AC-11** Path literal is statically resolved against `guard_policy.protected_paths`; matched literal → FAIL, variable path that cannot be resolved → WARN (not FAIL).
- **AC-12** `# guard-exempt: <reason>` (or `// guard-exempt:` / `<!-- guard-exempt: -->`) on same line or immediately preceding line suppresses FAIL for that occurrence; lint report still counts the exemption.
- **AC-13** `validate.sh` invokes the lint via `record_result` block; FAIL contributes to summary `fail=` count and exits non-zero.
- **AC-14** `validate.ps1` mirror addition produces identical FAIL/PASS classification for the same input on Windows.

### D2.3 — Lifecycle frontmatter

- **AC-15** `tools/check_lifecycle_frontmatter.py --root .` scans `docs/audit/*.md`, `docs/guides/governance-*.md`, `docs/adr/*.md`, `docs/architecture/*.md` (excluding `*.log.md`).
- **AC-16** For each file, parses YAML frontmatter; validates presence of `lifecycle.owner`, `lifecycle.review_cadence`, `lifecycle.review_trigger`, `lifecycle.supersedes`, `lifecycle.superseded_by`.
- **AC-17** `review_cadence` ∈ `{quarterly, biannual, annual, on-event}`; other values → FAIL.
- **AC-18** Files dated before 2026-04-25 (per frontmatter `date:` or `created:` field; if absent, fall back to git `log --diff-filter=A --reverse` first-commit date) → grandfathered: missing fields produce WARN not FAIL.
- **AC-19** Files dated 2026-04-25 or later → missing/invalid fields produce FAIL.
- **AC-20** `validate.sh` and `validate.ps1` integration: `record_result` block invokes the checker; FAIL propagates.

### Cross-cutting

- **AC-21** Existing `guard_context_write` callers (every site that runs in `validate.sh` today) remain green with identical exit codes.
- **AC-22** Phase 1 dual-write: every successful guarded write produces BOTH the new per-target receipt AND the legacy `.guard_receipt.json`. Validator paths can read either.
- **AC-23** `docs/audit/governance-lifecycle-2026-04-25.md` updated to include `lifecycle:` frontmatter (lead-by-example).
- **AC-24** `AGENTS.md §Document Lifecycle Governance` adds a 1-paragraph pointer to the new ownership matrix doc.
- **AC-25** `docs/guides/governance-doc-lifecycle-matrix.md` created with the Architect's Part 2 matrix + 3 explicit ownership gaps marked as Spec Seeds.

## 3. Non-Goals

- D1 (AI Context Trust Boundary) and D3 (State Machine reverse transition) — separate ADRs.
- Backporting `lifecycle:` frontmatter to ALL existing docs — only the 4 governance categories listed in AC-15.
- Multi-path `lock_group` semantics — stub only; full implementation is ADR-003 D3.
- Migrating existing callers to new modes — Phase 2 is post-ship work, NOT part of this spec.
- Renaming `guard_context_write` to `guard_write_any` — Pragmatist roundtable rejected the rename.
- Linting markdown for `open(...)` — too noisy; deferred indefinitely.

## Domain Decisions

(Cross-references ADR-002. Spec consolidates here for consistency.)

- [DECISION] Replace path-restricted lock with policy-driven allow-list (ADR §D1)
- [DECISION] CI lint enforces guard usage at PR time (ADR §D2)
- [DECISION] `lifecycle:` frontmatter as the meta-governance mechanism (ADR §D3)
- [TRADEOFF] Keep `guard_context_write` name vs rename — keep name to preserve muscle memory
- [TRADEOFF] Per-target receipt directory vs append-only JSONL — chose directory for O(1) latest-receipt lookup
- [CONSTRAINT] Stdlib-only Python; no new dependencies
- [CONSTRAINT] Backward compat for one full release via `legacy_receipt_mirror`
- [CONSTRAINT] Liveness check works on Windows + POSIX without external libs

## 5. Test Strategy

Per `test-classify.md` for `architecture-change`: Full + Beast Mode adversarial.

### Unit tests (pytest under `tests/guard/` — directory created by spec)

- AC-1: load config, verify default `protected_paths` content
- AC-2: target outside policy → exit 1; with `--allow-outside` + config flag → succeeds
- AC-3: append mode rejects `--expected-sha`; replace mode requires it
- AC-5: receipt files appear at correct paths in both new + legacy locations
- AC-7: env override + config + default precedence
- AC-8: `lock_group([single_path])` works; `lock_group([a, b])` raises NotImplementedError
- AC-10/11: lint detects each pattern; resolves path literals; WARN for variables
- AC-12: exemption marker suppresses FAIL but counts in report
- AC-16/17/19: frontmatter parser accepts valid; rejects invalid `review_cadence`

### Race / concurrency tests (subprocess `Popen × 2`)

- AC-4: 50 concurrent appends to single target — exactly 50 lines, every line valid JSON
- AC-6: hold lock with sleeping process; second process verifies pid alive → does NOT clear; kill first → second succeeds after age threshold
- AC-21: regression — existing call sites (ssot update, archive index, retro lessons) all green

### Cross-platform (CI matrix)

- AC-14: Windows-latest validate.ps1 produces identical FAIL/PASS classification as ubuntu-latest validate.sh
- AC-6 liveness check on both POSIX (`os.kill(pid, 0)`) and Windows (`OpenProcess`)

### Adversarial (Beast Mode per `red-team-adversarial`)

- TOCTOU symlink swap mid-flight — resolved-path check rejects
- Path traversal `../../etc/passwd` in `--path` — rejected with exit 1
- Lint exemption marker abuse: bulk-add `# guard-exempt: x` to suppress real violations → reviewer-flagged via per-file exemption count threshold (>5 per file = WARN aggregated)
- Concurrent `/retro` lessons append — AC-4 covers; verify Global Lessons gain count matches retros run

## 6. Risks & Rollback

- **Risk**: lint false positives block dev velocity → mitigated by exemption marker + per-file threshold + WARN-not-FAIL for variable paths
- **Risk**: liveness check ↑ syscall cost per lock acquisition → measured: `os.kill(pid, 0)` is microseconds; negligible
- **Risk**: per-target receipts inflate inode count → bounded by number of distinct governance targets (~30-50 in mature project); negligible
- **Rollback**: feature-flag `legacy_receipt_mirror` allows reverting receipt strategy via config-only change; `git revert` reverts the entire ADR-002 implementation as a single coherent unit (3 commits matching D1/D2/D3)

## 7. Spec Drift Prevention

- Per `engineering_guardrails.md` §5.3: any deviation from this spec during /implement → STOP and surface
- Per `engineering_guardrails.md` §4.2: this spec freezes at /plan entry; updates require unfreeze approval
