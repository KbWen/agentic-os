"""Structural tests for CI security scanning workflow.

Spec: docs/specs/ci-security-scanning.md (AC-1 through AC-11)
Run: python -m pytest tests/ci/test_security_workflow.py -v
"""

from __future__ import annotations

import re
import sys
import unittest

import pytest
from pathlib import Path

try:
    import yaml
    _PYYAML_AVAILABLE = True
except ImportError:
    yaml = None  # type: ignore[assignment]
    _PYYAML_AVAILABLE = False

ROOT = Path(__file__).resolve().parents[2]
SECURITY_YML = ROOT / ".github" / "workflows" / "security.yml"
VALIDATE_YML = ROOT / ".github" / "workflows" / "validate.yml"
DEPENDABOT_YML = ROOT / ".github" / "dependabot.yml"

# Floating-ref denylist: known mutable branch/alias names used as action refs.
# Intentionally does NOT match @v4 / @v5 — version tags are not floating branch refs.
# SHA enforcement for ALL actions (incl. first-party) is asserted separately by
# test_ac5_security_and_validate_actions_use_commit_sha (AC-5).
_FLOATING_REF_RE = re.compile(
    r"@(main|master|HEAD|latest|develop|dev|trunk|stable|edge|next|nightly|release|current"
    r"|beta|alpha|rc|canary|preview|unstable|snapshot|experimental|pre)\b",
    re.IGNORECASE,
)


def setUpModule():  # noqa: N802
    if not _PYYAML_AVAILABLE:
        raise unittest.SkipTest("pyyaml not installed — pip install pyyaml")


def _load_workflow() -> dict:
    with SECURITY_YML.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestSecurityWorkflowExists(unittest.TestCase):
    """AC-1: workflow file must exist at the declared path."""

    def test_ac1_security_yml_exists(self):
        self.assertTrue(
            SECURITY_YML.exists(),
            f"security.yml not found at {SECURITY_YML}",
        )

    def test_ac1_security_yml_is_valid_yaml(self):
        wf = _load_workflow()
        self.assertIsInstance(wf, dict)

    def test_ac1_triggers_push_and_pr_on_main(self):
        wf = _load_workflow()
        # PyYAML parses bare `on:` as Python True (YAML 1.1 boolean); handle both forms.
        on = wf.get("on") or wf.get(True) or {}
        self.assertIn("push", on, "missing push trigger")
        self.assertIn("pull_request", on, "missing pull_request trigger")
        self.assertIn("main", on["push"]["branches"], "push must target main")
        self.assertIn("main", on["pull_request"]["branches"], "pull_request must target main")


class TestSecurityWorkflowPermissions(unittest.TestCase):
    """AC-6: permissions: contents: read at top level; no job escalates to write."""

    def test_ac6_top_level_permissions_contents_read(self):
        wf = _load_workflow()
        perms = wf.get("permissions", {})
        self.assertEqual(
            perms.get("contents"), "read",
            "Top-level permissions.contents must be 'read'",
        )

    def test_ac6_no_job_level_contents_write(self):
        wf = _load_workflow()
        for job_name, job in (wf.get("jobs") or {}).items():
            perms = job.get("permissions")
            if perms is None:
                continue
            if isinstance(perms, str):
                # scalar forms like `permissions: write-all` are also prohibited
                self.assertNotIn(
                    perms.lower(), ("write-all", "write"),
                    f"Job '{job_name}' uses scalar permissions '{perms}' — prohibited (AC-6)",
                )
            elif isinstance(perms, dict):
                self.assertNotEqual(
                    perms.get("contents"), "write",
                    f"Job '{job_name}' escalates contents to write — prohibited (AC-6)",
                )
            else:
                self.fail(
                    f"Job '{job_name}' has unexpected permissions type {type(perms).__name__!r}: {perms!r}",
                )


