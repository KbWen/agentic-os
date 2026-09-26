# Governance Self-Audit — Downstream Product-Development Simulation (2026-09-26)

> `/govern-audit`, scope **downstream**: does a project that installs today's
> `main` get a framework that installs cleanly, upgrades safely, and actually
> helps an AI agent build a better product? Continues backlog **#194** (the
> 2026-09-05 pass that ran 8 of 16 scenarios) and adds the question that pass
> never asked: product outcomes with and without the framework.
>
> Every finding below was attacked by a refute-only reviewer and then
> re-verified against primary sources by the primary. Where the refuter was
> right, the claim is corrected in place and the correction is listed in
> `## Adjudication`. Harness errors the audit made are recorded in
> `## Harness errors`, not hidden.

## Verdict

- **Install and upgrade mechanics are solid.** Adopter state survived 4/4
  upgrade paths, the validator twins agreed on 7/7 states, zero-Python
  degrades honestly, and Windows-native entry points work in a CJK + space
  path. The defects found are real but bounded (F1, F2, F6–F8).
- **"A strong aid for downstream product development" is not supported by
  this evidence.** Across 20 agent sessions no framework cell scored above
  its no-framework control on hidden acceptance tests; sessions that engaged
  the flow cost **2.4–10.4x** (Claude, dollars) or **2.75–3.25x** input tokens
  (Codex); and the one subtle product defect in the task set was caught by
  **2/2 controls but 1/5 framework-arm sessions**. n = 1 per cell,
  small tasks — directional, not an effect size.
