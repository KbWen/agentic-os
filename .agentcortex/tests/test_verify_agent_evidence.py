import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


TOOL = Path(__file__).resolve().parents[1] / "tools" / "verify_agent_evidence.py"


def run_tool(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def build_work_log(
    *,
    classification: str = "feature",
    phases: str = "- bootstrap\n- spec\n- plan\n- implement\n- review\n- test\n- handoff\n- ship",
    task_description: str = "- implement path safety improvements",
    external_references: str = "- none",
    known_risk: str = "- mitigation recorded",
    conflict_resolution: str = "- none",
    skill_notes: str = "none",
    evidence: str = "Command: python -m pytest -q test_sample.py\nResult: pass\nSummary: sample test passes",
    recommended_skills: str = "none",
) -> str:
    return "\n".join(
        [
            "# Work Log: sample",
            "",
            "- **Branch**: codex/sample",
            f"- **Classification**: {classification}",
            "- **Owner**: codex",
            f"- **Recommended Skills**: {recommended_skills}",
            "",
            "## Task Description",
            task_description,
            "",
            "## Phase Sequence",
            phases,
            "",
            "## External References",
            external_references,
            "",
            "## Known Risk",
            known_risk,
            "",
            "## Conflict Resolution",
            conflict_resolution,
            "",
            "## Skill Notes",
            skill_notes,
            "",
            "## Evidence",
            evidence,
            "",
        ]
    )


class VerifyAgentEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        write_file(
            self.root / ".agentcortex/context/current_state.md",
            """
            ## Global Lessons
            - [Category: path-safety][Severity: HIGH][Trigger: bulk-rename] Validate path rewrites after bulk rename operations.
            """,
        )
        write_file(
            self.root / ".agent/rules/skill_conflict_matrix.md",
            """
            | Skill A | Skill B | Relation | Guidance |
            | --- | --- | --- | --- |
            | dispatching-parallel-agents | test-driven-development | partial-conflict | Keep TDD on the critical path. |
            """,
        )
        write_file(
            self.root / "test_sample.py",
            """
            def test_sample():
                assert True
            """,
        )

    def test_passes_for_valid_feature_work_log(self) -> None:
        write_file(
            self.root / ".agentcortex/context/work/sample.md",
            build_work_log(
                external_references="- Ref: https://example.invalid/official-doc",
                known_risk="- bulk rename risks documented and mitigated",
            ),
        )
        result = run_tool(
            self.root,
            "--root",
            ".",
            "--path",
            ".agentcortex/context/work/sample.md",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Verified `python -m pytest -q test_sample.py`", result.stdout)

    def test_missing_required_section_fails(self) -> None:
        write_file(
            self.root / ".agentcortex/context/work/sample.md",
            """
            # Work Log: sample

            - **Branch**: codex/sample
            - **Classification**: feature

            ## Task Description
            - missing core sections

            ## Evidence
            Command: python -m pytest -q test_sample.py
            Result: pass
            Summary: sample test passes
            """,
        )
        result = run_tool(
            self.root,
            "--root",
            ".",
            "--path",
            ".agentcortex/context/work/sample.md",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required section `## Phase Sequence`", result.stderr)
        self.assertIn("missing required section `## Skill Notes`", result.stderr)

    def test_invalid_feature_phase_sequence_fails(self) -> None:
        write_file(
            self.root / ".agentcortex/context/work/sample.md",
            build_work_log(phases="- bootstrap\n- plan\n- implement\n- ship"),
        )
        result = run_tool(
            self.root,
            "--root",
            ".",
            "--path",
            ".agentcortex/context/work/sample.md",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid phase sequence", result.stderr)

    def test_in_progress_reviewable_sequence_is_allowed(self) -> None:
        write_file(
            self.root / ".agentcortex/context/review/sample.md",
            build_work_log(
                phases="- bootstrap\n- spec\n- plan\n- implement\n- review",
                external_references="- Ref: https://example.invalid/official-doc",
            ),
        )
        result = run_tool(
            self.root,
            "--root",
            ".",
            "--path",
            ".agentcortex/context/review/sample.md",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("in-progress phase sequence accepted", result.stdout)

    def test_review_rework_sequence_is_allowed(self) -> None:
        write_file(
            self.root / ".agentcortex/context/review/sample.md",
            build_work_log(
                phases="- bootstrap\n- spec\n- plan\n- implement\n- review\n- implement",
                external_references="- Ref: https://example.invalid/official-doc",
            ),
        )
        result = run_tool(
            self.root,
            "--root",
            ".",
            "--path",
            ".agentcortex/context/review/sample.md",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("in-progress phase sequence accepted", result.stdout)

    def test_phase_sequence_after_ship_fails(self) -> None:
        write_file(
            self.root / ".agentcortex/context/review/sample.md",
            build_work_log(
                phases="- bootstrap\n- spec\n- plan\n- implement\n- review\n- test\n- ship\n- implement",
                external_references="- Ref: https://example.invalid/official-doc",
            ),
        )
        result = run_tool(
            self.root,
            "--root",
            ".",
            "--path",
            ".agentcortex/context/review/sample.md",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid phase sequence", result.stderr)

    def test_high_lesson_trigger_without_known_risk_warns(self) -> None:
        write_file(
            self.root / ".agentcortex/context/work/sample.md",
            build_work_log(
                task_description="- bulk rename for module paths",
                known_risk="- none",
                external_references="- Ref: https://example.invalid/official-doc",
            ),
        )
        result = run_tool(
            self.root,
            "--root",
            ".",
            "--path",
            ".agentcortex/context/work/sample.md",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("HIGH Global Lesson trigger `bulk-rename` matched task description", result.stdout)

    def test_skill_conflict_without_resolution_warns(self) -> None:
        write_file(
            self.root / ".agentcortex/context/work/sample.md",
            build_work_log(
                recommended_skills="dispatching-parallel-agents (parallel tasks), test-driven-development (test first)",
                conflict_resolution="- none",
                external_references="- Ref: https://example.invalid/official-doc",
            ),
        )
        result = run_tool(
            self.root,
            "--root",
            ".",
            "--path",
            ".agentcortex/context/work/sample.md",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("`partial-conflict`", result.stdout)

    def test_dependency_manifest_change_without_external_references_warns(self) -> None:
        git(self.root, "init")
        git(self.root, "config", "user.email", "codex@example.com")
        git(self.root, "config", "user.name", "Codex")
        write_file(self.root / "package.json", '{ "name": "sample" }\n')
        write_file(
            self.root / ".agentcortex/context/review/sample.md",
            build_work_log(external_references="none"),
        )
        git(self.root, "add", ".")
        initial_commit = git(self.root, "commit", "-m", "baseline")
        self.assertEqual(initial_commit.returncode, 0, initial_commit.stderr)
        base_sha = git(self.root, "rev-parse", "HEAD").stdout.strip()

        write_file(self.root / "package.json", '{ "name": "sample", "version": "1.0.0" }\n')
        write_file(
            self.root / ".agentcortex/context/review/sample.md",
            build_work_log(
                external_references="- none",
                evidence="Command: python -m pytest -q test_sample.py\nResult: pass\nSummary: manifest change tracked",
            ),
        )
        git(self.root, "add", ".")
        second_commit = git(self.root, "commit", "-m", "change manifest")
        self.assertEqual(second_commit.returncode, 0, second_commit.stderr)
        head_sha = git(self.root, "rev-parse", "HEAD").stdout.strip()

        result = run_tool(
            self.root,
            "--root",
            ".",
            "--base-sha",
            base_sha,
            "--head-sha",
            head_sha,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("dependency manifest changed but `## External References` is empty", result.stdout)

    def test_diff_mode_is_quiet_when_repo_did_not_opt_in_to_review_mirrors(self) -> None:
        git(self.root, "init")
        git(self.root, "config", "user.email", "codex@example.com")
        git(self.root, "config", "user.name", "Codex")
        write_file(self.root / "README.md", "baseline\n")
        git(self.root, "add", ".")
        initial_commit = git(self.root, "commit", "-m", "baseline")
        self.assertEqual(initial_commit.returncode, 0, initial_commit.stderr)
        base_sha = git(self.root, "rev-parse", "HEAD").stdout.strip()

        write_file(self.root / "README.md", "updated\n")
        git(self.root, "add", "README.md")
        second_commit = git(self.root, "commit", "-m", "docs change")
        self.assertEqual(second_commit.returncode, 0, second_commit.stderr)
        head_sha = git(self.root, "rev-parse", "HEAD").stdout.strip()

        result = run_tool(
            self.root,
            "--root",
            ".",
            "--base-sha",
            base_sha,
            "--head-sha",
            head_sha,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PR-visible evidence checks are not enabled", result.stdout)

    def test_diff_mode_warns_when_opted_in_repo_skips_reviewable_log_update(self) -> None:
        git(self.root, "init")
        git(self.root, "config", "user.email", "codex@example.com")
        git(self.root, "config", "user.name", "Codex")
        write_file(self.root / ".agentcortex/context/review/.gitkeep", "")
        write_file(self.root / "README.md", "baseline\n")
        git(self.root, "add", ".")
        initial_commit = git(self.root, "commit", "-m", "baseline")
        self.assertEqual(initial_commit.returncode, 0, initial_commit.stderr)
        base_sha = git(self.root, "rev-parse", "HEAD").stdout.strip()

        write_file(self.root / "README.md", "updated\n")
        git(self.root, "add", "README.md")
        second_commit = git(self.root, "commit", "-m", "docs change")
        self.assertEqual(second_commit.returncode, 0, second_commit.stderr)
        head_sha = git(self.root, "rev-parse", "HEAD").stdout.strip()

        result = run_tool(
            self.root,
            "--root",
            ".",
            "--base-sha",
            base_sha,
            "--head-sha",
            head_sha,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Evidence verification was skipped", result.stdout)

    def test_suspicious_evidence_argument_is_marked_unverified(self) -> None:
        write_file(
            self.root / ".agentcortex/context/work/sample.md",
            build_work_log(
                external_references="- Ref: https://example.invalid/official-doc",
                evidence=(
                    "Command: python -m pytest -q test_sample.py --tb=short\n"
                    "Result: pass\n"
                    "Summary: safe rerun\n\n"
                    "Command: python -m pytest /etc/passwd\n"
                    "Result: pass\n"
                    "Summary: suspicious absolute path"
                ),
            ),
        )
        result = run_tool(
            self.root,
            "--root",
            ".",
            "--path",
            ".agentcortex/context/work/sample.md",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Verified `python -m pytest -q test_sample.py --tb=short`", result.stdout)
        self.assertIn("UNVERIFIED: command `python -m pytest /etc/passwd` contains suspicious arguments.", result.stdout)


if __name__ == "__main__":
    unittest.main()