class TestSecurityWorkflowNoContinueOnError(unittest.TestCase):
    """AC-7: no job uses continue-on-error: true."""

    def test_ac7_no_continue_on_error_in_any_job(self):
        wf = _load_workflow()
        for job_name, job in (wf.get("jobs") or {}).items():
            self.assertNotEqual(
                job.get("continue-on-error"), True,
                f"Job '{job_name}' has continue-on-error: true — prohibited (AC-7)",
            )

    def test_ac7_no_step_level_continue_on_error(self):
        wf = _load_workflow()
        for job_name, job in (wf.get("jobs") or {}).items():
            for i, step in enumerate((job.get("steps") or [])):
                self.assertNotEqual(
                    step.get("continue-on-error"), True,
                    f"Step {i} in job '{job_name}' has continue-on-error: true — "
                    "step-level suppression also prohibited (AC-7)",
                )


class TestSemgrepJob(unittest.TestCase):
    """AC-2: semgrep job with p/python + p/bash, --metrics=off, --error, pinned version."""

    def setUp(self):
        wf = _load_workflow()
        self.job = (wf.get("jobs") or {}).get("semgrep", {})

    def test_ac2_semgrep_job_exists(self):
        self.assertTrue(self.job, "jobs.semgrep missing")

    def test_ac2_semgrep_step_present(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        self.assertIn("semgrep", combined, "No semgrep invocation found in steps")

    def test_ac2_semgrep_uses_auto_config(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        self.assertIn(
            "--config auto", combined,
            "Semgrep must use --config auto (language-agnostic; no hardcoded language rulesets)",
        )

    def test_ac2_semgrep_config_flag_present(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        self.assertIn("--config", combined, "Semgrep must specify --config")

    def test_ac2_semgrep_no_metrics_off(self):
        # Semgrep 1.123.0+ rejects --config auto when --metrics=off is set.
        # Telemetry is aggregate stats only (no repo contents) — constraint satisfied without the flag.
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        self.assertNotIn("--metrics=off", combined,
            "Do not use --metrics=off with --config auto (Semgrep 1.123.0+ incompatibility)")

    def test_ac2_semgrep_error_flag(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        self.assertIn("--error", combined, "Semgrep must exit non-zero on finding (--error)")

    def test_ac5_semgrep_version_pinned(self):
        # install step must pin exact semgrep version (pip install semgrep==X.Y.Z)
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        self.assertRegex(
            combined,
            r"semgrep==\d+\.\d+\.\d+",
            "Semgrep pip install must pin an exact version (semgrep==X.Y.Z)",
        )


class TestTruffleHogJob(unittest.TestCase):
    """AC-3 & AC-5: TruffleHog job pinned, only-verified."""

    def setUp(self):
        wf = _load_workflow()
        self.job = (wf.get("jobs") or {}).get("trufflehog", {})

    def test_ac3_trufflehog_job_exists(self):
        self.assertTrue(self.job, "jobs.trufflehog missing")

    def test_ac3_trufflehog_only_verified(self):
        # --only-verified must appear in the extra_args of the trufflehog action step
        th_steps = [
            s for s in (self.job.get("steps") or [])
            if "trufflehog" in str(s.get("uses", "")).lower()
        ]
        self.assertTrue(th_steps, "No TruffleHog action step found")
        extra_args = (th_steps[0].get("with") or {}).get("extra_args", "")
        self.assertIn("--only-verified", extra_args,
                      "TruffleHog must use --only-verified in extra_args")

    def test_ac3_checkout_full_depth(self):
        checkout_steps = [
            s for s in (self.job.get("steps") or [])
            if "checkout" in str(s.get("uses", ""))
        ]
        self.assertTrue(checkout_steps, "No checkout step found in trufflehog job")
        checkout = checkout_steps[0]
        fetch_depth = (checkout.get("with") or {}).get("fetch-depth", 1)
        self.assertEqual(fetch_depth, 0, "TruffleHog checkout must use fetch-depth: 0")

    def test_ac5_trufflehog_version_pinned(self):
        th_steps = [
            s for s in (self.job.get("steps") or [])
            if "trufflehog" in str(s.get("uses", "")).lower()
        ]
        self.assertTrue(th_steps, "No TruffleHog action step found")
        uses = th_steps[0].get("uses", "")
        self.assertNotEqual(uses, "", "TruffleHog step missing 'uses' field")
        self.assertFalse(
            _FLOATING_REF_RE.search(uses),
            f"TruffleHog action uses floating ref: {uses!r} — must pin to tag or SHA",
        )
        # Third-party actions (non actions/*) MUST use a 40-char commit SHA per AC-5.
        # Semver tags are mutable and do not provide supply-chain immutability.
        self.assertIn("@", uses)
        tag = uses.split("@")[1]
        self.assertRegex(
            tag,
            r"^[0-9a-fA-F]{40}$",
            f"TruffleHog tag {tag!r} must be a 40-char commit SHA — semver tags are mutable (AC-5)",
        )


class TestDependencyAuditJob(unittest.TestCase):
    """AC-4 & AC-5: pip-audit conditional on requirements files, -r flags, pinned version."""

    def setUp(self):
        wf = _load_workflow()
        self.job = (wf.get("jobs") or {}).get("dependency-audit", {})

    def test_ac4_dependency_audit_job_exists(self):
        self.assertTrue(self.job, "jobs.dependency-audit missing")

    def test_ac4_pip_audit_invoked(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        self.assertIn("pip-audit", combined, "pip-audit must be invoked in dependency-audit job")

    def test_ac4_conditional_on_requirements_files(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        # Must check for requirements files before running
        self.assertTrue(
            "requirements" in combined or "pyproject.toml" in combined,
            "dependency-audit must be conditional on requirements files",
        )

    def test_ac4_uses_r_flag_for_requirements(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        # pip-audit must use -r for requirements files (not audit CI env).
        # Checks semantic presence; does not couple to exact variable form ($f vs array).
        self.assertIn(
            "-r ", combined,
            "pip-audit must use -r flag per requirements file (not audit CI env)",
        )

    def test_ac4_uses_osv_vulnerability_service(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        self.assertIn("osv", combined, "pip-audit must use --vulnerability-service osv")

    def test_ac4_skip_when_no_requirements(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        self.assertIn("skipping", combined.lower(), "Must have skip message when no requirements found")

    def test_ac4_pyproject_toml_project_mode(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        # When only pyproject.toml exists, pip-audit . audits the project's deps.
        # Guard must check for [project]/[build-system] before invoking project mode.
        self.assertIn("pip-audit .", combined,
                      "pip-audit must use project mode (pip-audit .) for pyproject.toml-only repos")
        # grep pattern uses \[project\] / \[build-system\] (escaped brackets for regex literal match)
        # so check for the word itself, not the bracket-wrapped form
        self.assertIn("build-system", combined,
                      "pyproject.toml branch must guard on [project] or [build-system] presence")

    def test_ac5_pip_audit_version_pinned(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        self.assertRegex(
            combined,
            r"pip-audit==\d+\.\d+\.\d+",
            "pip-audit install must pin exact version (pip-audit==X.Y.Z)",
        )

    def test_ac4_strict_flag(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        self.assertIn(
            "--strict", combined,
            "pip-audit must use --strict to exit non-zero on any finding (AC-4)",
        )


class TestCredentialScanFailClosed(unittest.TestCase):
    """AC-8: credential-scan step must fail-closed on rc==3 (scanner execution error)."""

    def setUp(self):
        wf = _load_workflow()
        self.job = (wf.get("jobs") or {}).get("credential-scan", {})

    def test_ac8_credential_scan_job_exists(self):
        self.assertTrue(self.job, "jobs.credential-scan missing")

    def test_ac8_rc3_not_exit_zero(self):
        """rc==3 (scanner could not run) must NOT be exit 0 — fail-closed required."""
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        # Find the rc==3 branch — must exist and must NOT exit 0.
        self.assertIn(
            '"3"', combined,
            "credential-scan step must handle rc==3 (scanner execution error)",
        )
        # Locate the rc==3 block and verify it does not contain a bare 'exit 0'.
        # Split on the rc==3 guard, take the first block after it.
        parts = combined.split('"3"')
        self.assertGreater(
            len(parts), 1,
            "rc==3 guard not found in credential-scan step",
        )
        rc3_block = parts[1]
        # The block ends at the next `fi` (end of if block). Extract up to that.
        fi_pos = rc3_block.find("\n          fi\n")
        if fi_pos != -1:
            rc3_block = rc3_block[:fi_pos]
        self.assertNotIn(
            "exit 0", rc3_block,
            "credential-scan: rc==3 branch must NOT exit 0 — must fail-closed (AC-8)",
        )

    def test_ac8_base_sha_missing_still_exits_zero(self):
        """The base-sha-missing path (nothing to scan) must keep exit 0 — that is legitimate."""
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        # The base-sha guard precedes the actual scan — it exits 0 legitimately.
        self.assertIn(
            "exit 0", combined,
            "credential-scan: base-sha-missing path must still exit 0 (nothing to scan — AC-8)",
        )


class TestDependencyAuditCIManifest(unittest.TestCase):
    """AC-9: pip-audit must also scan .github/requirements-ci.txt (the repo's only real Python manifest)."""

    def setUp(self):
        wf = _load_workflow()
        self.job = (wf.get("jobs") or {}).get("dependency-audit", {})

    def test_ac9_ci_requirements_manifest_included(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        self.assertIn(
            ".github/requirements-ci.txt",
            combined,
            "dependency-audit must include .github/requirements-ci.txt "
            "(the repo's only real Python manifest — AC-9)",
        )


class TestVersionPinningGlobal(unittest.TestCase):
    """AC-5: no floating refs or mutable tags anywhere in workflow uses lines."""

    def test_ac5_no_floating_refs_in_raw_yaml(self):
        # Anchor search to `uses:` lines only — avoids false positives from comments
        # or SSH-style URLs (e.g. git@main.example.com) elsewhere in the file.
        raw = SECURITY_YML.read_text(encoding="utf-8")
        uses_lines = [ln for ln in raw.splitlines() if re.search(r"^\s*-?\s*uses:", ln)]
        matches = [m for ln in uses_lines for m in _FLOATING_REF_RE.findall(ln)]
        self.assertFalse(
            matches,
            f"Floating action refs in uses: lines: {matches} — must pin to tag or SHA (AC-5)",
        )

    def test_ac5_security_and_validate_actions_use_commit_sha(self):
        workflow_paths = [SECURITY_YML, VALIDATE_YML]
        bad = []
        for workflow_path in workflow_paths:
            raw = workflow_path.read_text(encoding="utf-8")
            for line_no, line in enumerate(raw.splitlines(), start=1):
                if not re.search(r"^\s*-?\s*uses:", line):
                    continue
                uses = line.split("uses:", 1)[1].split("#", 1)[0].strip()
                ref = uses.split("@", 1)[1] if "@" in uses else ""
                if not re.fullmatch(r"[0-9a-fA-F]{40}", ref):
                    bad.append(f"{workflow_path.relative_to(ROOT)}:{line_no}: {uses}")
        self.assertFalse(
            bad,
            "Workflow actions must use immutable 40-char commit SHAs, not mutable tags: "
            + "; ".join(bad),
        )

    def test_ac5_dependabot_github_actions_updates_have_cooldown(self):
        self.assertTrue(DEPENDABOT_YML.exists(), "Dependabot config must exist for action pin refreshes")
        with DEPENDABOT_YML.open(encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        updates = cfg.get("updates") or []
        github_action_updates = [
            update for update in updates
            if update.get("package-ecosystem") == "github-actions"
        ]
        self.assertTrue(github_action_updates, "Dependabot must manage github-actions updates")
        missing = []
        for update in github_action_updates:
            default_days = (update.get("cooldown") or {}).get("default-days")
            if not isinstance(default_days, int) or default_days < 7:
                missing.append(update.get("directory", "<missing-directory>"))
        self.assertFalse(
            missing,
            "github-actions Dependabot updates must set cooldown.default-days >= 7: "
            + ", ".join(missing),
        )


@pytest.mark.docs_pin
class TestClaimsVsReality(unittest.TestCase):
    """AC-7 (dev-flow-hardening): security spec must not overstate enforcement reality.

    The security jobs run on every PR but are NOT required merge checks (branch
    protection only requires Framework Validation, ShellCheck, Check Markdown Links).
    The spec Goal must not claim security runs 'before merge … no human opt-in required'
    as an unconditional guarantee.
    """

    _SPEC = ROOT / "docs" / "specs" / "ci-security-scanning.md"
    # Phrases that incorrectly imply security is an unconditional pre-merge gate.
    _FALSE_GATE_PHRASES = [
        "before merge, with no human opt-in required",
    ]

    def test_ac7_spec_goal_does_not_claim_unconditional_pre_merge_gate(self):
        if not self._SPEC.exists():
            self.skipTest(f"Spec not found: {self._SPEC}")
        content = self._SPEC.read_text(encoding="utf-8")
        for phrase in self._FALSE_GATE_PHRASES:
            self.assertNotIn(
                phrase,
                content,
                f"ci-security-scanning.md Goal must not claim security is an unconditional "
                f"pre-merge required gate (found: {phrase!r}). Security jobs are advisory "
                f"unless branch protection requires them. (AC-7)",
            )

    def test_ac7_spec_documents_required_checks(self):
        """Spec must document the actual required check set for this repo."""
        if not self._SPEC.exists():
            self.skipTest(f"Spec not found: {self._SPEC}")
        content = self._SPEC.read_text(encoding="utf-8")
        required_checks = ["Framework Validation", "ShellCheck", "Check Markdown Links"]
        for check in required_checks:
            self.assertIn(
                check,
                content,
                f"ci-security-scanning.md must document the actual required merge check "
                f"{check!r} so readers understand the real enforcement floor (AC-7)",
            )


class TestWorkflowIsolation(unittest.TestCase):
    """AC-10: security.yml is a separate file; security jobs do not bleed into validate.yml."""

    def test_ac10_security_yml_is_separate_file(self):
        self.assertTrue(SECURITY_YML.exists())

    def test_ac10_security_jobs_not_in_validate_yml(self):
        self.assertTrue(
            VALIDATE_YML.exists(),
            "validate.yml must exist — accidental deletion should be a FAIL, not a skip",
        )
        with VALIDATE_YML.open(encoding="utf-8") as f:
            wf = yaml.safe_load(f)
        jobs = set((wf.get("jobs") or {}).keys())
        security_jobs = {"semgrep", "trufflehog", "dependency-audit"}
        self.assertFalse(
            jobs & security_jobs,
            f"Security jobs found in validate.yml: {jobs & security_jobs} — must stay in security.yml",
        )
        # Core validate jobs must all still exist (guard against accidental deletion)
        expected_core = {"validate", "shellcheck"}
        self.assertTrue(
            expected_core.issubset(jobs),
            f"Core validate jobs missing from validate.yml: {expected_core - jobs}",
        )
        # AC-10: test-ci-structural job must exist (it is the AC-10 evidence runner)
        self.assertIn(
            "test-ci-structural", jobs,
            "validate.yml must contain additive test-ci-structural job (AC-10)",
        )

    def test_semgrepignore_exists(self):
        # .semgrepignore prevents false positives from test fixtures / installers
        # blocking every PR via --error. Its accidental deletion would not be caught
        # by any other test, so we assert it explicitly.
        semgrepignore = ROOT / ".semgrepignore"
        self.assertTrue(
            semgrepignore.exists(),
            ".semgrepignore must exist at repo root to prevent Semgrep false positives "
            "on test fixtures and installer scripts (--config auto + --error)",
        )

    def test_semgrepignore_excludes_fixture_dirs(self):
        """AC-11: .semgrepignore must exclude the directories that contain
        intentional bad-pattern examples so --config auto --error never fails on them."""
        semgrepignore = ROOT / ".semgrepignore"
        if not semgrepignore.exists():
            self.skipTest(".semgrepignore missing — covered by test_semgrepignore_exists")
        content = semgrepignore.read_text(encoding="utf-8")
        required_exclusions = ["tests/", "installers/", ".agentcortex/templates/"]
        for entry in required_exclusions:
            self.assertIn(
                entry, content,
                f".semgrepignore must exclude '{entry}' (contains intentional bad patterns)",
            )
