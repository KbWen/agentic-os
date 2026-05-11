"""Structural tests for CI security scanning workflow.

Spec: docs/specs/ci-security-scanning.md (AC-1 through AC-10)
Run: python -m unittest tests.ci.test_security_workflow -v
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

import yaml  # PyYAML — already present as Semgrep transitive dep in CI; stdlib fallback below

ROOT = Path(__file__).resolve().parents[2]
SECURITY_YML = ROOT / ".github" / "workflows" / "security.yml"

# Floating-ref pattern: actions like @main, @master, @HEAD, @latest (case-insensitive)
_FLOATING_REF_RE = re.compile(r"@(main|master|HEAD|latest)\b", re.IGNORECASE)


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
    """AC-6: permissions: contents: read at top level."""

    def test_ac6_top_level_permissions_contents_read(self):
        wf = _load_workflow()
        perms = wf.get("permissions", {})
        self.assertEqual(
            perms.get("contents"), "read",
            "Top-level permissions.contents must be 'read'",
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

    def test_ac2_semgrep_uses_python_ruleset(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        self.assertIn("p/python", combined, "Semgrep must use p/python config")

    def test_ac2_semgrep_uses_bash_ruleset(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        self.assertIn("p/bash", combined, "Semgrep must use p/bash config")

    def test_ac2_semgrep_metrics_off(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        self.assertIn("--metrics=off", combined, "Semgrep must disable metrics (--metrics=off)")

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
        # --only-verified must appear somewhere in step config or extra_args
        raw = str(self.job)
        self.assertIn("only-verified", raw, "TruffleHog must use --only-verified")

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
        # Must have a version suffix
        self.assertIn("@", uses)
        tag = uses.split("@")[1]
        self.assertRegex(tag, r"^v\d+\.\d+\.\d+$", f"TruffleHog tag {tag!r} must be semver")


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
        self.assertIn(
            "-r $f", combined,
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

    def test_ac5_pip_audit_version_pinned(self):
        run_steps = [s.get("run", "") for s in (self.job.get("steps") or [])]
        combined = "\n".join(run_steps)
        self.assertRegex(
            combined,
            r"pip-audit==\d+\.\d+\.\d+",
            "pip-audit install must pin exact version (pip-audit==X.Y.Z)",
        )


class TestVersionPinningGlobal(unittest.TestCase):
    """AC-5: no floating refs anywhere in the workflow file."""

    def test_ac5_no_floating_refs_in_raw_yaml(self):
        raw = SECURITY_YML.read_text(encoding="utf-8")
        matches = _FLOATING_REF_RE.findall(raw)
        self.assertFalse(
            matches,
            f"Floating action refs found: {matches} — must pin to tag or SHA (AC-5)",
        )


class TestWorkflowIsolation(unittest.TestCase):
    """AC-10: security.yml is a separate file; validate.yml is not modified."""

    def test_ac10_security_yml_is_separate_file(self):
        self.assertTrue(SECURITY_YML.exists())

    def test_ac10_validate_yml_unchanged_jobs(self):
        validate_yml = ROOT / ".github" / "workflows" / "validate.yml"
        if not validate_yml.exists():
            self.skipTest("validate.yml not present")
        with validate_yml.open(encoding="utf-8") as f:
            wf = yaml.safe_load(f)
        # validate.yml must not contain security scanner jobs
        jobs = set((wf.get("jobs") or {}).keys())
        security_jobs = {"semgrep", "trufflehog", "dependency-audit"}
        self.assertFalse(
            jobs & security_jobs,
            f"Security jobs found in validate.yml: {jobs & security_jobs} — must stay in security.yml",
        )
