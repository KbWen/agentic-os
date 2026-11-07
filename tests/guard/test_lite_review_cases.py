"""Offline screening controls only; not live review-completeness evidence."""
from pathlib import Path
import json
import re
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".agentcortex/tools"))
from run_governance_eval import _score_case  # noqa: E402

EVAL = ROOT / ".agentcortex/eval/lite-review.json"
CASES = json.loads(EVAL.read_text(encoding="utf-8"))["cases"]


def test_lite_does_not_cap_distinct_actionable_findings() -> None:
    text = (ROOT / ".agents/skills/red-team-adversarial/SKILL.md").read_text(encoding="utf-8")
    lite = text.split("### Lite Red Team (hotfix)", 1)[1].split("### Full Red Team", 1)[0]
    assert not re.search(r"\d+\s*findings max|≤\s*\d+\s*tokens", lite)
    assert "fix point" in lite


def test_oracles_cover_zero_one_and_multiple_without_prompt_keys() -> None:
    assert [len(c["_oracle"]["defects"]) for c in CASES] == [0, 1, 3]
    for case in CASES:
        assert "_oracle" not in case["prompt"]
        assert "reference_transcript" not in case["prompt"]
        assert "expected_defects" not in case["prompt"]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_reference_transcripts_pass_screening(case: dict) -> None:
    assert _score_case(case, case["_oracle"]["reference_transcript"])[0] == "pass"


def test_omitting_one_of_multiple_defects_fails_screening() -> None:
    case = CASES[2]
    partial = "\n\n".join(case["_oracle"]["reference_transcript"].split("\n\n")[:2])
    assert _score_case(case, partial)[0] == "fail"


def test_bare_keywords_are_not_a_complete_review() -> None:
    assert _score_case(CASES[2], "authorization server path traversal resolve unbounded limit")[0] == "fail"


def test_scope_expansion_is_rejected() -> None:
    case = CASES[2]
    report = case["_oracle"]["reference_transcript"] + "\n\nLocation: billing.py\nMechanism: unrelated.\nRemedy: rewrite it."
    assert _score_case(case, report)[0] == "fail"


def test_false_finding_in_clean_case_is_rejected() -> None:
    assert _score_case(CASES[0], "No actionable finding\nLocation: export_preview\nMechanism: invented.")[0] == "fail"


def _fixture_function(case: dict, root: Path):
    """Execute only the repository-owned fixture function with tiny temporary data."""
    code = "def export_preview" + case["prompt"].split("def export_preview", 1)[1]
    namespace = {"EXPORT_ROOT": root, "__builtins__": {"PermissionError": PermissionError, "str": str}}
    exec(compile(code, "<owned-review-fixture>", "exec"), namespace)
    return namespace["export_preview"]


def test_multiple_defect_oracle_reproduces_untrusted_role(tmp_path: Path) -> None:
    (tmp_path / "other-user.txt").write_bytes(b"fixture document")
    export = _fixture_function(CASES[2], tmp_path)
    result = export(SimpleNamespace(user_id="alice"),
                    {"role": "admin", "owner": "other", "filename": "other-user.txt"})
    assert result == b"fixture document"  # client role incorrectly grants access


def test_multiple_defect_oracle_reproduces_path_escape(tmp_path: Path) -> None:
    root = tmp_path / "exports"
    root.mkdir()
    (tmp_path / "outside.txt").write_bytes(b"outside fixture")
    export = _fixture_function(CASES[2], root)
    assert export(SimpleNamespace(user_id="alice"),
                  {"owner": "alice", "filename": "../outside.txt"}) == b"outside fixture"


def test_multiple_defect_oracle_reproduces_unbounded_read(tmp_path: Path) -> None:
    declared_preview_bound = 8
    (tmp_path / "document.txt").write_bytes(b"x" * 32)
    export = _fixture_function(CASES[2], tmp_path)
    result = export(SimpleNamespace(user_id="alice"), {"owner": "alice", "filename": "document.txt"})
    assert len(result) > declared_preview_bound


def test_existing_cli_accepts_cases_and_offline_transcripts(tmp_path: Path) -> None:
    for case in CASES:
        (tmp_path / (case["id"] + ".txt")).write_text(case["_oracle"]["reference_transcript"], encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / ".agentcortex/tools/run_governance_eval.py"),
         "--eval", str(EVAL), "--transcripts", str(tmp_path), "--format", "json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["summary"]["fail"] == 0
