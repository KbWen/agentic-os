# Repo Gotchas

> **What this is**: traps specific to THIS repository that cost a real session at least once.
> Each entry is a mechanical failure you cannot infer by reading the surrounding code.
>
> **What this is not**: rules. There is no directive here and nothing to obey — it is a
> lookup table. Generic AI-assisted-development failure modes live in
> `ai-development-pitfalls.md`; recurring *behavioural* lessons live in
> `.agentcortex/context/current_state.md` `## Global Lessons`. Do not duplicate either here.
>
> **When to read**: before editing validators, README, deploy tooling, governance surfaces,
> or before cutting a release. Conditional read — skip it for ordinary code work.
>
> **If you deployed the brain into your own project**: these entries describe the agentic-os
> framework repo, and most of them still bite any fork that runs the same validators, deploy
> script, and work-log flow. This file is upstream-maintained and sits in the force-update
> class (ADR-005), so `deploy` overwrites it wholesale — record your own project's traps
> somewhere `deploy` does not own, not here.

---

## 1. README content is pinned in two independent layers

Editing or relocating `README.md` can break checks that never mention README in their name.

- `validate.sh` / `validate.ps1` carry an encoding canary that matches **literal phrases**
  from the README (`validate.sh` ~L891-895).
- `tests/ci/test_deploy_tiering.py` and `tests/ci/test_pre_commit_hook.py` assert README
  content (fork guidance, pre-commit hook instructions). These are CI-only.

Before restructuring README, grep both `tests/ci/` and `.agentcortex/bin/validate.*` for the
phrases you are about to move.

## 2. A new validator check has three wiring points, not one

Adding a check to `validate.sh` / `validate.ps1` fails in three separate places if wired
naively (ADR-006):

1. The check has to be a **Python tool invoked through `run_python_check` /
   `Invoke-PythonCheck`**. A new native `record_result` / `Add-Result` site trips the ADR-006
   native-count ratchet.
2. The shipped tool needs **both** whitelist spots in `.agentcortex/bin/deploy.sh`
   (`check_ssot_caps` appears twice — match that shape).
3. It also needs a row in `tests/ci/fixtures/deploy_manifest_golden.txt`, or
   `test_deploy_tiering` fails.

`check_ssot_caps.py` is the working template — copy its wiring, not just its logic.

The inverse trips people who never touched `deploy` at all. The governance docs that ship
downstream — `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, and the top level of `.agent/workflows/` and
`.agent/rules/` — get scanned by `test_deployed_governance_referenced_tools_are_deployed` for tool
paths under the runtime-tools directory, and a cited tool that `deploy` does not ship fails the
test. Not every checker is meant to ship: the skill-provenance one self-skips as soon as a deploy
manifest is present, so shipping it would only add a permanent no-op downstream. Prose describing
the upstream enforcement passes; a bare tool path in these files is a command the downstream
reader cannot run.

## 3. Local `validate` FAILs about work logs are usually invisible to CI

Work logs under `.agentcortex/context/work/` are gitignored. Local FAILs about work-log
count, compaction thresholds, or illegal gate progression come from files CI never sees —
CI reports `fail=0` on the same commit.

Clear them by **archiving tracked logs**, not by editing the validator. `/ship` archival is a
MOVE, not a copy. Before assuming a validator bug, check whether the offending path is
gitignored.

The inverse bites harder, because it turns CI red rather than green. **Archiving flips a log
from gitignored to tracked**, so checks that skipped it while it lived in `work/` start
judging it — `check_decision_disposition.py` is the one that catches people, since it excludes
`work/` entirely and enforces a date cutoff on the archive. A `## Decisions` entry that never
received its ship-time disposition marker (`ship.md` 2b: `→ promoted: ADR-<id>` /
`→ consolidated: L2 <domain>` / `→ local`) passes every local run right up until the moment
you archive it.

