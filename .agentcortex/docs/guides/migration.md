# Migration & Integration Guide (vNext)

This guide describes how to upgrade the legacy template to vNext and how to introduce the system into ongoing projects.

---

## 1. Project A: Legacy Upgrade Path

The core goal of upgrading to vNext: **"Transition from process-driven to state-driven."**

### Step 1: Code Update

```bash
./deploy_brain.sh /path/to/project-a
```

> [!NOTE]
> `deploy_brain.sh` defaults to `cp -n` (no overwrite for existing files); your custom settings will not be overwritten.
> Add the `--force` flag to force-update all files.
> The script also automatically updates the `.gitignore` of the target project.

### Step 2: AI Automated Migration

Instruct the AI to perform a migration scan:

```text
Please run /bootstrap.
We've just upgraded to vNext v3.5.2.
Please scan the project for existing documentation and perform the following:
1. Identify scattered notes, specs, and ADRs; move them to correct directories and rename.
2. Initialize .agentcortex/context/current_state.md.
3. Create Work Logs for ongoing tasks.
```

The AI will automatically perform:

| AI Logic | Action | Target Location |
| :--- | :--- | :--- |
| Historical ARCH decision records | Move & Name as `ADR-NNN-<topic>.md` | `docs/adr/` |
| Feature specs or requirements | Move & Name as `<feature-name>.md` | `docs/specs/` |
| Ongoing task logs | Move & Name as `<branch-name>.md` | `.agentcortex/context/work/` |
| Completed historical logs | Move & Name as original filename | `.agentcortex/context/archive/` |
| Unclassifiable files | No action; list in report for review | Original location |

> [!IMPORTANT]
> After the scan, the AI will output a migration plan (mapping sources to targets). It will NOT move or delete files without user confirmation.

### Step 3: Verification

- Review the AI's migration plan; reply `OK` to confirm.
- AI executes the move and updates `.agentcortex/context/current_state.md`.
- From here, `/ship` will automatically maintain the SSoT.

---

## 2. Project B: Legacy Project / Mid-Task Integration

Focus: **"Catch-up; the AI organizes, no manual preprocessing needed."**

### Step 1: Environment Deployment

```bash
./deploy_brain.sh /path/to/project-b
```

### Step 2: Raw Material Processing & Archiving

Use vNext's automated processing capabilities. **No manual organization required**:

```text
Please run /bootstrap.
Integration into an mid-development project.
Please perform:
1. Process the following raw discussion materials, extract specs to docs/specs/.
2. Scan existing project files, automatically classify and move.
3. Initialize .agentcortex/context/current_state.md.
4. Create Work Logs for ongoing tasks.
---
[Paste TODO lists, chat logs, project specs, or any cluttered raw data]
---
```

### Step 3: AI Automated Refactoring

The AI will follow the vNext logic:

1. **Extract Specs**: Convert raw materials into detailed specs in `docs/specs/<feature-name>.md`.
2. **Scan Existing Files**: Identify scattered docs and determine classification/naming.
3. **Output Migration Plan**: List all proposed moves/renames for user confirmation.
4. **Establish Map**: Produce `.agentcortex/context/current_state.md` to describe the project overview.
5. **Establish Tasks**: Create Work Logs (`.agentcortex/context/work/<worklog-key>.md`) for active work.

### Regarding Directory Conflicts

If the project already has a `docs/` directory (e.g., API docs, manuals), the template's `.agentcortex/context/`, `docs/specs/`, and `docs/adr/` directories will be isolated and **not** interfere with existing `docs/api/`, `docs/architecture/`, etc.

---

## 💡 FAQ

**Q: Will the AI automatically delete my files?**
A: No. The AI only **proposes moves** and awaits user confirmation. Unclassifiable files remain untouched.

**Q: Can I organize files manually instead of using AI?**
A: Absolutely. Manually placing files in correct directories is most token-efficient. AI migration is a convenience option.

**Q: Can I delete old `superpowers/features/` files?**
A: Recommended after confirming the new `.agent/workflows/` process works correctly.

**Q: What if there's too much data for the AI to process?**
A: Batch it. Provide core specs via `/bootstrap` for SSoT; then provide details via `/research`.