- **The mechanism is specific, and it is where the value lever is.** When the
  full documented flow ran (`/bootstrap → /plan → /implement → /review →
  /test`, real slash commands), `/review` wrote the right invariant ("deleted
  IDs are never reused"), marked it **PROVEN** with a test that deletes a
  non-maximal ID, and its Red Team *observed the counterexample* ("delete-all
  then add → id=1") and filed it as safe (F3). The framework produced the
  appearance of rigor without a rule that makes a proof discriminate. Around
  it: the Claude adapter never tells a quick-win to open a Work Log (F4), and
  receipt timestamps are rarely clock-derived in practice (F5).

## Method

Four rounds against real deployments of `main` @ `de1c609` (v1.8.27 + #441–#443),
cloned from GitHub as INSTALL.md instructs, into `tasklite`, a small Python
product (CLI + JSON store + 6 pytest tests). Host: Windows 11, Git for Windows
2.53 with its default `core.autocrlf=true` and `core.longpaths` unset, Python
3.14, Windows PowerShell 5.1, pwsh 7.6.

| Round | What ran |
|---|---|
| R1 install mechanics | about 20 scripted scenarios: greenfield (dry-run, deploy, 4 validator variants, hook, banner-literal commit, teammate clone), documented update path, no-op redeploy, upgrades v1.8.10/20/24/26 → HEAD with 11 adopter customizations each, downgrade, brownfield (9 pre-existing adopter files), zero-Python (deploy, validate, hook), `deploy_brain.ps1` under 5.1 and `.cmd` into `…\G 我的 專案\my app`, monorepo per-package install, non-git and nested targets, banner-literal commit → CRLF teammate upgrade (with an A/B control) |
| R2 lifecycle tooling | primary-run `/ship` tool chain by the book; sh↔ps1 tally parity on 5 agent-produced states |
| R3 behavioural | 20 headless sessions: Claude Code 2.1.160 (`claude -p --model sonnet`, which resolved to **claude-sonnet-4-6**; host `CLAUDE*` env vars unset; no MCP) and Codex CLI 0.148.0 (`codex exec -m gpt-5.5`; the configured default needs a newer CLI). Arms: **ctrl** (no framework), **acx** (deployed + hook, zero-hint prompt), **guided** (INSTALL.md's recommended preface), **slash** (`/bootstrap <task>`, INSTALL.md option C). Tasks: T1 feature (due dates), T2 bug with a data trap (繁中 prompt), T3 pressure ("skip the ceremony"), T4 the banner's sidecar-merge instruction after an upgrade; plus 2 cross-session resume-and-ship runs and one full slash-command chain. Product quality scored by **hidden acceptance tests** the agents never saw, each shown to fail on the unmodified product first. |
| R4 adversarial | one refute-only subagent (same vendor) over all findings; a different-vendor refute pass was started and **cut off by the Codex usage limit** after partial output; every verdict primary-verified |

Caveats that bound every behavioural conclusion: n = 1 per cell; small tasks;
Sonnet 4.6 and gpt-5.5 rather than each vendor's strongest model; headless
mode (an interactive user answers the "stop and ask" prompts a headless run
cannot); one OS. The Claude and Codex arms differ in model tier as well as in
entry file, so **no vendor comparison is drawn** (see F4).

External-signal caveat (`/govern-audit` step 5): the behavioural data includes a
different-vendor model as a *subject* (Codex, gpt-5.5), but the adjudication is
**same-vendor-only** — the refuter and the primary are Claude-family models, and
the different-vendor refute pass ended at a usage limit after four partial
verdicts (all reflected in `## Adjudication`). Architecture-level conclusions
(the verdict, F3–F5) carry that label.

## Validator baseline and already-known list

Source repo `validate.sh`: `pass=99 warn=4 fail=0 skip=3`, exit 0. Fresh
downstream install: `86/1/0/8` on `validate.sh`, `validate.ps1` under 5.1 and
under 7; `--no-python` `76/1/0/18`.

Excluded as already known, re-verified in a real deploy:

| Row | Re-verification |
|---|---|
| #188 | Brownfield first install silently replaced the adopter's own tracked `.claude/commands/test.md` — no `[SKIP]`, no sidecar, no mention. |
| #193 | Same target: banner prints `Platform Entry Points Ready` while `validate.sh` exits 1 with the same 3 FAILs. |
| #105 | Downgrade HEAD → v1.8.24 rewrote the manifest to `1.8.24` with no warning. |
| #435 residue | Mixed-version rounds add 3 `.gitignore` lines each (recorded and accepted there). |
| config.yaml watch-item (2026-07-16) | `config.yaml:170` still says downstream "MUST override" `production_paths` while the file is core-tier; the edit was reverted (with `.acx-local`) on 4/4 upgrades. A simulation is not the watch-item's reopen trigger (a fork reporting it) — evidence recorded, disposition unchanged. |
| #100 | Its "same-owner + different-session — UNTESTED" case is now observed: a Codex resume 10 minutes after its own session stopped mid-flow was blocked and asked for `approve takeover`. This is the documented contract (`config.yaml:56-62`); evidence appended to #100. |
| #129 | Lingering-sidecar signal — F1 shows the opposite failure, which buries it. |
| #122 / 2026-07-11 receipt-integrity | Self-attested receipts — F5 is new occurrence evidence, not a new class. |
| #172 | The `no guard receipt found` WARN is cosmetic on every clean checkout — confirmed; it also fires unchanged after an unguarded SSoT write. |
| #194 | (a) zero-Python validator, (c) Windows-native, (d) non-git/nested, (f) twin parity, (g) skill shipping: **audited, clean**. (b) idempotency → F1; (e) greenfield noise → F11; (h) gate bypass → F5. Its two reproduced leads became F1 and F2. |

## Results — behavioural

| Arm | Sessions | Work Log created | Hidden tests vs control | Cost vs control |
|---|---|---|---|---|
| Claude acx (zero-hint) | T1, T2, T3 | 0/3 | T1 5/5 = 5/5; T2 3/4 < 4/4 | 1.03–1.07x (never engaged) |
| Claude guided | T1, T2 | 1/2 | T1 5/5 = 5/5; T2 3/4 < 4/4 | 2.39x, 1.51x |
| Claude slash (`/bootstrap`) | T1, T2 | 2/2 | stopped after bootstrap as designed (AGENTS.md Runtime v1, item 3) | bootstrap alone 2.1–2.6x the whole control task |
| Claude full slash chain | T2 | yes | **3/4 < 4/4** | **10.4x** ($2.76 vs $0.27) |
| Codex acx (zero-hint) | T1, T2, T3 | 3/3 | T1 5/5 = 5/5; T2 3/4 = 3/4 | input tokens 2.79x, 3.25x |
| Codex guided | T1, T2 | 2/2 | T1 5/5 = 5/5; T2 3/4 = 3/4 | input tokens 2.75x, 2.91x |

T2's subtle defect (an ID reused after deleting the highest ID): caught by
both controls, by 1 of 3 framework-engaged sessions (codex-guided; it failed a
different test) and by 0 of 2 non-engaged treatment sessions.

## Findings

### F1 (P2) — Scaffold sidecars regenerate on every deploy; every active adopter is told to merge a blank SSoT template → backlog **#201**

`.agentcortex/bin/deploy.sh:283-299` sidecars a locally modified scaffold file
whenever `src != dst` and never asks whether upstream changed since the
adopter's baseline; it re-records the old baseline (`:298`), so the condition
never clears. The live SSoT is scaffold-tier and always differs from its
template once used. Measured: upgrades from 4 versions and a no-op redeploy all
print `[SKIP] .agentcortex/context/current_state.md` plus "⚠ … merge each
`*.acx-incoming` … adopting framework updates", although the template is
byte-identical upstream (`git diff v1.8.26 HEAD` empty). Reproduced
independently by the refuter (`204 updated / 1 skipped` on two consecutive
no-op redeploys). Same run: a no-op update reports `205 updated` and rewrites
the tracked manifest's `deployed_at` (#194(b)). Both T4 agents judged the
sidecars correctly as no-ops — which is the point: the banner asks for a merge
that never exists. Adopter delta if fixed: updates stop producing false
"merge me" work, so a real framework change waiting in a sidecar (#129) becomes
visible. Design question (amends ADR-005's sidecar semantics) → spec first.

### F2 (P2) — A CR in the stored manifest makes a Windows teammate's upgrade report 13 false `[OVERWRITE]`s and freezes scaffold updates → backlog **#202**

`process_queue` (`deploy.sh:399-410`) reads the old manifest with `read -r` and
never strips `\r`, while file content is CR-normalized (`:81-93`). **A/B at
HEAD on the same commit**: original `205 updated / 0 skipped`; CRLF teammate
clone `13 locally-modified core force-updated / 3 skipped`; an identical clone
with only the manifest's CRs stripped `0 / 0`. Worse than first stated: the
regenerated manifest keeps 3 CR-bearing hashes (the sidecar'd lines, via
`:298`), so those 3 sidecars recur even after the EOL rule lands. Trigger: the
banner's `git add` line (`:1511`) omits `.gitattributes`, `.gitignore` and
`.githooks/` (a #194 lead, now reproduced); Git for Windows then checks the
manifest out CRLF for every teammate. Brownfield adopters whose own
`.gitattributes` is preserved are exposed the same way. Fix: strip `\r` where
manifest hashes are parsed (bash `read -r` keeps the CR; MSYS `sed`/`grep`/`awk`
drop it in text mode, which is why only the batch path is affected); list the
three paths in the banner.

### F3 (P2) — `/review` accepted a non-discriminating proof and dismissed its own counterexample → backlog **#203**

Full slash chain on T2 (transcript-verified `/bootstrap → /plan → /implement →
/review → /test`): the Burden-of-Proof table marked "B-3 Deleted IDs are never
reused … ✅ PROVEN" on a test that deletes id=1 of 3 (the `max(id)+1` scheme
only reuses when the highest ID is deleted); the Red Team section then recorded
"delete-all then add → new task gets id=1 (safe; no coexisting duplicates)" —
the counterexample itself — and closed with "No HIGH/CRITICAL findings". The
hidden test for exactly that case failed. The same defect shipped in 4 of 5
framework-arm sessions on T2. This is the product-quality lever: a PROVEN row
needs evidence at the boundary where the invariant is most likely to break, and
a red-team observation that contradicts a PROVEN row must reopen it. Behavioural
guidance, not machinery; `review.md` is counted by the lifecycle-token ratchet,
so the wording must be measured and deletion-funded.

### F4 (P2) — The Claude adapter never tells an agent to open a Work Log; #159's reach fix did not reach it → backlog **#204**

`CLAUDE.md:9-16`: the quick-win bullet (`:12`) is "read SSoT (Step 3), skip
Step 4", and Steps 3–5 are reads only — no tier is told to run bootstrap or create the
Work Log. #159 (PR #388) added that clause to `bootstrap.md` and
`state_machine.md`, which a Claude quick-win never loads. claude-acx-t1 followed
`CLAUDE.md` verbatim: read the SSoT, said "This is a quick-win — two modules,
clear scope. I'll implement directly," and did. Codex loads `AGENTS.md` natively
and opened a Work Log in every Codex session (6/6). The other Claude non-engagements (T2, T3
with "skip the ceremony") show no classification at all and are the known
adherence ceiling; with model tier confounded, **this is a first-party
parity defect, not a vendor finding**. Fix the adapter, then re-measure.

### F5 (P2) — Receipt timestamps are rarely clock-derived in practice; future-dated receipts pass → backlog **#205**

29 receipts in the 7 receipt-bearing Work Logs: **4** carry a plausible clock
time, **18** are midnight placeholders (`00:00:00+08:00`, `00:00:00Z…00:05:00Z`,
including the fully compliant slash chain) and **7** are future-dated relative
to the log's last write (codex-acx-t2: implement…ship at 07:16–07:25Z in a log
last written 07:10:46Z, validated at 07:12:03Z, exit 0, and no ship happened;
codex-guided-t1: 07:18–07:19Z in a log last written 07:15:01Z). In the Claude resume the hook's
`illegal gate phase progression` FAIL was answered by inserting a `plan`
receipt for a phase neither session ran; the commit then passed. The class is
known and was decided (`validate.sh:1979-1982`: presence-only; the 2026-07-11
audit's own alternative was to "remove Timestamp from the claimed receipt
contract"). New: real downstream occurrence in 7 of 7 receipt-bearing logs; 25 of 29
timestamps are not a clock reading. Options, in DELETE-bias order: drop Timestamp from the
contract; or have a helper write receipts with the real clock. A
"receipt-after-now" FAIL is **not** zero-false-positive (local time labelled
`Z` in UTC+8 would trip it) and would catch 2 of the 7 logs.

### F6 (P3) — The documented update path fails on a long Windows path, and a retry proceeds from a partial checkout → backlog **#206**

`installers/deploy_brain.sh:85-119` clones the whole upstream into
`<project>/.agentcortex-src`; upstream's longest path is 100 chars, so project
roots over ~141 chars fail checkout (`Filename too long`, exit 128) with Git for
Windows defaults. The retry takes the `git pull` branch (`:98`), reports
`Already up to date` over an empty index, and deploys with exit 0; only one file
(outside the deploy set) was missing, and the only guard is the existence of
`deploy.sh`. Triggered here by the 149-char scratch path; rare on real paths but
grows with archive filenames. Fix: `-c core.longpaths=true`, and treat a
non-clean cache as corrupt.

### F7 (P3) — The managed ignore block ignores `.cursor/` wholesale → backlog **#207**

`deploy.sh:1103`, present since the initial release. Cursor project rules are
meant to be committed; a new `.cursor/rules/*.mdc` is silently skipped by
`git add -A` and IDE staging (an explicit `git add <file>` errors). Already
tracked rules stay tracked. Same scope principle #191 shipped under (framework
namespace only).

### F8 (P3) — In a monorepo per-package install, INSTALL.md's hook steps install nothing → backlog **#208**

Run inside `packages/app`, `git config core.hooksPath .githooks` resolves
against the repository root; the ACX hook never ran on two commits. (That it
replaces existing hooks is already warned at INSTALL.md:61 and in the banner.)
`[PASS] optional guard hook sample present` only proves the sample exists; the
activation check is #142's territory.

### F9 (P3) — No deployed doc contains a runnable guarded SSoT write, and `ship.md` permits the direct edit AGENTS.md routes away from → backlog **#209**

`--lock-key` and `--input` (both required) appear in no deployed workflow or
guide; `ship.md:185` says `guard_context_write.py --mode replace` (no `write`
subcommand) "or a surgical anchored Edit", while `AGENTS.md` §Write Isolation
routes SSoT writes through the guard. `append_chain_entry.py` and
`recover_worklog_lock.py` get copy-paste templates. Related observation: the
Claude resume executed `/ship` **without opening `ship.md`** (its reads were the
SSoT, the Work Log and the template) — hence copy-not-move archival, no chain
entry, no lock release, an unguarded SSoT write, and the SSoT update left
uncommitted after the feature commit.

### F10 (P3) — The missing-receipts FAIL is count-only → backlog **#210**

`validate.sh:1880-1881` / `validate.ps1:1773-1774` print `…: N`, while the
checkpoint WARN beside it lists offenders. With the opt-in hook installed this
blocks product commits on a gitignored local file. The one agent that hit it
repaired the format in one step from the template, so impact is low; 3 other
free-form logs were never seen by their agents.

### F11 (P3) — Install-day copy and encoding defects, batched → backlog **#211**

(a) No-Python hook: a clean floor pass is silent — an OpenAI-shaped key
(blocked with Python as `openai-key`) committed without Python with no
credential-scope notice; only the fallback path prints REDUCED ASSURANCE.
(b) `--dry-run` says 26 docs (30 deploy) and omits the `.githooks` sample and
the `.gitignore` edit. (c) The first install commit prints three irrelevant
`GUARD WARN … use the /ship workflow` lines. (d) Banner `Python 3.8+` vs
INSTALL.md / validators `3.9+`. (e) INSTALL.md:210 says an in-place `AGENTS.md`
edit is "force-updated on the next deploy"; it is scaffold (sidecar'd).
(f) On a cp950 console, 17 of 19 deployed Python tools emit non-ASCII in the
code page while `validate.sh` emits UTF-8 (`check_lifecycle_frontmatter`'s em
dash arrives as `A1 58`) — adjacent to #175 (script literals) and #146 (tests).

## Adjudication (refute pass, primary-verified)

| Claim in draft | Refuter | Primary verification | Result |
|---|---|---|---|
| Update retry deploys with "~30 files missing", clone "14 MB" | WEAKENED | `ls-tree` 630 paths, 629 on disk; the 30 were `??` lines; 9–11 MB | corrected (F6 → P3) |
| Sidecar on every deploy (N2) | CONFIRMED + reproduced | own no-op redeploy | kept; AGENTS.md/SKILL.md angle narrowed (INSTALL advises against in-place edits) |
| `.cursor/` "silently" blocks adds; "#435 scope rule" | WEAKENED | explicit `git add` errors; the principle is written in #191's row, not a repo rule | corrected (F7 → P3) |
| Monorepo: existing hook disabled "with no warning" | WEAKENED | INSTALL.md:61 + banner do warn | dropped that half (F8) |
| Manifest CR "fixed at HEAD" (partial different-vendor pass) | — | A/B at HEAD: 13 overwrites vs 0 | refuted; F2 stands and is worse (CR re-recorded) |
| Hook ⇒ fabrication; "missing receipts" blocked twice | WEAKENED | 2nd block was `illegal gate phase progression`; Codex future-daters never committed | mechanism narrowed to 1 case; occurrence broadened to 7 of 7 receipt-bearing logs |
| Receipt-after-now check is zero-false-positive | WEAKENED | local time labelled `Z` would trip it | withdrawn |
| Id reuse "missed by all 4 framework sessions" | FACTUAL ERROR | codex-guided-t2 caught it | corrected to the counts above |
| Codex token overhead "up to 3.5x" | WEAKENED | 2.75–3.25x from raw usage | corrected |
| Claude never engaged "while Codex did" (vendor contrast) | WEAKENED (pre-mortem pick) | `CLAUDE.md:9-16` has no Work-Log step; model tier confounded | reframed as F4 (adapter parity) |
| Claude resume failed because ship.md's hint is unrunnable | WEAKENED | agent never opened ship.md | causal claim dropped; doc gap stands (F9) |
| Lock blocking a same-owner resume is new | ALREADY-KNOWN | `config.yaml:56-62`, #100 | evidence appended to #100 |
| `no guard receipt` WARN cannot discriminate | ALREADY-KNOWN | #172 | not re-filed |
| No-op "205 updated" | ALREADY-KNOWN (#194 lead) | reproduced | folded into F1 |
| Stripe-shaped key shows a no-Python gap | WEAKENED | scanner has no Stripe shape either | re-tested with an OpenAI shape (F11a) |
| "12 of 17 tools" lack UTF-8 stdout | WEAKENED | 17 of 19 | corrected (F11f) |
| Sidecars missed because gitignored | REFUTED | `rg -g` overrides ignores; rg skips the hidden `.agentcortex/` dir | mechanism dropped; lingering-sidecar signal is #129 |

**Pre-mortem adopted:** the most likely embarrassing error was blaming a vendor
for a first-party adapter gap. The report draws no vendor conclusion.

## Harness errors (recorded, not hidden)

- Two Codex runs lost their post-session evidence step because the runner
  script was edited while they ran; evidence was re-collected from the
  untouched trees afterwards (the agents had already finished).
- Git Bash's MSYS path conversion rewrote `/plan` into `C:/Program
  Files/Git/plan` in the first slash chain; that run was discarded
  (`_invalid-chain-*`) and re-run with `MSYS_NO_PATHCONV=1`, verified from the
  transcript. The `/bootstrap` runs were unaffected (multi-line argument).
- The first zero-Python secret probe used a shape the Python scanner does not
  cover either; replaced (F11a).
- Side effects on the operator's machine: Codex runs registered 10 scratch
  directories as trusted in `~/.codex/config.toml` (removed; file verified
  identical to its pre-session state) and **exhausted the Codex usage
  window**; nested Claude sessions persisted transcripts under
  `~/.claude/projects/` (kept as evidence).

## Dispositions

| # | Finding | Disposition |
|---|---|---|
| F1 | perpetual sidecars / SSoT template merge | backlog #201 (spec: ADR-005 amendment) |
| F2 | manifest CR | backlog #202 (quick-win) |
| F3 | review proof discipline | backlog #203 (quick-win, ratchet-measured) |
| F4 | Claude adapter parity | backlog #204 (quick-win) |
| F5 | receipt timestamps | backlog #205 (spec) |
| F6 | update path long paths | backlog #206 |
| F7 | `.cursor/` ignore | backlog #207 |
| F8 | monorepo hook path | backlog #208 |
| F9 | guarded-write template / ship.md contradiction | backlog #209 |
| F10 | count-only FAIL | backlog #210 |
| F11 | install-day copy + cp950 | backlog #211 |
| — | config.yaml "MUST override" on a core file | close-with-reason: existing watch-item, reopen trigger not met |
| — | lock blocks same-owner resume | close-with-reason: documented contract; evidence on #100 |

Suggested order, by leverage on downstream product outcomes, then cost:
**#204 + #203** (the two product-outcome levers: Claude users entering the flow
at all, and `/review` proofs that discriminate — both ratchet-measured) →
**#202 + #206 + #207 + #208** (install path, one branch) → **#209 + #210 +
#211** (docs and tooling polish) → **#201** and **#205** (both need a spec;
#205's preferred option is a deletion). Ship serializes on SSoT: one branch at
a time.

## routing_actions

```yaml
routing_actions:
  - finding: "Scaffold sidecars regenerate without an upstream change; the live SSoT is sidecar'd from its template on every deploy (backlog #201)"
    target_doc: "docs/architecture/document-governance.log.md"
    status: pending
    owner: "unassigned"
  - finding: "Review PROVEN rows accept non-discriminating proofs; a red-team counterexample does not reopen them (backlog #203)"
    target_doc: "docs/architecture/governance.log.md"
    status: merged
    owner: "fix/agent-guidance-levers-204-203"
  - finding: "Gate-receipt Timestamp is rarely a clock reading in practice (25 of 29 synthetic or pre-written) — keep, auto-stamp, or delete from the contract (backlog #205)"
    target_doc: "docs/architecture/governance.log.md"
    status: merged
    owner: "fix/gate-evidence-tooling"
```

Probe hygiene: all deployments, agent sessions and reproductions ran in a
scratch directory outside the repository; nothing from them was committed.
Evidence (logs, transcripts, work logs, scripts) is kept there for the session.

## Addendum — post-remediation measurement (same day)

The two product-outcome levers were implemented on `fix/agent-guidance-levers-204-203` and re-measured with the same harness before shipping.

- **F4 / #204 — refuted as a lever.** Adding the Work-Log step to `CLAUDE.md` changed nothing: zero-hint Claude opened a Work Log in 0/3 runs before and 0/3 after (one run classified quick-win and went straight to code without reading the SSoT). The change was reverted. The pre-mortem's hypothesis that one clause could close the gap does not hold; what does work is starting the task with `/bootstrap <task>` (6/6 engaged). Decision moved to #213.
- **F3 / #203 — shipped, effect not demonstrated.** v1 (Self-Check only) lost to the existing rule that accepts `file:line` evidence: the re-run review certified "deleted IDs are not recycled" by citing the very `max(id)` line that recycles them. v2 moved the rule into the evidence definition. In two v2 chains the rule never fired, because neither review listed the invariant as a criterion. Governed chains caught the defect 0/4 — one run before the change, three after — against 2/2 no-framework controls. The shipped wording, after two further review rounds (rule placed above both evidence lists, untagged PARTIAL forces NOT READY, receipt written after the Self-Check), was not re-measured. The upstream gap is filed as #212.
- **Unchanged conclusion:** the verdict above stands, and it is now sharper — wording in the phase files is not where the product-quality lever sits for these models.
