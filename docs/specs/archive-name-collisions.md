---
status: frozen
created: 2026-10-06
classification: feature
primary_domain: document-governance
backlog: 186
signal_tier: T1
---

# Archive Name Collisions: the Directory Is the Type

## Goal

Make every archive consumer honor the rule the workflows already state: a file
in the archive **root** (`.agentcortex/context/archive/`) is a final Work Log
written by `/ship §3`; a file under `archive/work/` is a compaction fragment
written by `/handoff §6`. Two validator checks cross that boundary today, and
the workflows leave same-day name collisions undefined. This spec closes the
verified false PASSes, defines collision naming, and resolves backlog #186.

Owner choices recorded 2026-10-06 in chat (Option 2; legacy files moved;
D4 edited in place; `--N-` collision name). Work Log `## Decisions` D-1..D-4.

## Evidence and Root Cause

Baseline: `main` at `9905177b9850416a34b1a5f1b1c6db213ea2134c`. Line anchors
describe this baseline only.

1. **D4 masks a missing final log.** `validate.sh:455` / `validate.ps1:524`
   accept an INDEX.jsonl `log` if `archive/<log>` **or** `archive/work/<log>`
   exists. A fragment written on ship day has the final log's basename (11 of
   194 entries today). Reproduced on a scratch copy of the archive: delete root
   `fix-gate-evidence-tooling-20260926.md`, keep the same-named fragment → D4
   still `ok:194`; delete both → `missing:...`.
2. **D4 sh twin reports PASS when its check did not run.** `validate.sh:465-467`
   default to PASS and only switch on `missing:*`, so a child that prints
   `error` or nothing yields "all present on disk (error checked)". The ps1
   twin WARNs (`validate.ps1:541-546`). With no Python, neither twin emits a
   D4 line at all (`validate.sh:435`, `validate.ps1:498`).
3. **#186 is recursion, not naming.** The archived-Work-Log Phase-Summary scan
   is recursive (`validate.sh:2220` `find` without `-maxdepth`,
   `validate.ps1:2081` `-Recurse`), so fragments are audited as Work Logs.
   `handoff.md:151` works around it by asking fragments to carry a Phase
   Summary. `check_decision_disposition.py:274` already scans the root only.
4. **Same-day collisions are undefined and have happened.** `/ship §3`
   (`ship.md:203`) claims the date suffix prevents a reused key from
   overwriting its prior archive; that is false for a same-day reship. Two
   ships on `main` on 2026-06-15 produced an improvised `claude-main-20260615.md`;
   two same-day compactions produced `codex-research-main-20260619-2.md` / `-3.md`
   in one case and an append into one fragment in another. No data loss was
   observed. Git Bash (coreutils 8.32) `mv` overwrites silently with exit 0, and
   `mv -n` refuses but also exits 0, so an exit code cannot reveal a collision.
5. **Two legacy final logs live under `archive/work/`.** INDEX lines 1–2
   (`fix-40-validate-missing-workflow-files-20260417.md`,
   `architecture-change-adr-002-lock-unification.md`) predate the root-archive
   wording (#106, 2026-05-22). Both have a non-empty Phase Summary, well-formed
   receipts and no relative links, and are already read by the recursive M7 and
   gate-schema scans.

## Acceptance Criteria

- **AC-1 (D4 root-only).** In both twins, D4 resolves each INDEX `log` value
  as `archive/<log>` only. A value carrying an explicit `work/` prefix still
  resolves through that join. An entry missing at root whose basename exists
  under `archive/work/` produces a WARN that names it and says it belongs in
  the archive root; an entry found nowhere keeps the existing dangling WARN.
  Verified by a test that is red on the baseline (same-name fragment, root
  missing → no WARN today) on sh and on ps1.
- **AC-2 (D4 tells the truth when it cannot run).** sh records WARN when the
  child output is neither `ok:*` nor a recognized finding (parity with ps1).
  Both twins record SKIP when INDEX.jsonl exists and Python is unavailable. D4
  still emits exactly one native result call per twin, so
  `tests/ci/validator_native_baseline.json` counts are unchanged and only
  justification #5 is reworded. Verified by tests (child failure → WARN on sh;
  `--no-python` → SKIP line) and the native-check ratchet test.
- **AC-3 (twins cannot drift).** The Python embedded in the two D4 twins is
  byte-identical after extraction; a test asserts it.
