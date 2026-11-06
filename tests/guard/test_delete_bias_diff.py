"""End-to-end checks for the DELETE-bias comparison's completeness gate."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".agentcortex/tools/run_delete_bias_diff.sh"
RUNNER = ROOT / ".agentcortex/tools/run_governance_eval.py"
git_path = shutil.which("git")
git_root = Path(git_path).parent.parent if git_path else None
_bash_candidates = [
    str(git_root / "bin" / "bash.exe") if git_root else None,
    str(git_root / "usr" / "bin" / "bash.exe") if git_root else None,
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    shutil.which("bash"),
]
BASH = next(
    (
        item for item in _bash_candidates
        if item and "WindowsApps".casefold() not in item.casefold() and Path(item).exists()
    ),
    None,
)
requires_bash = pytest.mark.skipif(BASH is None, reason="bash not available")


def _run_diff(tmp_path: Path, baseline: object, mutated: object) -> subprocess.CompletedProcess[str]:
    before = tmp_path / "baseline.json"
    after = tmp_path / "mutated.json"
    before.write_text(json.dumps(baseline), encoding="utf-8")
    after.write_text(json.dumps(mutated), encoding="utf-8")
    return subprocess.run(
        [BASH, str(SCRIPT), "--baseline", str(before), "--mutated", str(after)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
        check=False,
        timeout=30,
    )


def _result(*cases: tuple[str, str]) -> dict[str, object]:
    return {"cases": [{"id": case_id, "status": status} for case_id, status in cases]}


@requires_bash
@pytest.mark.parametrize(
    ("baseline", "mutated"),
    [
        pytest.param(_result(), _result(), id="empty-pair"),
        pytest.param(_result(("a", "skipped")), _result(("a", "skipped")), id="skipped-pair"),
        pytest.param(_result(("a", "error")), _result(("a", "error")), id="error-pair"),
        pytest.param(_result(("a", "pass")), _result(("b", "pass")), id="different-cohort"),
        pytest.param(_result(("a", "pass"), ("b", "fail")), _result(("a", "pass")), id="baseline-only-case"),
        pytest.param(_result(("a", "pass")), _result(("a", "pass"), ("b", "fail")), id="mutated-only-case"),
        pytest.param(
            {"cases": [{"id": "a", "status": "pass"}, {"id": "a", "status": "fail"}]},
            _result(("a", "pass")),
            id="duplicate-id",
        ),
        pytest.param([], _result(("a", "pass")), id="bad-top-level"),
        pytest.param({}, {"cases": [{"id": "a", "status": "pass"}]}, id="missing-cases"),
        pytest.param({"cases": {}}, {"cases": [{"id": "a", "status": "pass"}]}, id="non-list-cases"),
        pytest.param({"cases": ["bad row"]}, {"cases": [{"id": "a", "status": "pass"}]}, id="non-object-case"),
        pytest.param({"cases": [{}]}, {"cases": [{"id": "a", "status": "pass"}]}, id="missing-id"),
        pytest.param({"cases": [{"id": "a", "status": "pass"}, {"id": "  ", "status": "fail"}]}, _result(("a", "pass")), id="blank-id"),
        pytest.param({"cases": [{"id": "a"}]}, _result(("a", "pass")), id="missing-status"),
        pytest.param(_result(("a", "unknown")), _result(("a", "pass")), id="unknown-status"),
    ],
)
def test_incomplete_or_malformed_pairs_exit_without_verdict(
    tmp_path: Path, baseline: object, mutated: object
) -> None:
    result = _run_diff(tmp_path, baseline, mutated)
    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    assert "verdict:" not in output.lower(), output
    assert "INCOMPLETE comparison" in output, output


@requires_bash
def test_complete_equal_cohorts_keep_vacuous_signal(tmp_path: Path) -> None:
    result = _run_diff(tmp_path, _result(("a", "pass"), ("b", "fail")), _result(("a", "pass"), ("b", "fail")))
    assert result.returncode == 0, result.stderr
    assert "Verdict: rule appears VACUOUS" in result.stdout


@requires_bash
def test_complete_changed_statuses_keep_load_bearing_signal(tmp_path: Path) -> None:
    result = _run_diff(tmp_path, _result(("a", "pass"), ("b", "fail")), _result(("a", "fail"), ("b", "pass")))
    assert result.returncode == 0, result.stderr
    assert "2 case(s) changed status" in result.stdout
    assert "Verdict: rule appears LOAD-BEARING" in result.stdout


@requires_bash
def test_malformed_json_exits_without_echoing_payload_or_verdict(tmp_path: Path) -> None:
    before = tmp_path / "baseline.json"
    after = tmp_path / "mutated.json"
    before.write_text('{"cases": [', encoding="utf-8")
    after.write_text(json.dumps(_result(("a", "pass"))), encoding="utf-8")
    result = subprocess.run(
        [BASH, str(SCRIPT), "--baseline", str(before), "--mutated", str(after)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=ROOT,
        check=False,
        timeout=30,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0, output
    assert "INCOMPLETE comparison" in output
    assert "verdict:" not in output.lower()
    assert '{"cases": [' not in output


def test_runner_still_reports_missing_transcript_as_skipped_with_exit_zero(tmp_path: Path) -> None:
    eval_file = tmp_path / "small-eval.yaml"
    eval_file.write_text(
        "cases:\n"
        "  - id: alpha\n"
        "    prompt: sample\n"
        "    protects: AGENTS.md section\n"
        "    expect_substrings: [expected]\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(RUNNER), "--eval", str(eval_file), "--transcripts", str(tmp_path / "empty"), "--format", "json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["cases"] == [
        {"id": "alpha", "status": "skipped", "failed_expectations": []}
    ]
