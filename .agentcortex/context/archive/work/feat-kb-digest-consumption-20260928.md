# Work Log overflow: feat/kb-digest-consumption

## Phase Summary

- Compaction overflow (2026-09-28, /handoff §6) of the still-active log `.agentcortex/context/work/feat-kb-digest-consumption.md`; moved verbatim below.

## Moved: Phase Summary (Session 1 + Session 2 pre-review fix)

- bootstrap: read AGENTS.md, CLAUDE.md, SSoT, repo-gotchas, ADR-009/010, the three shipped KB specs. Classified `feature` (workflow contract change + ADR amendment + spec). Shipped specs are immutable (spec-intake §8b) → new EXTENDS spec + ADR-009 record Amendment.
- plan: AC-1..AC-7 in `docs/specs/kb-seam-anchor-neutrality.md`. Constraint: lifecycle ceiling headroom was 512 tokens, so `bootstrap.md` edits trimmed to net +336 chars.
- implement (coordinator addendum mid-implement): digest missing/unreadable → read the page; KB root git repo not on clean main/master → `(WARN: KB not on clean main)` on the record + a visible line, honor-system, no tool (validator never resolves the KB path; no doctor tool exists).
- implement: `bootstrap.md §1b` (integer schema_version additive, header-only, visible UNREADABLE line) and `§3.6` `kb-consult` row (digest + KB-declared anchors, BYO fallback); ADR-009 inline corrections + Amendment; adopter guide; `.example`; CHANGELOG `[Unreleased]`.
- implement (Session 2 fix, pre-review verification): blind sim showed an `llms.txt`-only BYO KB resolves UNREADABLE under §1b ("still no integer `schema_version`" was not scoped to JSON entrypoints) — breaks AC-5. Pre-existing on main (control arm read the old text the same way). Fix: scope the schema check + failure clause to JSON entrypoints, add `markdown index: readable=OK`; net −5 lifecycle tokens (trimmed "bootstrap", "is", "behavior unchanged"). Spec AC-1 scoped to match. Read-before-write: bootstrap.md read in full at bootstrap (§1b bullet L120 is the only change site).

## Moved: Drift Log (Session 1)

- Skipped bootstrap `Last Verified` SSoT refresh: the write would add an unrelated tracked diff to `current_state.md` in a branch the owner will review; left for the owner's session.
- Gate receipts for bootstrap/plan/implement were written together at 2026-09-28T07:11:14Z (read from the clock when the log was created, after implement finished), not at each phase end.
- CHANGELOG: the repo has no prior `[Unreleased]` section (entries are written at release cut); added one because the owner asked for it.

## Moved: Review Feedback (round 1)

- S2 acx-reviewer, primary-adjudicated. Do-now: F1 (own receipt, log size), F3 grep-not-load, F4 page fallback/anchor miss, F6 own-repo root, F2/F5/F7/F9/F10c-e docs. Close: F8 (explicit §1b line; 3/3 sims emitted), F10a/b LOW, F10f (pointer trimmed), RT1 (page authoritative), RT2 (= KB-authored page `path` class; no-guard is owner decision). Backlog: RT3 kb_version format, approx_tokens-vs-routed-order.

## Moved: Drift Log (Session 2, early)

- S2 vs note: CHANGELOG untouched on disk (add at /ship); S1 `Downstream-Capabilities: none` but this checkout has a dogfood declaration.

## Moved: Phase Summary (review r1/r2) + Review Feedback (r2)

- review (S2): NOT READY — F1 own receipt chain + log size; F3/F4/F6 §1b/§3.6 wording; F2/F5/F7/F9/F10 doc accuracy — routed back to implement.
- implement (S2 re-entry): review fixes applied (see Review Feedback); no scope change.
- review r2: NOT READY (primary; fresh reviewer said READY + LOWs) — spec AC-3b wording must change before freeze, guide `--show-toplevel` check never fires on a relative path — routed back to implement.
- r1 adjudication moved to overflow. r2 (fresh acx-reviewer, READY + LOWs): do-now #2 regex spacing, #3/#4/#8 guide git + PS parity, #5 spec wording, #6 relative-path phrase, #7 pointer `*seam*`, #10 backlog #217 wording, RT stale-digest → accepted risk (ADR + Known Risk). Close: #1 template slot (= r1 F8; owner call, ~+18 tok), #9 (row ladder pre-existing).

