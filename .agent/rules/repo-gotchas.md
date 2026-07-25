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

## 3. Local `validate` FAILs about work logs are usually invisible to CI

Work logs under `.agentcortex/context/work/` are gitignored. Local FAILs about work-log
count, compaction thresholds, or illegal gate progression come from files CI never sees —
CI reports `fail=0` on the same commit.

Clear them by **archiving tracked logs**, not by editing the validator. `/ship` archival is a
MOVE, not a copy. Before assuming a validator bug, check whether the offending path is
gitignored.

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

## 13. Six tests fail locally on a non-UTF-8 Windows console and are green in CI

On a Windows box whose ANSI code page is not UTF-8 (e.g. `cp950`, Traditional Chinese), some
tests read subprocess output with the system codec. The tools emit UTF-8 (an em-dash is enough
— byte `0xe2`), decoding raises `UnicodeDecodeError`, `result.stdout` / `result.stderr` come
back as `None`, and the assertion dies with `TypeError: argument of type 'NoneType' is not a
container` rather than anything resembling the real cause.

Confirmed on clean `main` @ `1627852` (2026-07-25): `test_lesson_chain_archival.py` ×2,
`test_verify_agent_evidence.py` ×3, `test_trigger_metadata_tools.py::test_command_sync_rejects_alias_directive_retarget`.
Same commit is green in CI.

Before assuming you broke something, re-run the failing files in a clean worktree of `main`:

```bash
git worktree add ../baseline main
```

If they fail there too, it is this trap. Tracked as backlog #146.

---

## Adding to this file

An entry earns its place when it cost a real session and is specific to this repo. If the
trap is generic to AI-assisted development, it belongs in `ai-development-pitfalls.md`. If it
is a recurring behavioural pattern rather than a mechanical trap, it belongs in
`## Global Lessons`. Keep entries short: what breaks, how you notice, what to do instead.
