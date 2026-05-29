# Document Governance — Layer 2 Decision Log

> Append-only chronological entries. Never delete or modify existing entries.
> Each entry records a [DECISION] / [TRADEOFF] / [CONSTRAINT] from a shipped spec.
> See L1 Synthesis: [docs/architecture/document-governance.md](document-governance.md)

---

### [document-governance][2026-04-25][architecture-change/adr-002-lock-unification]
source_spec: docs/specs/lock-unification.md
source_adr: docs/adr/ADR-002-guarded-governance-writes.md
source_sha: <ship-commit-sha>

[DECISION] Replace path-restricted lock in `guard_context_write.py` with policy-driven allow-list (`.agent/config.yaml §guard_policy.protected_paths`). Preserves safety while expanding scope to all framework governance files (AGENTS.md, .agent/rules/**, .agent/workflows/**, docs/adr/**, docs/architecture/*.log.md, docs/specs/_product-backlog.md).

[DECISION] CI lint (`tools/lint_governed_writes.py`) enforces guard usage at PR time, not at runtime. Workflow authors using direct `open()` against governed paths get FAIL in CI; `# guard-exempt: <reason>` opt-out preserved with per-file exemption count tracking.

[DECISION] `lifecycle:` frontmatter contract for governance docs (audit/, guides/governance-*, adr/, architecture L1) — fields: {owner, review_cadence, review_trigger, supersedes, superseded_by}. Date-based grandfather: pre-2026-04-25 files WARN; newer FAIL. Closes meta-doc rot identified by Future-Proofing Skeptic in Phase A roundtable.

[TRADEOFF] Kept `guard_context_write.py` name vs renaming to `guard_write_any` — preserves muscle memory at the cost of slight name/scope mismatch. Pragmatist roundtable rejected the rename; downstream forks unaffected.

[TRADEOFF] Per-target receipt directory (`.guard_receipts/<sha[:16]>.json`) vs append-only JSONL — chose directory for O(1) latest-receipt lookup at the cost of inode-pressure risk at very high volume (bounded ~30-50 governance targets).

[TRADEOFF] Append-write serialization via per-target sidecar lock vs naive `O_APPEND` — Windows O_APPEND insufficient under thread concurrency, so we serialize via process-local `threading.Lock` + cross-process file lock. Cost: ~2 ms per append; benefit: cross-platform correctness.

[CONSTRAINT] Stdlib-only Python implementation. No new dependencies; YAML parsed via existing `_yaml_loader.load_data`; Windows liveness via `ctypes.windll.kernel32.OpenProcess`.

[CONSTRAINT] Backward compatibility for one full release via `guard_policy.legacy_receipt_mirror: true` (Phase 1 dual-write). Phase 2 callsite migration is post-ship; Phase 3 removes legacy mirror after one release runway.

[CONSTRAINT] `lock_group()` reserved API — single-path implementation in this ADR; multi-path `NotImplementedError` placeholder for ADR-003 D3 reverse-transition multi-file atomicity needs. Prevents future ADR from reinventing the lock primitive.

[CONSTRAINT] Capability-by-presence enforcement. Python checks (`lint_governed_writes.py`, `check_lifecycle_frontmatter.py`) gated by `run_python_check` in validate.sh — downstream projects without Python installed degrade to SKIP/WARN, never blocking CI.

### [document-governance][2026-05-29][feat/audit-chain-tamper-evidence]
source_spec: docs/specs/audit-chain-tamper-evidence.md
source_sha: 9c035887c83dad2e8095c1b2ae8cb49828642960

[DECISION] C1 tail-truncation detection uses git `origin/main` (merge-base) as an EXTERNAL append-only witness in validate.sh/.ps1, chosen over a forgeable in-repo anchor file — a same-commit-forgeable anchor is false-confidence theatre per the [enforcement][HIGH] Global Lesson.

[DECISION] C2 `migrate` fails closed (exit 2, no writes) on an existing-but-mismatched prev_sha, only filling genuinely-missing fields — removing the "run migrate to launder forged history" attack and aligning with ADR-003's documented migration intent.

[TRADEOFF] The git witness is tamper-EVIDENCE, not prevention: an attacker can still truncate + commit, but the removal of published audit lines becomes a visible diff against the merge-base baseline that must survive PR review. Accepted as the strongest dependency-free guarantee absent an external transparency log.

[CONSTRAINT] Future INDEX rotation (backlog #3) MUST re-anchor the witness baseline as a deliberate reviewed operation; until then origin/main's merge-base is a valid monotonic lower bound and the strict-prefix invariant holds.

[CONSTRAINT] The witness MUST degrade to WARN (never silent PASS) when git/origin/baseline is unavailable; and MUST CR-normalize + drop blank lines identically in bash (`tr -d '\r'` + `grep '.'`) and PowerShell (string-array read + `-ne ''`) so the two validators cannot disagree (Windows CRLF parity).
