# AgentCortex Runtime v5

## Antigravity Hard-Path Enforcement Overlay

Version: v5.0
Date: 2026-03-04
Scope: **Antigravity environments** (token-generation agents where shell exit codes don’t halt execution)

### Why v5 exists

AgentCortex v3.5+ already enforces strong process gates via workflows:

* `/bootstrap` reads SSoT + Work Log, locks classification, and only allows upward changes via rollback + re-entry
* `/plan` is “NO CODING YET” and requires spec for feature/architecture-change
* `/implement` has a hard gate `state >= IMPLEMENTABLE` and scope escalation checks
* `/ship` requires state TESTED and handoff for non-tiny-fix, then updates SSoT via guarded writes. `/retro` is the only non-ship SSoT write exception, and only for structured Global Lessons.
* AGENTS.md is injected every turn and already defines write isolation + evidence requirements

**Remaining issue:** Antigravity sometimes “continues anyway” even when a workflow says STOP (because STOP is still text).
Runtime v5 adds **hard generation-path checkpoints** that are short, deterministic, and token-cheap.

---

## Architecture Diagram

```mermaid
flowchart LR

    %% ==========================================
    %% Styles
    %% ==========================================
    classDef entry fill:#f3f3f3,stroke:#666,stroke-width:1px,color:#333
    classDef gov fill:#fcdede,stroke:#e74c3c,stroke-width:2px,color:#333
    classDef rt fill:#e8daf8,stroke:#9b59b6,stroke-width:2px,color:#333
    classDef wf fill:#d1ecf1,stroke:#31708f,stroke-width:2px,color:#333
    classDef art fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#333
    classDef kl fill:#fff3cd,stroke:#f1c40f,stroke-width:2px,color:#333
    classDef decision fill:#e8daf8,stroke:#9b59b6,stroke-width:2px,color:#333

    %% ==========================================
    %% Entry
    %% ==========================================
    U["User Input<br/>Natural Language or Slash"]:::entry --> IR

    %% ==========================================
    %% Governance
    %% ==========================================
    subgraph GOV ["GOVERNANCE SHELL (Constraint Layer)"]
        direction TB
        A1["AGENTS.md<br/>Runtime v4 Minimal Contract"]:::gov
        A2[".agent/rules<br/>engineering_guardrails.md + others"]:::gov
        A3["Write Isolation<br/>SSoT controlled writes"]:::gov
    end

    %% ==========================================
    %% Runtime
    %% ==========================================
    subgraph RT ["RUNTIME LAYER (Enforcement & Logic)"]
        direction TB
        IR["Intent Router<br/>NL == Slash"]:::rt
        CL{"Classifier<br/>tiny-fix / quick-win /<br/>hotfix / feature / arch-change"}:::decision
        ESC["Escalation Check<br/>rollback + upgrade if scope grows"]:::rt
        GATE["Gate Engine<br/>Minimal Gate Block"]:::rt
        HS["Handshake (High Risk Only)<br/>PROCEED-PLAN / PROCEED-SHIP /<br/>PROCEED-IMPLEMENT"]:::rt
        SM["State Machine<br/>Plan→Implement→Review→Ship→Learn"]:::rt
        STOP["STOP<br/>wait for user"]:::entry
        U2(["Done fast path"]):::entry
    end

    %% ==========================================
    %% Workflows
    %% ==========================================
    subgraph WF ["WORKFLOWS LAYER (Operations)"]
        W4["/bootstrap<br/>bootstrap-report ONLY"]:::wf
        W1[".agent/workflows/plan.md"]:::wf
        W2[".agent/workflows/handoff.md"]:::wf
        W3[".agent/workflows/ship.md"]:::wf
    end

    %% ==========================================
    %% Artifacts
    %% ==========================================
    subgraph ART ["ARTIFACTS LAYER (Outputs)"]
        SPECS["docs/specs/&lt;feature&gt;.md"]:::art
        WL[".agentcortex/context/work/&lt;worklog-key&gt;.md<br/>Work Log + Drift + Evidence"]:::art
        SSOT[".agentcortex/context/current_state.md<br/>SSoT (controlled writes)"]:::art
        CODE["src/** + tests/**"]:::art
        GUIDE["docs/guides/antigravity-anti-drift.md"]:::art
    end

    %% ==========================================
    %% Knowledge Loop
    %% ==========================================
    subgraph KL ["KNOWLEDGE LOOP (Learning)"]
        EV["Evidence Ledger<br/>tests / verification"]:::kl
        EX["/retro + /ship<br/>lessons + ship refs"]:::kl
        GL["Global Lessons<br/>structured guarded append"]:::kl
    end

    %% ==========================================
    %% Governance injection (dotted)
    %% ==========================================
    U -.-> A1
    U -.-> A2
    U -.-> A3
    GUIDE -. "reference" .-> A1
    A3 -. "controls" .-> SSOT

    %% ==========================================
    %% Intent + classification
    %% ==========================================
    IR --> CL --> ESC

    %% ==========================================
    %% /bootstrap special path
    %% ==========================================
    ESC -->|"/bootstrap"| W4 --> STOP
    STOP -->|"Next: /plan or tiny-fix"| IR

    %% ==========================================
    %% tiny-fix fast path (skip gate/handshake/worklog)
    %% ==========================================
    ESC -->|"tiny-fix"| CODE
    ESC -->|"tiny-fix"| U2
    A2 -. "guardrails apply" .-> CODE

    %% ==========================================
    %% non-tiny-fix paths
    %% ==========================================
    ESC -->|"quick-win / hotfix"| GATE
    ESC -->|"feature / arch-change"| GATE

    %% Gate results
    GATE -->|"FAIL"| WL --> STOP
    STOP -->|"User fixes missing → rerun"| IR

    %% Gate PASS splits: handshake only for high-risk
    GATE -->|"PASS + feature/arch-change"| HS
    GATE -->|"PASS + quick-win/hotfix"| SM

    %% Handshake actions
    HS -->|"PROCEED-PLAN"| W1
    HS -->|"PROCEED-IMPLEMENT"| CODE
    HS -->|"PROCEED-SHIP"| W3

    %% Workflow outputs
    W1 --> SPECS
    W1 --> WL
    SM --> CODE --> EV --> WL
    SM --> W2 --> WL
    SM --> W3 --> EX --> GL --> SSOT --> IR
    W3 --> EV
```

