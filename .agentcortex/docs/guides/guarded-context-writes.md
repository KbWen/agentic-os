# Guarded Context Writes

Use `.agentcortex/tools/guard_context_write.py` as the single approved helper when writing SSoT files such as:

- `.agentcortex/context/current_state.md`
- `.agentcortex/context/archive/INDEX.md` (legacy compatibility mirror)

`.agentcortex/context/archive/INDEX.jsonl` is hash-chained: append to it only with `append_chain_entry.py` (`ship.md` §3), never with this helper. The runnable snapshot → write template is in `ship.md` §2.

Stage 1 keeps this helper **observable, not hard-blocking**:

- successful guarded writes update `.agentcortex/context/.guard_receipt.json`
- missing or stale receipts should produce warnings in validation and local hooks
- missing receipts do **not** block runtime execution in Stage 1

This preserves backward compatibility while making guarded-write drift visible in CI and downstream validation.
