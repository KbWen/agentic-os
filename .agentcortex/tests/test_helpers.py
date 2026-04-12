from __future__ import annotations

import re
from pathlib import Path


def sanitize_deployed_ssot(target: Path) -> None:
    """Rebuild SSoT indexes from tmpdir disk contents so completeness checks match reality."""
    ssot = target / ".agentcortex" / "context" / "current_state.md"
    if not ssot.exists():
        return
    content = ssot.read_text(encoding="utf-8")
    # Rebuild ADR Index from files actually present in tmpdir
    adr_lines = []
    for adr_dir in ["docs/adr", ".agentcortex/adr"]:
        d = target / adr_dir
        if d.is_dir():
            adr_lines += [f"  - {adr_dir}/{f.name}\n" for f in sorted(d.glob("ADR-*.md"))]
    replacement = r'\1\n' + ''.join(adr_lines) if adr_lines else r'\1 none\n'
    content = re.sub(r'(\*\*ADR Index\*\*:)\n(?:\s+-\s+\S.*\.md\n)*', replacement, content)
    # Replace Active Backlog value with none
    content = re.sub(r'(\*\*Active Backlog\*\*:)\s*`[^`]+`', r'\1 none', content)
    # Remove Spec Index file entries (keep header and instruction lines).
    # Support both older backtick-wrapped entries and current plain bullet entries.
    content = re.sub(
        r'(\*\*Spec Index\*\*[^:]*:)\n(?:\s+-\s+.*\n)*?(?=\s+-\s+When reading specs:|\s+-\s+Summary line helps AI decide relevance|$)',
        r'\1\n',
        content,
        flags=re.MULTILINE,
    )
    ssot.write_text(content, encoding="utf-8")
