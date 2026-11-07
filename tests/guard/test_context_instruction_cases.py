"""Local fixture/scorer controls, not evidence of live-model or product benefit."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "context_eval_runner", ROOT / ".agentcortex/tools/run_governance_eval.py"
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def _cases():
    for path in sorted((ROOT / ".agentcortex/eval").glob("context-m*.json")):
        yield from json.loads(path.read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case", list(_cases()), ids=lambda case: case["id"])
def test_reference_passes_and_wrong_action_fails(case):
    assert runner._score_case(case, case["_oracle"]["reference"])[0] == "pass"
    assert runner._score_case(case, case["_oracle"]["counterexample"])[0] == "fail"


def test_m4_controls_have_distinct_authority_ground_truth():
    cases = json.loads((ROOT / ".agentcortex/eval/context-m4.json").read_text())["cases"]
    assert {c["_oracle"]["action"] for c in cases} == {
        "continue", "clarify", "approval", "reserved_decision"
    }
    assert sum(c["_oracle"]["action"] == "clarify" for c in cases) == 2
    for case in cases:
        assert "_oracle" not in case["prompt"]
        if case["_oracle"]["action"] != "continue":
            assert case["_oracle"]["allowed_paths"] == []


def test_m7_packet_requires_every_matching_skill():
    # M7 candidate retained-baseline (2026-11-07 comparison); the packet stays as a screen.
    cases = json.loads((ROOT / ".agentcortex/eval/context-m7.json").read_text())["cases"]
    assert [len(case["_oracle"]["required_skills"]) for case in cases] == [0, 1, 9]
    for skill in cases[-1]["_oracle"]["required_skills"]:
        missing = cases[-1]["_oracle"]["reference"].replace(skill, "")
        assert runner._score_case(cases[-1], missing)[0] == "fail"


def test_m3_semantic_screen_rejects_unsafe_slogan_echo():
    cases = {case["id"]: case for case in _cases()}
    case = cases["scope-a"]
    assert "UNAUTHORIZED REFACTORING" not in case["_oracle"]["reference"]
    assert "UNAUTHORIZED REFACTORING" in case["_oracle"]["counterexample"]
    assert case["_oracle"]["allowed_paths"] == ["src/rounding.py"]
    assert cases["scope-b"]["_oracle"]["action"] == "approved_refactor"


def test_m5_retains_lexical_order_and_host_neutral_fallback():
    text = (ROOT / ".agent/rules/engineering_guardrails.md").read_text(encoding="utf-8")
    section = text.split("### 9.3 ", 1)[1].split("### 9.4 ", 1)[0]
    assert "ALWAYS use lexical search first" in section
    assert "ONLY after lexical search yields no results" in section
    assert "ask a targeted question" in section


def test_no_duplicate_ids_or_oracle_exposure():
    cases = list(_cases())
    assert len({case["id"] for case in cases}) == len(cases)
    assert all("_oracle" not in case["prompt"] for case in cases)


@pytest.mark.parametrize("name", ["context-m4.json", "context-m7.json", "context-m9.json", "context-m3-m5.json"])
def test_existing_cli_scores_offline_packets(name, tmp_path):
    path = ROOT / ".agentcortex/eval" / name
    cases = json.loads(path.read_text(encoding="utf-8"))["cases"]
    for case in cases:
        (tmp_path / (case["id"] + ".txt")).write_text(case["_oracle"]["reference"], encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / ".agentcortex/tools/run_governance_eval.py"),
         "--eval", str(path), "--transcripts", str(tmp_path), "--format", "json"],
        capture_output=True, text=True, encoding="utf-8", check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["summary"]["fail"] == 0
