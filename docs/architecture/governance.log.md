# Governance (meta) — Layer 2 Decision Log

> Append-only chronological entries. Never delete or modify existing entries.
> Each entry records a [DECISION] / [TRADEOFF] / [CONSTRAINT] from a shipped spec.
> Domain scope: meta-governance — rule authoring, enforcement tiers, behavioral evals,
> session/lock discipline. (Document lifecycle decisions live in document-governance.log.md.)

---

### [governance][2026-06-10][feat/deletion-first-add-gate]
source_spec: docs/specs/deletion-first-add-gate.md
source_sha: ccb0294

[DECISION] 3 tiers, not 4: "external standard" as a standalone tier fails the [enforcement] lesson's test (citation ≠ enforcement); demoted to supporting metadata. Tiers map 1:1 to the lesson's taxonomy (validator/test/hook · eval case · named observer), ordered strongest-first so authoring is "pick strongest feasible", not a 4-way judgment.

[DECISION] Deletion-First scope = the three always-loaded surfaces only (AGENTS.md, .agent/rules/*, shared-contracts.md). Workflow files are heading-scope-read and mostly receive operational fixes — taxing each tweak with a deletion citation is the heaviness this feature is forbidden to add. The ADD-gate still covers workflows for NEW gates.

[DECISION] T2 is constrained to rules inside the eval harness's governance files — the seed-schema test requires `protects` anchors to resolve against that inventory; expanding the inventory for workflow gates would be scope creep (workflow gates use T1: validate.* already does workflow-literal checking).

[CONSTRAINT] `signal_tier: none` escape exists so tooling-only governance specs don't WARN forever — a nagging false positive trains people to ignore the validator.

### [governance][2026-07-19][feature/directive-enforcement-audit]
source_spec: docs/specs/directive-enforcement-audit.md
source_sha: 3004d88

- [DECISION] Scope is the **four phase-entry surfaces only** (AGENTS.md, engineering_guardrails.md, security_guardrails.md, shared-contracts.md). Other `.agent/**` files (workflows read heading-scoped, skills) are out of scope — this is Strand D's declared bound, and deletion-first already limits the Deletion-First norm to the always-loaded surfaces.
- [DECISION] Enforcement tiers reuse §13's **T1/T2/T3 verbatim** (T1 validator/test/hook · T2 eval-backed case · T3 named human observer); `NONE` is the 4th bucket. The **counting unit is semantic**: one enforceable behavioral obligation = one row, keyword-independent (a keyword-less imperative like the reply-language rule is still a row). No new tier vocabulary is invented (would fork the taxonomy governance.log.md already records).
- [DECISION] Success = **100% of directives tier-LABELED (honest `NONE` allowed) + every NONE-tier directive carries a disposition**; count reduction is an OUTCOME, not a target. A `NONE` survivor is legitimate under `keep-honest-unenforced` — deleting a load-bearing-but-unenforceable rule (e.g. Read-Once Discipline) is self-harm, and fabricating an observer to manufacture a tier is the very theatre being retired. Calibration: expected clean deletions ≈ 0–2 (a private upstream prior-art run of the identical census deleted ZERO); the deliverable is the map, not the prune. The instruction-consistency threshold is a **150–200 range** (research doc Corrections), our ~90 sits under it, so a count target would delete load-bearing rules to hit a number while ignoring burial depth.
- [DECISION] `primary_domain: governance` (NOT document-governance): governance.log.md scope is explicitly "rule authoring, **enforcement tiers**, behavioral evals", while document-governance owns doc *lifecycle/taxonomy*. The parent spec deletion-first-add-gate.md also consolidated into governance.log.md — same domain, consistent sink.
- [DECISION] Enumeration artifact = a **one-time dated point-in-time snapshot** in `docs/reviews/` — NOT a living table and with **NO observer re-snapshot duty** (a re-snapshot duty would be a new T3 honor-system process, the exact category this spec retires). Drift is instead caught by a **directive-count ratchet test** (`tests/ci/`, cap-at-today). It is **test-tier FAIL, not WARN-tier**: the repo's own 355k test-tier ceiling demonstrably formed deletion-funding discipline, WARN advisories are ignorable, and a private upstream prior-art run's +9 keyword growth UNDER a green token ratchet proves observer-only fails. Cap-at-today ≠ the rejected fixed count target — it caps growth from today without setting a `target < N` bar.
- [DECISION] ADR-008 fenced cluster is **EXCLUDED regardless of tier** because placement governs it: an irreversible-hazard rule stays on the always-loaded surface even where its filesystem teeth are T0 advisory (`[rule-placement]`). Subagent Safety Delegation is itself T0 but survives *because it is fenced*, not because it is enforced — the one deliberate exception to the deletion rubric, and it is a placement decision, not a tier decision.
- [DECISION] The **sentinel is not NONE-tier theatre.** The Work Log `## Phase Summary` half is true T1 (validate.sh/ps1 WARN; validator reads the artifact) and the chat-emission half is T2 = adherence measured OFFLINE by the eval harness (`governance.yaml sentinel-omission`), NOT live-enforced in production. The `[enforcement]` lesson names `⚡ ACX` as a theatre *example*, but that naming predates the validator + eval case; both halves survive. ADR-011 makes the final call.
- [DECISION] *(ship-added, Work Log D-2 disposition — provenance: primary adjudication 2026-07-19, not in the spec's own section)* ADR frontmatter `classification` describes the DECISION's nature, not the task tier: a `feature`-classified task may author an `architecture-change`-classified ADR (ADR-010 precedent, reaffirmed by ADR-011).
- [TRADEOFF] Fewer *fake* tiers → honest labels. A behavior-shaping advisory with no teeth is now retained as `keep-honest-unenforced` (labeled `NONE` with a rationale) rather than deleted or given a manufactured observer — false confidence is removed by honest labeling, not by stripping the prompt. A rule genuinely deleted (observability-only) carries no behavioral loss. **Reopen trigger**: a post-ship incident traced to a rule this prune removed.
- [CONSTRAINT] Every touched eval case re-maps (SECTION-level) or retires its `governance.yaml` `protects`-tag in the same change; a green eval run is NOT evidence a rule survived — the runner never reads the protected text (`[eval-mapping]`).
- [CONSTRAINT] Burial-depth = **within-loaded-unit ordinal**, a first-class audit axis for engineering_guardrails.md. Each directive's read-moment / load-layer is marked BEFORE any move; **relocation across load-layers is forbidden for always-on rules** and merges may only hold or decrease a survivor's ordinal — moving a rule deeper transfers lost-in-the-middle risk (Strand D: ordering may matter more than count).

### [governance][2026-08-13][chore/local-state-contract]
source_spec: (none — quick-win; external audit `docs/reviews/2026-08-13-govern-audit-drift-core-health.md` F3)
source_sha: (ship commit on chore/local-state-contract — squash-merged via PR)

- [DECISION] **A file that declares itself user-local must be untracked, not
  re-declared.** `.claude/settings.json:2` says per-operator permissions live
  in `settings.local.json`; git tracked that file anyway, so every session's
  permission edits dirtied the shared tree — 13 archived Work Logs record the
  cost of routing around it. The declaration was correct and git was wrong, so
  git changed. The inverse fix (amend the declaration to match git) was
  rejected: it would make a genuinely per-operator artifact shared state.
- [CONSTRAINT] **This class is not closed by fixing one instance.** Two more
  paths carried the same contradiction more sharply — present in `.gitignore`
  *and* tracked. Two grandfathered `.guard_receipts/*.json` blobs were cleared
  here (`git ls-files` showed 2 tracked against 21 on disk, so the ignore rule
  was already working for the rest). `.guard_receipt.json` was **not**: the
  validators PASS on `-f` of that exact path, so untracking alone converts a
  real contradiction into a permanent cosmetic WARN on every clean checkout.
  Audit the class, then check each member for a machine dependency before
  touching it — a contradiction is not automatically safe to resolve.
- [CONSTRAINT] A repo-side hygiene fix that has a downstream twin MUST land
  both halves. `deploy.sh` ships `.claude/settings.json` at scaffold tier, so
  adopters inherited the user-local claim with none of the git behaviour
  backing it; the pattern goes in the managed ignore block **and** the
  per-pattern `managed[]` map in `strip_managed_ignore_blocks`, since block-
  only leaves adopters with a duplicated line.
- [DECISION] **When a deployed document promises enforcement that does not
  exist downstream, the prose is corrected immediately and the enforcement
  decision is routed separately.** `ship.md` told adopters a broken audit
  chain is "caught by `check_audit_chain.py`" and "will cause `validate.sh
  check_audit_chain` to fail" — that tool is not deployed, so neither happens.
  The correction is true whichever way the deploy question resolves, so it
  does not wait on that question; whether the checker should ship is
  ADR-003-adjacent and became backlog #173. Applied twice in one wave (#172
  routed `.guard_receipt.json` to ADR-002 the same way): **a hygiene unit
  fixes what is unambiguously false and never decides what is genuinely
  open.**
- [CONSTRAINT] Downstream reach is a property to be *measured*, not assumed
  from the fact that a control exists upstream. The deployed validators
  reference 19 tools and 7 are absent, at least 4 deliberately, with no
  allowlist separating intent from oversight — and the guard meant to catch
  exactly this scans governance docs for a literal `.agentcortex/tools/<name>.py`
  path, so a tool named in prose as a bare filename, or referenced only by the
  deployed validator, is invisible to it. Simulate the adopter; do not read the
  whitelist and conclude.
- [TRADEOFF] Untracking is not free for anyone holding an existing clone: on
  the next `git pull` an identical local copy is deleted and a modified one
  makes the merge refuse. Accepted on measured blast radius (one worktree, no
  persistent bot checkouts, fresh clones never had the file) and recorded
  rather than assumed away. **Reopen trigger**: a contributor reports lost
  local permissions.

---

### [governance][2026-08-24][fix/ignore-assertion-binding]
source_spec: — (quick-win; Work Log `.agentcortex/context/archive/fix-ignore-assertion-binding-20260824.md`)
source_sha: 14ac9d9

- [DECISION] A guard that asserts something about **git's behaviour** must ask git, not
  pattern-match the file git reads. The `.gitignore preserves persistent SSoT artifacts`
  check compared whole `.gitignore` lines against a list of directory paths; a downstream
  fork's `.agentcortex/context/archive/*.md` hides the archived Work Logs without ever
  spelling that directory, so the guard reported PASS while the governance record stopped
  being committed. Reproduced here before fixing: one appended line left `fail=0` while
  `git check-ignore` confirmed the logs were hidden. The same shape had independently
  grown in two forks of the same ancestor, which is what makes it a class and not a slip.
- [DECISION] Probe a representative **file inside** each protected directory, never the
  directory itself — `docs/specs/*.md` ignores the contents without matching the directory,
  so a directory probe reproduces the original blindness. Probing inside subsumes both.
- [CONSTRAINT] `git check-ignore -v` exits 0 whenever a pattern **matched**, including a
  negation. On the ordinary `docs/adr/*` + `!docs/adr/*.md` idiom, `-v` exits 0 while `-q`
  exits 1 and git tracks the file. Taking the verdict from `-v` fails a correct adopter and
  names their protective `!` line as the pattern to remove — a diagnostic whose advice
  breaks something that was working. Verdict from `-q`; `-v` for the message only.
- [CONSTRAINT] `check-ignore` skips **tracked** paths unless `--no-index`, so the one real
  path in any such probe list is inert in a healthy tree. Omitting the flag shipped a
  detection *narrowing* inside a change whose stated purpose was broadening.
- [DECISION] Three verdicts, not two, and FAIL outranks SKIP. A guard that could not run
  must say so rather than report assurance — the discipline PR #412 established for absent
  tools, applied here to an absent git or a non-work-tree. And when some probes are ignored
  while others are unresolvable, the FAIL wins and names the unresolved count in its tail;
  letting SKIP win would let one unreadable probe swallow a real data-loss finding.
- [DECISION] A page that documents a mechanism should point at the check, not carry a second
  copy of its claim. Test 1 drifted because its assertion lived only in prose with nothing
  binding it; the rewrite states the standing guarantee is the validator's and reduces the
  page to a guided walk-through, and a test now executes the page's own assertion list
  against a real deployed ignore block. The durable form: **doc claims about mechanism
  behaviour either name the mechanism or get executed — prose alone is a second source of truth.**
- [DECISION] Diagnose "this whole tree is ignored by an outer repository" as its own
  cause with its own remedy — but **re-label, never re-decide**. Deployed under a
  `vendor/`-style ignore every probe resolves ignored, and per-probe blame points at the
  outer repo's directory rule. Run the probe loop first and only relabel when **all**
  probes came back ignored **and** `git rev-parse --show-prefix` is non-empty; that
  ordering cannot turn a PASS into a FAIL, and it reuses the same emission site so the
  ADR-006 native ratchet does not move.
- [CONSTRAINT] Do **not** use `git check-ignore -- .` as that discriminator. A blank CRLF
  line in `.gitignore` is not blank to git: it is the pattern `
`, which git strips to
  the empty string, and the empty pattern matches the pathspec `.`. So the probe returns
  "ignored" on every healthy `core.autocrlf=true` checkout — the Git-for-Windows default.
  Shipped in the first version of this branch and caught only because an independent
  reviewer ran the validators against **this** repository, whose own `.gitignore` is CRLF.
  Minimal repro: `printf '
' > .gitignore; git check-ignore -q --no-index -- .` exits 0.
  The general lesson is sharper than the flag: **a fresh-deploy fixture is not a checkout.**
  Fourteen scenarios all deployed clean LF trees and none of them could see this.
- [CONSTRAINT] ADR-006's native escape hatch applies here and was invoked without spending
  ratchet headroom: the guard must stay native because it is a FAIL-tier data-loss check
  and `run_python_check` degrades to a graceful SKIP on no-Python downstreams — unprotecting
  exactly the adopters it exists for — and the wrappers map exit!=0 to FAIL and cannot
  express the did-not-run SKIP. Net emission change was zero because the same unit deleted
  a branch that asserted a PASS without checking anything.
- [DECISION] No claim-decay mechanism (ADR-011 domain). The downstream report proposed
  `<!-- claim: verified-at <sha> -->` markers for quantified claims. Rejected on two
  grounds: the instance found here was mis-attributed — the SSoT's dated `### Ship-*`
  headings already anchor those measurements as history, not standing claims — and a
  "remember to tag" convention with no verifier is precisely the ritual-without-
  discriminating-power defect the same report diagnoses. **Reopen trigger**: a second
  quantified claim found false inside a *living* (non-dated) governance surface.
- [CONSTRAINT] A doc that ships downstream must be written for the downstream reader.
  `audit-guardrails.md` Test 1 was rewritten around `installers/deploy_brain.sh` and "the
  source repo root"; measured from an installed project, that wrapper clones from the
  remote, writes an `.agentcortex-src/` cache into the reader's own tree, and audits the
  fetched version rather than theirs. The canonical `.agentcortex/bin/deploy.sh` exists in
  both positions, needs no network, and audits the copy on disk.
- [TRADEOFF] A self-review by the author is structurally weaker than an independent one,
  and this unit measured the gap rather than asserting it: a tenth-man pass over my own
  diff returned PASS and found the defect that was *visible in the diff*; a delegated
  adversarial pass then found one CRITICAL and two MAJOR that required knowing
  `git check-ignore`'s exit semantics. Every finding was re-derived before being acted on.