## Moved: Drift Log (S2) + review r3 lines

- Session 2 takeover (2026-09-28T10:44Z): Owner `claude-code-subagent-kbseam` → `KbWen` per Resume + user instruction; prior session ended, lock was `missing` → created. Resumed at implement; next /review.
- S2: removed its own `Gate: implement` receipt of 11:09:12Z — implement→implement is an illegal edge (validator); the S2 fix sat inside the still-open implement phase (no review receipt existed yet).
- review r3: NOT READY (primary; reviewer READY + LOWs) — own r2 regressions: `*seam*` glob hits adopter specs, PS snippet prints whole minified file, "any spacing" claim misses `" :`. Routed back to implement.
- r1/r2 adjudication in overflow. r3 (fresh delta reviewer, READY): do-now F1 regex `"schema_version"\s*:\s*<int>` (bootstrap + guide + ADR/spec), F2 PS `-LiteralPath` + `.Matches.Value`, F3 `k*seam*`, F5/F7 backlog wording. Close: F6 (§1b prescribes no command), guide:166 topic names (pre-existing).

## Moved: compaction pass 3 (Task Description, Known Risk, Red Team originals)

Make the ADR-009 KB seam KB-neutral: section anchors come from the KB's `_meta.digest.anchors` (digest sha-checked), `schema_version` is additive-only with a header-only check, a declared-but-UNREADABLE KB shows one visible bootstrap line, and `${ACX_KB_PATH}` is optional with a literal path recommended. Owner-adjudicated scope; not re-debated.
- All new consult behavior is honor-system (no validator can check which section an agent read). Mitigation: labeled as such in the ADR amendment table.
- Stale digest (RT r2): page edited without regenerating outputs → row + digest stale together, digest used. Accepted, recorded in ADR-009 Amendment A (KB CI's job).
- Privacy: `archive/` is TRACKED and /ship moves this log there → no absolute path / real `kb_version` (S2 scrubbed; `git grep` staged tree before commit).
- 2026-09-28 /review r1–r4: 0 CRITICAL/HIGH. MEDIUM: stale digest (accepted, ADR-009 A), kb_version echo (#217, pre-existing, widened), digest path containment (= page `path` class, owner no-guard decision). LOW: git in KB dir (fsmonitor needs pre-planted config).

## Moved: Review Feedback (r4)

- r4 (READY) closed: L1 "(any spacing)" qualifies prose; L2 StrictMode rare; L3/L4 pre-existing (narrowed); L5 JSON keys case-sensitive.

## Moved: Test skeleton (AC map, adversarial cases)

- Test Files: `tests/ci/`, `tests/guard/`, `.agentcortex/tests/` (CI paths, unchanged); behavioral sims = scratchpad `kbsim.py` + fixtures (not committed; spec Out-of-scope rejects fixture-KB tests).
- AC map: AC-1 sims 1/2/4 + regex ×3 formats · AC-2 sims 3/5 · AC-3 kbsim + sim 1 · AC-3b sims 4/6 + guide git run · AC-4 grep · AC-5 sim 2 · AC-6 reviews r1–r4 · AC-7 suite + validate ×2 + lifecycle.
- Adversarial (run): missing entrypoint, off-main KB, in-project folder, compact / `" :` JSON, BYO md → all as designed.

## Moved: compaction pass 6 originals

- /review r1–r4: none. `scan_credentials.py` on 5 changed files → clean; no absolute path / real fingerprint in diff or overflow; docs-only, no dependency change.
- Lifecycle headroom 97 (354,903 / 355,000). Rollback: revert the squash commit (docs/rule text only; no validator/schema change).
- Test Files: `tests/ci/`, `tests/guard/`, `.agentcortex/tests/` (CI paths); sims: scratchpad kbsim.py + fixtures (not committed; fixture-KB tests out of scope per spec). AC map + adversarial cases: overflow.
ADR-009 KB seam made KB-neutral: KB-declared digest anchors (sha-checked), additive `schema_version`, visible UNREADABLE line, optional `${ACX_KB_PATH}`. Owner-adjudicated scope.
- S1 bootstrap/plan/implement; S2 pre-review fix (BYO md index); review r1–r3 NOT READY → fixes (detail: overflow).

## Moved: Session 1 Resume (superseded at /handoff; redacted)

- **Handoff**: implemented by a KB-side session (2026-09-28) that has ENDED. The receiving session takes ownership: update `Owner`/`Session` in the header (no live lock exists; lock timeout is 60 min). Nothing is committed yet.
- **Why (owner-approved roundtable, 4 experts + tenth man)**: (1) KB wiring stays project-level explicit opt-in in the gitignored private file — absent = zero reads, zero notices; (2) the KB now publishes per-standard digests (`outputs/digest/<slug>.md`: summary + risks section + checklist section, a fraction of a page) and declares anchor strings in `digest.anchors` — frameworks must NOT hard-code any KB's headings; digest missing/empty/sha-mismatch → read the page; (3) `schema_version` is additive: any int is accepted, never reject a higher one; (4) `ACX_KB_PATH` = KB clone ROOT, expanded only when written as `${ACX_KB_PATH}`, never a silent override; default to literal paths; (5) declared-but-unreadable → one visible line + Work Log, never a gate; KB clone off clean main → WARN only. Rejected: MCP server, machine-level default, user-level skill, auto-discovery.
- **KB side is merged**: local clone `<KB clone root (see private downstream-capabilities.yaml)>` is on clean `main` (schema N, digests present). Manifest top-level `digest` == index line-1 `_meta.digest`; non-standard index rows have NO `digest` field.
- **Privacy (open-source repo)**: never commit absolute paths, real `kb_version` values, or private KB content. This Work Log is gitignored, so the path above is fine here only.
- **State**: original repo folder `agentic-os` (moved back from a temporary worktree on 2026-09-28 at the owner's request; diff verified identical), branch `feat/kb-digest-consumption` from origin/main `2002052`. Changed: `.agent/workflows/bootstrap.md` (§1b, §3.6 kb-consult), `docs/adr/ADR-009-*` (Amendment A–E), new `docs/specs/kb-seam-anchor-neutrality.md` (draft, EXTENDS shipped seam spec), `connecting-a-knowledge-base.md`, `downstream-capabilities.example.yaml`. CHANGELOG intentionally untouched (repo writes it at /ship).
- **Already verified (independent reviewer: PASS with notes → all 7 notes fixed)**: `validate.sh` pass=116 warn=5 fail=0 (5 WARN pre-existing: archive receipts ×2 kinds, backlog tag count, cross-branch backlog link, MUST-without-eval); lifecycle/baseline/capabilities tests 95 passed; example + two real configs `validate_downstream_capabilities.py` → gate-safe; token total 354,918 / 355k cap (only 82 left — do not grow workflow text without trimming).
- **Re-verify independently before shipping (don't trust this note)**:
  1. `git -C . diff origin/main --stat` and read the diff against the decision above; grep the diff for local paths, the user name, and 12-hex values.
  2. `bash .agentcortex/bin/validate.sh` (or `pwsh .agentcortex/bin/validate.ps1`) → fail=0; confirm WARNs are the pre-existing ones.
  3. `python -m pytest .agentcortex/tests -m "not slow_governance" -q` (Windows Git Bash timeouts are known noise; rerun failures serially).
  4. Simulation against the real KB: from `<KB clone root (see private downstream-capabilities.yaml)>/outputs/manifest.json` read the first ~40 lines and regex `"schema_version": <int>` (expect an int); load manifest top-level `digest` and index line-1 `_meta.digest` → must be equal; take the data/DB `task_routing` entry → its first slug; grep its index row → open `digest`, first line must contain `sha <row.sha>`; section under `anchors.risks` ≈1.3K tokens (/plan, /implement), under `anchors.checklist` ≈0.4K (/review); a playbook row must have no `digest` key.
  5. Negative sims: (a) BYO KB with only `llms.txt` → still consumable (no digest path); (b) entrypoint pointing at a missing file → UNREADABLE + one visible line, no gate; (c) KB clone on a non-main branch → `(WARN: KB not on clean main)` only.
- **Remaining**: /review → /test → /handoff → /ship per this repo's rules; at /ship: ADR Index "amended" note, Spec Index entry for the new spec, SSoT `Last Verified`, CHANGELOG entry. Ask the owner before raising any token cap.