Consequence for ordering: a full-suite run taken **before** archival does not cover the
archived state. Run it after the move, or at minimum re-run the guard suite. Confirmed
2026-07-27 — a green 813-test local run preceded the archival, and CI went red on `main`
immediately after (PR #374 → #375).

## 4. The 355k lifecycle ceiling does not count `AGENTS.md` or `CLAUDE.md`

A widely-assumed premise that is false. `.agentcortex/tests/test_lifecycle_token_consumption.py`
sums `current_total_tokens`, which is dominated by `workflow_tokens` (workflow bodies) plus
skill probe/detail tokens. `CLASSIFICATION_BASE_FILES` in that file is used for *scenario
modelling*, not for the ceiling sum.

Measured 2026-07-25: appending 400 characters to `AGENTS.md` moved the aggregate total by
**0** tokens. Headroom at that date was 460 tokens (354,540 / 355,000) — so the ceiling is
tight, but it is `.agent/workflows/*` and skill bodies that consume it.

Re-measure rather than assume: `.agentcortex/tests/test_lifecycle_token_consumption.py` is the
enforcing authority, and names the analyzer it shells out to. (The analyzer is a source-repo
tool and is not part of a downstream deploy.)

## 5. The credential scan flags the repo's own documentation

`scan_credentials.py` matches example tokens inside your own docs and SSoT entries (an
`AKIA...EXAMPLE` string in a guide is enough). It is a true positive by pattern and a false
positive by intent.

Abbreviate the example, or mark the line `# pragma: allowlist secret`. Dogfood it with
`--range main...HEAD` **after** committing — an uncommitted range scans nothing.

## 6. Deleting table rows on CRLF files can silently merge neighbours

An `Edit` whose `old_string` begins with a newline can merge two adjacent rows into one on
CRLF-checked-out files, leaving a table that still looks plausible.

After deleting rows from any markdown table, re-count the rows and read `git diff` before
moving on. This is distinct from the `[cross-platform-eol]` Global Lesson, which covers
content-comparing validators and shell appends.

## 7. Not every CI check is required — auto-merge can land red

Some checks (Structural, Pytest on Windows) are not in the required set, so auto-merge can
merge a PR whose CI is red. This has happened.

Confirm the actual state per PR instead of trusting the merge button:

```bash
gh pr checks --watch
```

Then merge manually once the run you care about is green.

## 8. Multi-line `gh` / `git` bodies fail from the Bash tool on Windows

Two separate failure modes, both silent-ish:

- PowerShell here-strings (`@'...'@`) corrupt git commit messages when routed through the
  Bash tool.
- Bash heredocs / `$(cat <<EOF)` for `gh pr create` bodies break on apostrophes with
  `unexpected EOF`.

Write the body to a file first, then pass `--body-file` (`gh`) or `-F` (`git commit`).

## 9. Editing a registry `detail_ref` doc stales the compact index

`AGENTS.md`, `.agent/workflows/bootstrap.md`, and `.agent/workflows/routing.md` are
referenced by `.agentcortex/metadata/trigger-compact-index.json`. Editing one without
regenerating the index leaves skill-trigger metadata pointing at stale content.

Regenerate in the same change, not as a follow-up.

## 10. A `quick-win` work log still needs the full receipt chain

`quick-win` skips spec and handoff, but `validate.sh` still expects bootstrap, plan,
implement, and ship receipts in `## Gate Evidence`, plus a real `## Phase Summary` (not the
placeholder `none`). A log with only a ship receipt fails.

## 11. A `NOT READY` review needs an implement receipt before the re-review PASS

`Verdict: NOT READY` is a reverse edge. The receipt has to carry `Classification:`, and an
`implement` receipt has to appear between it and the later `review | PASS` — otherwise
`validate` reports illegal gate phase progression.

## 12. A release is not finished when the PR merges

The release-cut PR carries the version banners, CHANGELOG, and Ship History entry. After it
merges, two manual steps remain and are easy to forget (forgotten twice already):

```bash
git tag vX.Y.Z && git push origin vX.Y.Z
```

```bash
gh release create vX.Y.Z --latest
```

## 13. `TypeError: 'NoneType' is not a container` from a subprocess helper means locale, not logic

On a Windows box whose ANSI code page is not UTF-8 (e.g. `cp950`, Traditional Chinese),
`subprocess.run(..., text=True)` without an explicit `encoding=` decodes the child's output
with the system codec. One UTF-8 byte — an em-dash is enough, `0xe2` — raises
`UnicodeDecodeError` inside subprocess, `stdout` / `stderr` come back as `None`, and the line
that reads them dies naming nothing about encoding. Six tests were red locally and green in CI
on the identical commit, which reads exactly like "you broke something".

**Fixed in Python**: every call site was corrected and `tests/ci/test_subprocess_encoding.py`
now caps new ones at zero, so this should not recur here. The fix is always
`encoding="utf-8", errors="replace"`. If you meet the same signature somewhere the ratchet
does not reach — a shell script, a file read, a new dependency — suspect the same cause.

The general technique that isolated it is worth keeping regardless: when local tests are red
and CI is green on the same commit, re-run them in a clean worktree before assuming you broke
something.

```bash
git worktree add ../baseline main
```

## 14. Isolate a validator count shift by stashing, not by a clean worktree

`validate.sh` / `validate.ps1` end with `pass=N warn=N fail=N skip=N`. When that line moves
and you want to know whether your diff caused it, the clean-worktree technique from #13 does
**not** transfer. The reason is specific: roughly **18 PASS lines come from the active
work-log checks**, and those do not run when `.agentcortex/context/work/` holds no `*.md` log
(the shipped `.gitkeep.md` placeholder does not count — both validators exclude dotfiles). A
fresh worktree has no work logs, so its totals are structurally lower than yours no matter
what you changed.

Measured 2026-07-27 on one commit: a clean `main` worktree reported `pass=99 warn=3`; the real
tree with two active logs reported `pass=116 warn=4`; after archiving both logs the real tree
reported `pass=99 warn=3` as well. Nothing in that gap was a diff.

Since backlog #149 the run at least *says* so — one `SKIP` line reading `active work-log
checks -- no active work logs`. That marks the absence; it does not restore the missing PASS
lines, so the totals still are not comparable across trees.

Stash only your own change and re-run in place instead, then compare the result **lines**
rather than the totals:

```bash
git stash push -- path/to/changed-file && bash .agentcortex/bin/validate.sh > after.txt
```

An identical result-line set proves a zero delta far better than an identical count does.

One culprit worth checking first, because it is self-inflicted and easy to miss: if you
reclassified mid-task, your own gitignored work log now carries a `## Gate Evidence` receipt
whose `Classification:` disagrees with the header. That surfaces as
`active work log gate receipts with schema violations: 1` and one fewer PASS — a real finding
about your session, not about the tree. Re-issue the receipt at the new tier and keep the
original classification in `## Drift Log`, since the receipt grammar is pipe-field-strict.

---

## 15. A red secret scan is often an ordinary identifier, and a rename will not clear it

TruffleHog's Lob detector matches a word boundary, `live` or `test`, an underscore, then
**exactly 35** characters from `[a-zA-Z0-9_]` — underscores count, so a plain snake_case
name of the right length satisfies it. Its verifier then returns **verified**, which is why
`--only-verified` never bounded this class. It has cost two sessions: PR #402 (the test
enforcing the secret-scanner pin was blocked by the secret scanner) and PR #419 (a committed
pytest durations file of 897 node ids).

`--exclude-detectors=lob` is now set in `security.yml`, so new cases should not appear. Two
facts still matter if you meet one on an older branch:

- The action walks **each commit's diff across the range**, not the net endpoint diff. A
  follow-up rename does not clear the finding, and neither does add-then-remove. Only
  removing the introducing commit from the range does — in practice, squash.
- Commit **messages** are in scope too. Describing the incident can re-instantiate the
  pattern in the very commit that documents it; write the shape in prose, never an instance.

## Adding to this file

An entry earns its place when it cost a real session and is specific to this repo. If the
trap is generic to AI-assisted development, it belongs in `ai-development-pitfalls.md`. If it
is a recurring behavioural pattern rather than a mechanical trap, it belongs in
`## Global Lessons`. Keep entries short: what breaks, how you notice, what to do instead.