---

## 1) Runtime v5 Contract (Minimal, Always-On)

### 1.1 NL == Slash intent equivalence

Natural language must map to canonical workflows **before any output**.
This is consistent with AGENTS.md being loaded every turn.

**Trigger examples:**

| Trigger example                             | Route      |
| ------------------------------------------- | ---------- |
| “help me design”, “幫我規劃”, “plan this”       | `/plan`    |
| “ship this”, “完成了”, “finalize”              | `/ship`    |
| “typo”, “rename variable”, “comment change” | `tiny-fix` |

If unclear: default to `/plan` and record “NL fallback” in Work Log Drift Log.

---

## 2) Minimal Gate Block (Antigravity proof)

Before **any** `/plan` or `/ship` execution (non-tiny-fix), the agent MUST output the following YAML **and nothing else**:

```yaml
gate: plan|ship
classification: tiny-fix|quick-win|hotfix|feature|architecture-change
branch: <git_branch_or_worklog_name>
checks:
  worklog_exists: yes|no
  spec_exists: yes|no|na
  state_ok: yes|no
  handoff_ok: yes|no|na
verdict: pass|fail
missing: []
```

### 2.1 Detection rules

* **Branch**: use git branch if available; else infer from `.agentcortex/context/work/<worklog-key>.md` naming convention.
* **Work Log resolution**: normalize the branch into a filesystem-safe `<worklog-key>` before checking `worklog_exists`. If the active log is recoverable, create or recover it before returning `verdict: fail`.
* **Spec**: for `feature` / `architecture-change`, spec must exist per `/plan` “Spec Gate” behavior.
* **State**:
  * `/implement` hard gate requires `state >= IMPLEMENTABLE`
  * `/ship` requires state `TESTED`
* **Handoff**: for non-tiny-fix, `/ship` requires `/handoff` completed.

### 2.2 Fail behavior (Instructional Rejection)

If `verdict: fail`:

* output **only** the gate block (with `missing` populated)
* STOP (no plan, no code, no doc edits)

This keeps the agent inside a deterministic “verify first” path.

---

## 3) Two-Turn Handshake (High-risk only)

Your workflows already separate phases (plan vs implement), but Antigravity can still “overrun” in a single response.
Runtime v5 adds a **user-controlled continuation token**.

Handshake applies only to:

* `feature`
* `architecture-change`

### 3.1 Plan handshake

After a passing gate for `/plan` high-risk tasks:

> Gate passed. Reply **PROCEED-PLAN** to continue.

Then STOP.

**When user replies `PROCEED-PLAN`:**

* produce **plan only** (no code), consistent with `/plan` “NO CODING YET”.

### 3.2 Implement handshake (prevents Plan→Implement drift)

After plan is approved and Work Log contains a plan section:

> Gate passed. Reply **PROCEED-IMPLEMENT** to continue.

Requirement:

* Must cite Work Log plan section (path + heading) before writing code.

### 3.3 Ship handshake

After a passing gate for `/ship` high-risk tasks:

> Gate passed. Reply **PROCEED-SHIP** to continue.

Then STOP.

---

## 4) /bootstrap Hard Stop (Antigravity specific)

* `/bootstrap` outputs **bootstrap-report only**, then STOP.
* Next step must be `/plan` (or tiny-fix).
* **No code output** is allowed immediately after bootstrap.

---

## 5) Docs-first requirement (front-load documentation)

For `feature` / `architecture-change`, plan output MUST include:

```text
Docs:
- <at least one path in docs/specs/ or .agentcortex/context/>
```

---

## 6) Scope rule (reduce classification ambiguity)

To avoid the model “choosing tiny-fix because it’s easiest,” add this deterministic boundary:

* `< 5 lines` and **no logic change** → `tiny-fix`
* **bug fix** isolated to one area/module → `hotfix`
* **new behavior** / cross-file / new module → `feature`

If “tiny-fix” touches logic or multiple files, escalate to `hotfix`.

---

## 7) Evidence discipline remains canonical

AgentCortex already enforces “NO EVIDENCE = NO COMPLETION” at the AGENTS.md level and in shipping.
Runtime v5 clarifies the minimum:

* At least **one** test command OR verification output must be recorded (Work Log Evidence section).
* If evidence is empty, `/ship` must be rejected.

---

## 8) Sentinel Check (Injection Diagnostic)

**SENTINEL: ACX-READ-OK**

Add this to the first line of `AGENTS.md`.
Every response MUST end with `[ACX-READ-OK]`.
If this token is missing, it signifies the prompt injection is broken or truncated.

---

## 9) Definition of Done for Runtime v5

In Antigravity, for any high-risk task:

1. Gate YAML printed first
2. PASS → waits for PROCEED token
3. PROCEED-PLAN → plan only (no code)
4. PROCEED-IMPLEMENT → code changes (scoped)
5. evidence recorded
6. PROCEED-SHIP → ship package + SSoT update

If any required artifact is missing, output MUST be limited to:

* gate block + missing list

---

## End of Runtime v5 Spec