- **AC-4 (legacy entries).** The 2 legacy files are moved with `git mv` into
  the archive root, content unchanged (blob SHAs identical before and after).
  No INDEX line changes. On this repo D4 reports PASS for all 194 entries.
- **AC-5 (Phase-Summary scan root-only, #186).** Both twins scan only the
  archive root (`-maxdepth 1` / no `-Recurse`). A fragment under
  `archive/work/` without `## Phase Summary` raises no WARN (test red on the
  baseline). `handoff.md:151` (the fragment-needs-a-Phase-Summary workaround)
  is deleted and the duplicate step number fixed.
- **AC-6 (compaction appends).** `handoff.md §6` step 2 and
  `token-governance.md §7` say the fragment is appended to, created if absent,
  never overwritten. The literal `<worklog-key>-<YYYYMMDD>` stays in all three
  archive-contract files (archive-contract check stays PASS).
- **AC-7 (ship collision rule).** `ship.md §3` replaces the false date-suffix
  claim with: never overwrite an existing archive (with the `mv`/`mv -n` exit-0
  hazard named); if the target exists, use `<worklog-key>--2-<YYYYMMDD>.md`
  (then `--3-`, …); INDEX `log` records the actual filename.
- **AC-8 (INDEX append guard).** `append_chain_entry.py append` rejects, with a
  nonzero exit and nothing written, an entry whose `log` value already appears
  in INDEX.jsonl; the error message states the `--N-` remedy. Entries without a
  `log` field are unaffected; existing duplicates in the chain are not
  re-checked. Verified by a unit test red on the baseline.
- **AC-9 (token budget).** The lifecycle aggregate measured by
  `analyze_token_lifecycle.py` stays ≤ the existing 355,000 ceiling, which is
  not raised (baseline 354,868).
- **AC-10 (no regression).** Both validators on the final tree report the same
  pass/warn/fail/skip counts as each other, with no new WARN or FAIL against
  the baseline; the full CI suite is green on the PR.

## Non-goals

- Renaming compaction fragments, or any existing archive file other than the
  2 legacy moves in AC-4.
- Editing, backfilling or annotating INDEX.jsonl (including the 10 root
  archives that have no INDEX entry and INDEX line 17 with no `log` field —
  a separate backlog row).
- A Python archival helper, a content hash in INDEX, or any check that pairs a
  log's content to a specific ship.
- Porting D4 to `run_python_check`, or changing the wrappers' exit-code
  semantics (would amend ADR-006).
- Changing the M7, gate-schema or M8 scan scopes; backlog #155, #179 and #3.
- Enforcing the collision rule on no-Python ships beyond the workflow text.

## Constraints

- sh and ps1 twins change together and stay count-identical.
- Archived file **contents** are immutable; INDEX.jsonl is append-only (ADR-003).
- Workflow edits are deletion-funded (AC-9); remedy text goes into the tool's
  error message, not into workflow prose.
- Deployed surfaces touched: `ship.md`, `handoff.md`, `token-governance.md`,
  `validate.sh`, `validate.ps1`, `append_chain_entry.py`. No new deployed file.

## File Relationship

INDEPENDENT. Related: ADR-003 (INDEX chain), ADR-006 (native baseline),
backlog #186 (resolved here).

## Domain Decisions

- [DECISION] The archive directory is the type discriminator: root holds final Work Logs, `archive/work/` holds compaction fragments; consumers resolve and scan by directory, and the same basename may exist in both.
- [DECISION] A same-day collision on a final archive uses `<worklog-key>--N-<YYYYMMDD>.md`: normalized keys never contain `--`, and the date stays last for filename-date parsers.
- [TRADEOFF] D4 stays a native check edited in place, a documented deviation from ADR-006 §3, because the Python wrappers cannot express WARN; byte-identical twin snippets are test-pinned instead.
- [TRADEOFF] Legacy final logs found under `archive/work/` are moved to the root (location is mutable, content is not) instead of being exempted in validator code.
- [CONSTRAINT] Duplicate INDEX `log` values are rejected at append time by `append_chain_entry.py`, not by a validator scan, so the existing duplicate in history needs no grandfathering.
- [CONSTRAINT] A check that cannot run reports SKIP or WARN, never PASS and never silence.
