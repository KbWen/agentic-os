---
status: proposed
date: 2026-04-25
classification: architecture-change
primary_domain: document-governance
deciders: "@kbwen + Claude Opus 4.7 (1M context) + 3-expert roundtable (Red Team / Subtraction / External Critic with WebFetch citations)"
applies_to:
  - ".agentcortex/context/archive/INDEX.jsonl"
  - ".agentcortex/tools/append_chain_entry.py"
  - ".agentcortex/tools/check_audit_chain.py"
  - ".agentcortex/bin/validate.sh"
  - ".agentcortex/bin/validate.ps1"
lifecycle:
  owner: "/adr"
  review_cadence: on-event
  review_trigger: "When the chain check fires on a real tamper attempt, OR when extending the chain to a second log surface (Drift Log, Gate Evidence, Global Lessons), OR when a different chain primitive is needed (e.g., Merkle tree if entry count exceeds 100K)"
  supersedes: none
  superseded_by: none
---

# ADR-003: Hash-Chained Tamper-Evident Audit Log

## Context

The Phase A audit (PR #70) and the 10th-man critique of the ADR-002 ship session (PR #73 retro Lesson L4) converged on a single structural diagnosis: every governance "MUST" rule that depends on agent self-attestation is honor-system theatre. PR #75 closes the Sentinel ⚡ ACX gap with an external observer hook. PR #74 closes the AC-1 ADR-coverage check. The remaining structural gap, identified independently by the External Critic sub-agent (citing Crosby & Wallach USENIX 2009 + transparency.dev), is that the framework's audit trails — `INDEX.jsonl` archive index, Drift Log entries, Gate Evidence, Global Lessons — are plain markdown / JSONL files. An agent (or compromised session) can silently rewrite history. **ADR-002 closed concurrent overwrite (file locking). ADR-003 closes retroactive tampering (hash chaining).**

Per Lesson L3 (`current_state.md` §Global Lessons 2026-04-25), this ADR adopts strict 1-decision discipline. The decision below covers ONE log surface (`INDEX.jsonl`); further chain adoption (Drift Log, Gate Evidence, Global Lessons) is explicit follow-up work, not bundled here.

### Evidence Sources (Verified)

- [Crosby & Wallach, USENIX Security 2009 — "Efficient Data Structures for Tamper-Evident Logging"](https://static.usenix.org/event/sec09/tech/full_papers/crosby.pdf): hash-chained append-only logs allow O(log N) inclusion proofs; tampering or reordering is cryptographically detectable.
- [Certificate Transparency / transparency.dev](https://transparency.dev/): Merkle-tree productionization of the same primitive at planetary scale.
- External Critic Insight #3 in this session's roundtable identified hash chains as the framework's "single most embarrassing gap" — solved-since-1999, productionized-since-2013, this framework doesn't even do it for its own Drift Log.

---

## Decision: Hash-chain `INDEX.jsonl` archive entries

Each entry in `.agentcortex/context/archive/INDEX.jsonl` carries a `prev_sha` field naming the sha256[:8] of the canonical-form previous entry. The first (genesis) entry uses `prev_sha: "GENESIS"`. A new validator walks the chain; any break is a CI FAIL.

**Rules:**

- **Canonical form**: each entry is serialized as `json.dumps(entry, sort_keys=True, ensure_ascii=False)` BEFORE hashing, EXCLUDING the entry's own `prev_sha` field. This makes the hash deterministic and order-stable across re-serializations.
- **Append helper**: `.agentcortex/tools/append_chain_entry.py` — single way to append. Reads the file's last line, extracts its canonical form (re-serializing without `prev_sha`), computes sha256[:8], adds `prev_sha` to the new entry, writes via `O_APPEND` for kernel-atomic single-line append. Reuses the per-target lock pattern from `guard_context_write.py` for cross-platform safety.
- **Validator**: `.agentcortex/tools/check_audit_chain.py` — walks each line in target file, recomputes the chain, FAIL on any mismatch, PASS on full chain integrity.
- **Migration of existing entries**: a one-time `--migrate` flag forward-computes the chain over existing entries (entries before this ADR ships have no `prev_sha`; the migration assigns them retroactively, accepting that pre-migration tampering is undetectable but post-migration is). The genesis entry gets `prev_sha: "GENESIS"`.
- **Validate.sh integration**: new `record_result` block calling `check_audit_chain.py` against `INDEX.jsonl`; FAIL propagates.

### Rationale

The chain is the simplest tamper-evident primitive that:
1. Adds **no new dependency** (sha256 is stdlib).
2. Handles **append-only growth** without rebalancing (Merkle tree is overkill at < 1000 entries).
3. **Compose-able** — once `append_chain_entry.py` exists, applying it to other logs (Drift Log, Gate Evidence, Global Lessons) is a per-log retro-fit, not a new mechanism.
4. **Visible to humans** — `prev_sha: "abcd1234"` is a normal JSON field anyone can grep.

### Rejected Alternatives

- **Merkle tree (transparency.dev style)**: O(log N) inclusion proof is overkill at our scale; adds complexity (root hash storage, sibling computation) without proportional benefit until the log exceeds ~10K entries.
- **HMAC with shared secret**: requires secret distribution; secret leakage = chain becomes forgeable. Hash chain provides tamper-EVIDENCE without authenticity (which we don't need — agents are on the trusted machine, the threat is silent rewriting, not impersonation).
- **Git as audit log**: already used for source code; INDEX.jsonl conceptually predates and survives multiple branch lifecycles, so coupling it to git history would create circular dependencies during rebase / cherry-pick.

### Affected Files

| File | Change |
|---|---|
| `.agentcortex/tools/append_chain_entry.py` | NEW (~80 LOC) |
| `.agentcortex/tools/check_audit_chain.py` | NEW (~70 LOC) |
| `.agentcortex/bin/validate.sh` | +1 `record_result` block (~5 LOC) |
| `.agentcortex/bin/validate.ps1` | mirror addition (~5 LOC) |
| `.agentcortex/context/archive/INDEX.jsonl` | one-time migration: each existing entry gets `prev_sha` field via `append_chain_entry.py --migrate` |

---

## Consequences

### Positive

- **Tamper-evidence**: any retroactive edit to `INDEX.jsonl` breaks the chain at the edited line forward. CI catches it.
- **Composable primitive**: same `append_chain_entry.py` will retro-fit Drift Log, Gate Evidence, Global Lessons in follow-up PRs without re-inventing the chain.
- **External-source-grounded**: addresses the External Critic's "most embarrassing gap" — closes a 17-year-old known pattern that this framework had ignored.

### Negative

- **One-time migration of existing entries** — entries before this ADR ships have no chain ancestor. Migration assigns retroactive `prev_sha`, accepting that pre-migration tampering is undetectable.
- **Append helper must be used** — direct `open(..., 'a')` to INDEX.jsonl bypasses the chain. Mitigated by ADR-002 D2.2 lint (already in PR #72): `lint_governed_writes.py` flags direct writes to governed paths; `INDEX.jsonl` would be added to the protected_paths glob.

### Neutral

- **No new dependency** — sha256 stdlib only.
- **Performance** — append is still O(1); validation is O(N) over all entries; at < 100 entries today, both are sub-millisecond.

---

## Implementation Plan

Follows `architecture-change` flow. Single decision, so no D3.1/D3.2/D3.3 sub-decisions (Lesson L3 discipline).

1. **/spec** — `docs/specs/hash-chained-audit-log.md` (signed off; this ADR is the contract)
2. **/plan** — Target Files + Steps + Risk + AC Coverage
3. **/implement** — TDD: helper + validator + migration in one commit
4. **/review** — Burden of Proof + Security Scan + adversarial test (try to tamper a line, verify validator catches it)
5. **/test** — chain-integrity test, tamper-detection test, migration test, validate.sh integration
6. **/handoff** — Resume + Read Map
7. **/ship** — SSoT update (ADR Index + Spec Index), L2 Domain Doc append (`docs/architecture/document-governance.log.md`), spec → shipped, archive Work Log

## Out of Scope (explicit follow-ups)

- **Drift Log chain** (markdown, per-Work Log) — separate PR after this lands; pattern is the same but requires defining canonical form for markdown lines.
- **Gate Evidence chain** — same.
- **Global Lessons chain** — same; smaller surface than Drift Log.
- **Merkle tree upgrade** — defer until INDEX entry count > 10K.
- **Validate.sh check that violations.jsonl (Sentinel hook output) is empty** — orthogonal; that's PR #75's follow-up.

## References

- Phase A audit: `docs/audit/governance-lifecycle-2026-04-25.md` §0.1 (External Critic Insight #3)
- Retro Lesson L4: `current_state.md` §Global Lessons 2026-04-25 (honor-system rules without external observer = theatre)
- Precedent ADRs: ADR-001 (friction tuning), ADR-002 (concurrent-write locking — this ADR is the retroactive-write counterpart)
- External: Crosby & Wallach 2009 — Efficient Data Structures for Tamper-Evident Logging; transparency.dev

## Domain Decisions

- [DECISION] Hash-chain (sha256[:8]) chosen over Merkle tree for simplicity; upgrade-path documented.
- [TRADEOFF] Migration assigns retroactive `prev_sha` to existing entries — pre-migration tampering undetectable; post-migration detectable.
- [CONSTRAINT] Stdlib only; no new dependency.
- [CONSTRAINT] Single log surface (INDEX.jsonl) in this ADR; chain-to-other-logs is explicit follow-up (Lesson L3 — 1 decision per ADR).
- [CONSTRAINT] Append helper MUST be used; lint-enforced via existing `lint_governed_writes.py` after `INDEX.jsonl` is added to `guard_policy.protected_paths`.
