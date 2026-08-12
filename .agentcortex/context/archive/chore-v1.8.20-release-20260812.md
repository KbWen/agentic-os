# Work Log: chore/v1.8.20-release

## Header

- Branch: `chore/v1.8.20-release`
- Classification: `quick-win`
- Classified by: `claude-opus-5`
- Frozen: `2026-08-12`
- Created Date: `2026-08-12`
- Owner: `KbWen`
- Guardrails Mode: `Quick`
- Current Phase: `ship`
- Diff Base SHA: `491f372`
- Checkpoint SHA: `491f372`
- Recommended Skills: `none`
- Primary Domain Snapshot: `governance`
- SSoT Sequence: `149`

---

## Session Info

- Agent: `claude-opus-5`
- Session: `2026-08-12 UTC`
- Platform: `claude-code`
- Files Read: `9`

---

## Task Description

Cut **v1.8.20**. Ten commits sat unreleased on `main` with the version banner still reading 1.8.19: the #166 P1 supply-chain fix, the #163/#164 audit-wave leftovers, three dependabot bumps, and the records wave. Docs-only cut by house convention — banners across the canonical 7 files, a CHANGELOG section, and the release's own Ship History entry.

---

## Phase Sequence

| Phase | Status | Entered | Notes |
|---|---|---|---|
| bootstrap | done | 2026-08-12 | diff measured before classifying |
| plan | done | 2026-08-12 | docs-only cut; no engine change rides the release |
| implement | done | 2026-08-12 | 7 banners + CHANGELOG + Ship History, seq 148→149 |
| review | skipped | 2026-08-12 | optional for quick-win |
| test | done | 2026-08-12 | caps, chain, validators |
| handoff | n/a | — | quick-win exempt |
| ship | done | 2026-08-12 | PR; tag + GitHub Release after merge |

---

## Phase Summary

**bootstrap** — Measured first: the cut touches 7 banner files plus CHANGELOG and the SSoT, all documentation, well inside the 200-line / 2-module hard block for substantive modules. `quick-win` holds. Order matters — PR #402 classified before measuring and violated that block.

**plan** — Release cuts carry no engine, test, or logic change; that is the house convention and it is what makes the diff reviewable at a glance. Everything substantive was already merged and individually CI-green.

**implement** — Banners 1.8.19→1.8.20 across the canonical 7 (`deploy.sh` `ACX_VERSION`, `CITATION.cff` version + `date-released`, Model Guide EN/zh-TW, Testing Protocol EN/zh-TW, `antigravity-v5-runtime.md`), each replacement asserted to match exactly once. CHANGELOG `[1.8.20]` in house format. SSoT via `guard_context_write.py` under optimistic locking, sequence 148→149, with the cap-10 rotation moving `Ship-fix-149-worklog-family-skip-2026-07-27` into `archive/ship-history-2026.md`.

**test** — `check_ssot_caps.py` → `ship history 10/10, spec index 26/30`; chain intact; both validators re-run after the final Work Log write.

⚡ ACX

---

## Gate Evidence

- Gate: bootstrap | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-12T14:00:00Z
- Gate: plan | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-12T14:05:00Z
- Gate: implement | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-12T14:25:00Z
- Gate: test | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-12T14:35:00Z
- Gate: ship | Verdict: PASS | Classification: quick-win | Timestamp: 2026-08-12T14:45:00Z

---

## External References

| Type | Path / URL | Notes |
|---|---|---|
| Spec | — | — |
| ADR | — | — |
| PR | https://github.com/KbWen/agentic-os/pull/402 | the P1 fix this release packages |

---

## Known Risk

- **The release is not complete at PR merge.** The lightweight `v1.8.20` tag and `gh release create --latest` are separate manual steps, and this repo has forgotten them twice (repo-gotchas #12). Tracked to completion in this session rather than assumed.

---

## Decisions

### D-1: Ship with five known defects filed and unfixed
#167–#171 are all real and all recorded. None is fixed here, because each fix touches tool, workflow, or `.gitattributes` code that a docs-only release cut must not carry, and one (#171's detector exclusion) is a security-coverage decision that deserves its own review rather than riding a release. The release therefore ships a **known** state rather than a quiet one — the CHANGELOG names all five, including the one that blocked this release's own security PR.
→ local

### D-2: #171 not fast-tracked despite being the only candidate
It is the sole open item with an argument for immediate action: 35 latent identifiers can block any future PR's CI. Against that — the class predates this wave by months and only fires when someone adds or touches a matching line, and the remedy weakens a detector. Deferred with the reasoning recorded, not silently.
→ local

---

## Conflict Resolution

none

---

## Skill Notes

none

---

## Drift Log

none

---

## Review Feedback

none

---

## Security Findings

- The release packages a supply-chain fix (#166) whose control had not been holding. No compromise is claimed or suspected: the exposure was the absence of the guarantee, not a known bad artifact.

---

## Red Team Findings

none

---

## Design Reference

none

---

## Observability

none

---

## Resume

none

---

## Test Gate Results

- `check_ssot_caps.py` → `ssot caps OK — ship history 10/10, spec index 26/30`
- `check_audit_chain.py` → `audit chain intact`

---

## Evidence

- **Banner sweep verified both directions**: each of the 7 replacements asserted to match exactly once before writing, then `grep -rn "1\.8\.19"` across the same 7 files → **no matches**.
- **Guarded SSoT write**: `--expected-sha b050f29e… --mode replace` → `{"status": "ok"}`; sequence 148→149; 10 Ship History entries before and after.
- **A wrong fact caught before it entered the SSoT**: the entry first named `Ship-chore-review-gate-findings-backlog-2026-07-27` as the rotated entry; the rotation actually moved `Ship-fix-149-worklog-family-skip-2026-07-27`. Corrected in the staged content, so the false name never reached `current_state.md`.
- **Final validators** (terminal write; postdates the self-archival): `validate.sh` **`pass=118 warn=4 fail=0 skip=2`**, `fail=0`. Three WARNs are the pre-existing historical set; the 4th is an external reviewer's stale lock from PR #401, gitignored and outside this diff. Machine-local totals — a clean checkout runs 18 fewer active-work-log checks; CI is the replayable evidence.
