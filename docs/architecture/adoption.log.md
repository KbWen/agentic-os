---
status: living
domain: adoption
---

# Adoption — Decision Log (L2)

### [adoption][2026-07-28][codex/skill-runtime-modernization]
cross-ref: See [skill-ecosystem][2026-07-28][codex/skill-runtime-modernization] in docs/architecture/skill-ecosystem.log.md

---

### [adoption][2026-09-27][fix/install-day-copy]
source_spec: — (quick-win; Work Log `.agentcortex/context/archive/fix-install-day-copy-20260927.md`)
source_sha: 870e4f8

- [DECISION] Claude Code users are told to start each task with the slash command
  (`/bootstrap <task>`), with the measured counts, instead of relying on `CLAUDE.md`
  prose: sessions that began with `/bootstrap` engaged 6/6, the prose preface 1/2, no hint
  0/3 (2026-09-26 simulation; a `CLAUDE.md` Work-Log clause measured 0/3 -> 0/3 and was
  reverted). A claim-triggered Stop hook was not reopened: Claude-only machinery with a
  parity cost. Reopen trigger: real adopter sessions where the documented entry does not
  change behaviour.
- [CONSTRAINT] A `--dry-run` preview must enumerate with the same globs as the deploy it
  previews; the two lists had drifted (26 vs 30 reference docs) because each kept its own.
