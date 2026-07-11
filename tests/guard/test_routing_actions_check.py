"""Structural tests for check_routing_actions.py (governance self-audit F3).

The native validators searched the whole review file for required-field
substrings and validated only standalone target_doc:/status: lines, so an inline
YAML map passed every substring check while escaping value validation. These
tests pin the structural fix: inline-map / fields-outside-block / traversal /
bad-status forms must FAIL, valid blocks PASS, and a column-0-only scope keeps
in-prose examples (an audit report quoting an attack fixture) from false-FAILing.

ADR: docs/adr/ADR-006-validator-python-core-strangler.md
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agentcortex" / "tools" / "check_routing_actions.py"
VALIDATE_SH = ROOT / ".agentcortex" / "bin" / "validate.sh"
VALIDATE_PS1 = ROOT / ".agentcortex" / "bin" / "validate.ps1"


def _write_review(root: Path, name: str, body: str) -> None:
    reviews = root / "docs" / "reviews"
    reviews.mkdir(parents=True, exist_ok=True)
    (reviews / name).write_text(body, encoding="utf-8")


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _fenced(records_yaml: str) -> str:
    return "# Review\n\n## routing_actions\n\n```yaml\n" + records_yaml + "```\n"


def _valid_block() -> str:
    return _fenced(
        "routing_actions:\n"
        '  - finding: "A real finding."\n'
        '    target_doc: "docs/architecture/foo.md"\n'
        "    status: pending\n"
        '    owner: "tester"\n'
    )


def _seed_target(root: Path) -> None:
    doc = root / "docs" / "architecture" / "foo.md"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("# foo\n", encoding="utf-8")


def test_valid_block_passes(tmp_path: Path) -> None:
    _seed_target(tmp_path)
    _write_review(tmp_path, "2099-01-01-ok.md", _valid_block())
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "structurally valid" in result.stdout


def test_inline_map_is_rejected(tmp_path: Path) -> None:
    """The core F3 fixture: an inline YAML map carries every required substring
    but must be rejected outright (values never validated otherwise)."""
    _write_review(
        tmp_path,
        "2099-01-01-inline.md",
        _fenced(
            "routing_actions:\n"
            '  - {finding: "x", target_doc: "../../escape.md", status: bogus, owner: y}\n'
        ),
    )
    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "inline-map form not permitted" in result.stdout


def test_path_traversal_target_is_rejected(tmp_path: Path) -> None:
    _write_review(
        tmp_path,
        "2099-01-01-traversal.md",
        _fenced(
            "routing_actions:\n"
            '  - finding: "x"\n'
            '    target_doc: "docs/architecture/../../etc/passwd.md"\n'
            "    status: pending\n"
            '    owner: "y"\n'
        ),
    )
    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "path traversal" in result.stdout or "target_doc must match" in result.stdout


def test_non_canonical_target_is_rejected(tmp_path: Path) -> None:
    _write_review(
        tmp_path,
        "2099-01-01-noncanon.md",
        _fenced(
            "routing_actions:\n"
            '  - finding: "x"\n'
            '    target_doc: "README.md"\n'
            "    status: pending\n"
            '    owner: "y"\n'
        ),
    )
    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr


def test_bad_status_is_rejected(tmp_path: Path) -> None:
    _seed_target(tmp_path)
    _write_review(
        tmp_path,
        "2099-01-01-status.md",
        _fenced(
            "routing_actions:\n"
            '  - finding: "x"\n'
            '    target_doc: "docs/architecture/foo.md"\n'
            "    status: bogus\n"
            '    owner: "y"\n'
        ),
    )
    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "status must be pending, merged, or rejected" in result.stdout


def test_required_field_outside_block_is_rejected(tmp_path: Path) -> None:
    """Fields-outside-block fixture: 'owner:' appears in prose elsewhere in the
    file, but the record itself omits it. The whole-file substring check passed
    this; structural parsing must reject the record."""
    _seed_target(tmp_path)
    body = (
        "# Review\n\nThe owner: of this finding is documented elsewhere.\n\n"
        "## routing_actions\n\n```yaml\n"
        "routing_actions:\n"
        '  - finding: "x"\n'
        '    target_doc: "docs/architecture/foo.md"\n'
        "    status: pending\n"
        "```\n"
    )
    _write_review(tmp_path, "2099-01-01-missingfield.md", body)
    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "missing required field 'owner'" in result.stdout


def test_nonexistent_target_is_warn_not_fail(tmp_path: Path) -> None:
    """A well-formed target_doc that does not exist on disk is advisory (WARN),
    not a structural failure — preserving the native 'exists → WARN' behavior."""
    _write_review(tmp_path, "2099-01-01-missingdoc.md", _valid_block())
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "does not exist yet" in result.stdout
    assert result.stdout.count("WARN:") >= 1


def test_indented_example_is_ignored(tmp_path: Path) -> None:
    """A routing_actions block quoted INSIDE a list item (indented, column>0) is
    an example, not the canonical block — it must not FAIL the report."""
    body = (
        "# Audit Report\n\n"
        "- Isolated fixture used:\n\n"
        "  ```yaml\n"
        "  routing_actions:\n"
        '    - {finding: "x", target_doc: "../../escape.md", status: bogus, owner: y}\n'
        "  ```\n"
    )
    _write_review(tmp_path, "2099-01-01-example.md", body)
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_non_list_form_is_rejected(tmp_path: Path) -> None:
    _write_review(
        tmp_path,
        "2099-01-01-nonlist.md",
        _fenced("routing_actions:\n  just a bare scalar, not a list\n"),
    )
    result = _run(tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "no valid action records" in result.stdout


def test_no_reviews_dir_passes(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_real_repo_passes() -> None:
    """The framework's own review snapshots must be structurally valid."""
    result = subprocess.run(
        [sys.executable, str(TOOL), "--root", str(ROOT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_both_validators_wire_structural_check_with_native_backstop() -> None:
    """Cross-platform parity: both validators invoke check_routing_actions.py
    behind the python seam AND retain the native block as the no-python backstop."""
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    for text, which in ((sh, "validate.sh"), (ps1, "validate.ps1")):
        assert "check_routing_actions.py" in text, f"{which} missing structural tool wiring"
        assert "routing_actions contract (structural)" in text, f"{which} missing python check label"
        # Native no-python backstop must still be present (else-branch).
        assert "routing_actions contract is structurally valid when present" in text, (
            f"{which} dropped the native no-python backstop"
        )
