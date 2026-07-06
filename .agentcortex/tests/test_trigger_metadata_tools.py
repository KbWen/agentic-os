import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".agentcortex" / "tools"))

from trigger_runtime_core import (
    assert_policy_allows_action,
    build_skill_registry_snapshot,
    cache_decision,
    load_json,
    load_skill_package_manifest,
    package_content_hash,
    parse_frontmatter,
    parse_simple_yaml,
    resolve_skill_execution_policy,
    resolve_skill_lockfile,
    validate_skill_manifest_authority,
    validate_skill_package_manifest,
    version_satisfies_range,
)


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def load_registry_entry(skill_id: str) -> dict[str, object]:
    if skill_id == "writing-plans":
        return {
            "id": "writing-plans",
            "kind": "skill",
            "canonical_ref": ".agent/skills/writing-plans",
            "mirror_ref": ".agents/skills/writing-plans/agents/openai.yaml",
            "detail_ref": ".agents/skills/writing-plans/SKILL.md",
        }
    registry = load_json(ROOT / ".agentcortex/metadata/trigger-registry.yaml")
    return next(candidate for candidate in registry["entries"] if candidate["id"] == skill_id)


def write_temp_skill_package(
    root: Path,
    skill_id: str,
    *,
    depends: list[dict[str, object]] | None = None,
    capabilities: list[str] | None = None,
    trust_tier_hint: str | None = None,
) -> None:
    skill_dir = root / ".agents" / "skills" / skill_id
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(f"# {skill_id}\n", encoding="utf-8")
    capability_lines = "\n".join(f"  - {capability}" for capability in (capabilities or ["read_repo"]))
    if depends:
        depends_lines = ["depends:"]
        for dependency in depends:
            dependency_id = dependency["id"]
            version_range = dependency["version_range"]
            required = str(dependency.get("required", True)).lower()
            reason = dependency.get("reason", "")
            depends_lines.extend(
                [
                    f"  - id: {dependency_id}",
                    f'    version_range: "{version_range}"',
                    f"    required: {required}",
                    f'    reason: "{reason}"',
                ]
            )
        depends_block = "\n".join(depends_lines)
    else:
        depends_block = "depends: []"
    trust_tier_block = f"trust_tier_hint: {trust_tier_hint}\n" if trust_tier_hint else ""
    manifest_template = f"""id: {skill_id}
name: {skill_id}
version: 1.0.0
description: temp package
engine_range: ">=5.4 <6.0"
entry_ref: SKILL.md
capabilities:
{capability_lines}
origin:
  publisher: Agentic OS
  channel: first-party
content_digest: sha256:PLACEHOLDER
lifecycle:
  status: active
{depends_block}
{trust_tier_block}"""
    manifest_path = skill_dir / "manifest.yaml"
    manifest_path.write_text(manifest_template, encoding="utf-8")
    digest = package_content_hash(skill_dir)
    manifest_path.write_text(manifest_template.replace("sha256:PLACEHOLDER", f"sha256:{digest}"), encoding="utf-8")


class TriggerMetadataToolTests(unittest.TestCase):
    # writing-plans was retired as a real skill in PR #114/#115 (inlined into plan.md),
    # but the skill-package-manifest system (load_skill_package_manifest, build_skill_registry_snapshot,
    # resolve_skill_lockfile, resolve_skill_execution_policy) remains under active strategic
    # direction per docs/architecture/skill-ecosystem.md (Near Term roadmap). No production skill
    # currently ships a manifest.yaml, so these tests stage a writing-plans fixture in a tempdir
    # to exercise the manifest system without polluting the real repo.

    def setUp(self) -> None:
        self._tmpdir_ctx = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir_ctx.cleanup)
        self.fixture_root = Path(self._tmpdir_ctx.name)

        summary_path = self.fixture_root / ".agent" / "skills" / "writing-plans"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text("""---
name: writing-plans
phases: [plan]
trigger_priority: hard
load_policy: phase-entry
cost_type: read
cost_risk: medium
runtime_anchor: ["AGENTS.md"]
description: temp package
---
""", encoding="utf-8")

        skill_dir = self.fixture_root / ".agents" / "skills" / "writing-plans"
        mirror_dir = skill_dir / "agents"
        mirror_dir.mkdir(parents=True, exist_ok=True)
        (mirror_dir / "openai.yaml").write_text("""display_name: writing-plans
description: temp package
short_description: temp package
agentcortex:
  summary_ref: .agent/skills/writing-plans
  detail_ref: .agents/skills/writing-plans/SKILL.md
  trigger_priority: hard
  phase_scope: [plan]
  load_policy: phase-entry
  cost_type: read
  cost_risk: medium
  runtime_anchor: ["AGENTS.md"]
""", encoding="utf-8")

        write_temp_skill_package(
            self.fixture_root,
            "writing-plans",
            capabilities=["read_repo"],
            trust_tier_hint="official",
        )

    def test_validator_passes_on_repo_state(self) -> None:
        result = run_tool(".agentcortex/tools/validate_trigger_metadata.py", "--root", ".")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("16 entries, 6 lifecycle scenarios, and fresh compact index parity", result.stdout)

    def test_compact_index_check_passes_on_repo_state(self) -> None:
        result = run_tool(".agentcortex/tools/generate_compact_index.py", "--root", ".", "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("compact index is fresh", result.stdout)

    def test_query_returns_compact_skill_slice(self) -> None:
        result = run_tool(
            ".agentcortex/tools/query_trigger_metadata.py",
            "--root",
            ".",
            "--ids",
            "test-driven-development",
            "auth-security",
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["source"], "compact-index")
        self.assertEqual(payload["count"], 2)
        ids = {entry["id"] for entry in payload["entries"]}
        self.assertEqual(ids, {"test-driven-development", "auth-security"})
        for entry in payload["entries"]:
            self.assertIn("runtime_anchor", entry)
            self.assertIn("fallback_behavior", entry)
            self.assertIn("content_hash", entry)
            self.assertNotIn("platforms", entry)

    def test_query_filters_by_phase_and_classification(self) -> None:
        result = run_tool(
            ".agentcortex/tools/query_trigger_metadata.py",
            "--root",
            ".",
            "--phase",
            "ship",
            "--classification",
            "feature",
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        ids = {entry["id"] for entry in payload["entries"]}
        self.assertIn("verification-before-completion", ids)
        self.assertNotIn("test-driven-development", ids)

    def test_lifecycle_analysis_reports_expected_scenarios(self) -> None:
        result = run_tool(
            ".agentcortex/tools/analyze_token_lifecycle.py",
            "--root",
            ".",
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        results = {entry["id"]: entry for entry in payload["results"]}

        self.assertIn("quick-win-single-module", results)
        self.assertIn("architecture-multi-agent", results)
        self.assertIn("feature-core-logic-tdd", results)
        self.assertEqual(results["quick-win-single-module"]["platforms"]["codex"]["probe_strategy"], "compact-index")
        self.assertEqual(results["architecture-multi-agent"]["platforms"]["codex"]["probe_strategy"], "compact-index")
        self.assertGreater(results["architecture-multi-agent"]["platforms"]["codex"]["delta_vs_current_tokens"], 0)
        self.assertGreater(results["quick-win-single-module"]["platforms"]["codex"]["delta_vs_current_tokens"], 0)
        self.assertGreater(results["feature-core-logic-tdd"]["platforms"]["codex"]["delta_vs_current_tokens"], 0)
        self.assertGreater(results["feature-core-logic-tdd"]["platforms"]["claude"]["delta_vs_current_tokens"], 0)
        self.assertEqual(
            results["feature-core-logic-tdd"]["platforms"]["codex"]["projected_total_tokens"],
            results["feature-core-logic-tdd"]["platforms"]["claude"]["projected_total_tokens"],
        )
        self.assertIn("workflow_scoped_tokens", results["feature-core-logic-tdd"])
        self.assertIn("continuation_tokens", results["feature-core-logic-tdd"])
        self.assertIn("compact_index_tokens", payload)
        self.assertFalse(results["feature-core-logic-tdd"]["workflow_scope_fallbacks"])

    def test_runtime_audit_reports_workflow_and_skill_coverage(self) -> None:
        result = run_tool(
            ".agentcortex/tools/audit_agent_runtime.py",
            "--root",
            ".",
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["all_workflows_ready"])
        self.assertTrue(payload["all_skills_auto_trigger_ready"])
        skills = {entry["skill"]: entry for entry in payload["skills"]}
        sd_hooks = skills["systematic-debugging"]["phase_hooks"]
        for phase in ("implement", "review", "test"):
            self.assertTrue(sd_hooks[phase]["ready"])
        # hotfix is a classification, not a phase — the phases carve-out was removed
        self.assertNotIn("hotfix", sd_hooks)

    def test_resolver_matches_across_platforms(self) -> None:
        outputs = []
        for platform in ("claude", "codex", "antigravity"):
            result = run_tool(
                ".agentcortex/tools/resolve_runtime_contract.py",
                "--root",
                ".",
                "--classification",
                "feature",
                "--phase",
                "implement",
                "--platform",
                platform,
                "--scope-signals",
                "testable logic,api endpoint,token",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            outputs.append(json.loads(result.stdout))

        self.assertEqual(outputs[0]["resolved_workflow"], outputs[1]["resolved_workflow"])
        self.assertEqual(outputs[1]["resolved_workflow"], outputs[2]["resolved_workflow"])
        self.assertEqual(outputs[0]["activated_skills"], outputs[1]["activated_skills"])
        self.assertEqual(outputs[1]["activated_skills"], outputs[2]["activated_skills"])
        self.assertIn("test-driven-development", outputs[0]["activated_skills"])
        self.assertIn("auth-security", outputs[0]["activated_skills"])

    def test_resolver_prefers_hash_cache_when_worklog_matches(self) -> None:
        compact_index = json.loads((ROOT / ".agentcortex/metadata/trigger-compact-index.json").read_text(encoding="utf-8"))
        tdd = next(entry for entry in compact_index["entries"] if entry["id"] == "test-driven-development")
        skill_notes_text = f"""### test-driven-development
- Content Hash: {tdd["content_hash"]}
- First Loaded Phase: implement
- Applies To: implement, test

#### implement
- Checklist: Write the failing test before changing production code for the current behavior slice.
- Checklist: Keep the production patch minimal until the targeted assertion turns green.
- Constraint: Do not merge multiple behavior changes into one cycle because the evidence trail must stay phase-local and reproducible.
"""
        decision = cache_decision(skill_notes_text, "test-driven-development", "implement", tdd["content_hash"])
        self.assertEqual(decision["action"], "use-cache")
        self.assertEqual(decision["reason"], "hash-match")

    def test_command_sync_check_passes_on_repo_state(self) -> None:
        result = run_tool(".agentcortex/tools/check_command_sync.py", "--root", ".")
        self.assertEqual(result.returncode, 0, result.stderr)
        # Source repos (with .agentcortex-manifest) legitimately skip command sync
        self.assertTrue(
            "Command sync check passed" in result.stdout
            or "Source repo detected" in result.stdout,
            f"Unexpected output: {result.stdout}",
        )

    def test_command_sync_expected_commands_plus_aliases_match_stub_count(self) -> None:
        """EXPECTED_COMMANDS + ALIAS_EXCLUSIONS must together account for every
        .claude/commands/*.md stub on disk (backlog #116) — no untracked gap,
        no overlap, and the two sets are disjoint by construction."""
        sys.path.insert(0, str(ROOT / ".agentcortex" / "tools"))
        import check_command_sync as checker

        stub_names = {
            p.stem for p in (ROOT / ".claude" / "commands").glob("*.md")
        }
        tracked = set(checker.EXPECTED_COMMANDS)
        aliased = set(checker.ALIAS_EXCLUSIONS)

        self.assertEqual(
            tracked & aliased, set(), "a command cannot be both tracked and alias-excluded"
        )
        self.assertEqual(
            tracked | aliased,
            stub_names,
            "EXPECTED_COMMANDS + ALIAS_EXCLUSIONS must exactly equal the set of "
            ".claude/commands/*.md stubs on disk — update both sides on drift",
        )

    def test_command_sync_alias_exclusions_have_workflow_and_target(self) -> None:
        """Each ALIAS_EXCLUSIONS entry must have its own redirect-stub workflow
        file and its command stub must still reference the documented target
        (guards against a silent alias retarget slipping past the checker)."""
        sys.path.insert(0, str(ROOT / ".agentcortex" / "tools"))
        import check_command_sync as checker

        for cmd, reason in checker.ALIAS_EXCLUSIONS.items():
            cmd_file = ROOT / ".claude" / "commands" / f"{cmd}.md"
            workflow_file = ROOT / ".agent" / "workflows" / f"{cmd}.md"
            self.assertTrue(cmd_file.is_file(), f"missing {cmd_file}")
            self.assertTrue(workflow_file.is_file(), f"missing {workflow_file}")

            target_ref = reason.rsplit("references ", 1)[-1].split(",")[0]
            content = cmd_file.read_text(encoding="utf-8")
            self.assertIn(
                target_ref,
                content,
                f".claude/commands/{cmd}.md no longer references documented alias target {target_ref}",
            )

    def test_writing_plans_manifest_validates(self) -> None:
        skill_dir = self.fixture_root / ".agents" / "skills" / "writing-plans"
        manifest = load_skill_package_manifest(skill_dir)
        self.assertIsNotNone(manifest)
        errors = validate_skill_package_manifest(skill_dir, manifest or {})
        self.assertEqual(errors, [])

    def test_writing_plans_manifest_authority_matches_repo_state(self) -> None:
        entry = load_registry_entry("writing-plans")
        summary = parse_frontmatter(self.fixture_root / entry["canonical_ref"])
        mirror = parse_simple_yaml((self.fixture_root / entry["mirror_ref"]).read_text(encoding="utf-8"))
        detail_path = self.fixture_root / entry["detail_ref"]
        manifest = load_skill_package_manifest(detail_path.parent)

        self.assertIsNotNone(manifest)
        errors = validate_skill_manifest_authority(
            entry=entry,
            summary=summary,
            mirror=mirror,
            manifest=manifest or {},
            detail_path=detail_path,
        )
        self.assertEqual(errors, [])

    def test_manifest_authority_reports_summary_and_mirror_drift(self) -> None:
        entry = load_registry_entry("writing-plans")
        summary = parse_frontmatter(self.fixture_root / entry["canonical_ref"])
        mirror = parse_simple_yaml((self.fixture_root / entry["mirror_ref"]).read_text(encoding="utf-8"))
        detail_path = self.fixture_root / entry["detail_ref"]
        manifest = load_skill_package_manifest(detail_path.parent)

        self.assertIsNotNone(manifest)
        drifted_summary = dict(summary)
        drifted_summary["description"] = "out-of-band summary text"
        drifted_mirror = dict(mirror)
        drifted_mirror["display_name"] = "Different skill name"

        errors = validate_skill_manifest_authority(
            entry=entry,
            summary=drifted_summary,
            mirror=drifted_mirror,
            manifest=manifest or {},
            detail_path=detail_path,
        )

        self.assertTrue(any("summary description must derive from manifest description" in error for error in errors), errors)
        self.assertTrue(any("mirror display_name must derive from manifest name" in error for error in errors), errors)

    def test_manifest_digest_mismatch_is_reported(self) -> None:
        skill_dir = self.fixture_root / ".agents" / "skills" / "writing-plans"
        manifest = load_skill_package_manifest(skill_dir)
        self.assertIsNotNone(manifest)
        mutated_manifest = dict(manifest or {})
        mutated_manifest["content_digest"] = "sha256:deadbeef"
        errors = validate_skill_package_manifest(skill_dir, mutated_manifest)
        self.assertTrue(any("content_digest does not match" in error for error in errors), errors)

    def test_registry_snapshot_includes_manifest_backed_packages(self) -> None:
        snapshot = build_skill_registry_snapshot(self.fixture_root)
        self.assertEqual(snapshot["version"], 1)
        self.assertEqual(snapshot["generated_from"], ".agents/skills")
        self.assertTrue(snapshot["snapshot_digest"].startswith("sha256:"))

        package = next(entry for entry in snapshot["packages"] if entry["id"] == "writing-plans")
        self.assertEqual(package["manifest_ref"], ".agents/skills/writing-plans/manifest.yaml")
        self.assertEqual(package["entry_ref"], "SKILL.md")
        self.assertEqual(package["lifecycle_status"], "active")

    def test_lockfile_resolution_pins_requested_package(self) -> None:
        snapshot = build_skill_registry_snapshot(self.fixture_root)
        lockfile = resolve_skill_lockfile(snapshot, ["writing-plans"])
        package = next(entry for entry in snapshot["packages"] if entry["id"] == "writing-plans")

        self.assertEqual(lockfile["version"], 1)
        self.assertEqual(lockfile["requested"], ["writing-plans"])
        self.assertEqual(lockfile["source_snapshot"]["snapshot_digest"], snapshot["snapshot_digest"])
        self.assertEqual(len(lockfile["resolved"]), 1)
        self.assertEqual(lockfile["resolved"][0]["id"], "writing-plans")
        self.assertEqual(lockfile["resolved"][0]["content_digest"], package["content_digest"])

    def test_lockfile_resolution_reports_missing_required_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_temp_skill_package(
                root,
                "primary-skill",
                depends=[{"id": "missing-skill", "version_range": "1.0.0", "required": True, "reason": "must exist"}],
            )
            snapshot = build_skill_registry_snapshot(root)
            with self.assertRaisesRegex(ValueError, "missing required dependency missing-skill"):
                resolve_skill_lockfile(snapshot, ["primary-skill"])

    def test_lockfile_resolution_reports_dependency_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_temp_skill_package(root, "dependency-skill")
            write_temp_skill_package(
                root,
                "primary-skill",
                depends=[{"id": "dependency-skill", "version_range": ">=2.0.0", "required": True, "reason": "must match"}],
            )
            snapshot = build_skill_registry_snapshot(root)
            with self.assertRaisesRegex(ValueError, "does not satisfy"):
                resolve_skill_lockfile(snapshot, ["primary-skill"])

    def test_lockfile_resolution_rejects_empty_request_set(self) -> None:
        snapshot = build_skill_registry_snapshot(ROOT)
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            resolve_skill_lockfile(snapshot, [])

    def test_lockfile_resolution_canonicalizes_requested_skill_sets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_temp_skill_package(root, "alpha")
            write_temp_skill_package(root, "beta")
            snapshot = build_skill_registry_snapshot(root)

            left = resolve_skill_lockfile(snapshot, ["alpha", "beta"])
            right = resolve_skill_lockfile(snapshot, ["beta", "alpha", "beta"])

            self.assertEqual(left, right)
            self.assertEqual(left["requested"], ["alpha", "beta"])
            self.assertEqual([entry["id"] for entry in left["resolved"]], ["alpha", "beta"])

    def test_lockfile_cli_emits_machine_readable_json(self) -> None:
        result = run_tool(
            ".agentcortex/tools/resolve_skill_lockfile.py",
            "--root",
            str(self.fixture_root),
            "--requested",
            "writing-plans",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["requested"], ["writing-plans"])
        self.assertEqual(payload["resolved"][0]["id"], "writing-plans")

    def test_policy_cli_emits_machine_readable_json(self) -> None:
        result = run_tool(
            ".agentcortex/tools/resolve_skill_lockfile.py",
            "--root",
            str(self.fixture_root),
            "--requested",
            "writing-plans",
            "--runtime",
            "codex",
            "--target-skill",
            "writing-plans",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["skill"]["id"], "writing-plans")
        self.assertEqual(payload["backend"]["runtime"], "codex")

    def test_version_range_helper_supports_conjunctive_ranges(self) -> None:
        self.assertTrue(version_satisfies_range("1.2.3", ">=1.0.0 <2.0.0"))
        self.assertFalse(version_satisfies_range("2.0.0", ">=1.0.0 <2.0.0"))

    def test_version_range_helper_ignores_build_metadata_in_precedence(self) -> None:
        self.assertTrue(version_satisfies_range("1.0.0+build.1", "==1.0.0"))
        self.assertTrue(version_satisfies_range("1.0.0+build.1", ">=1.0.0"))

    def test_version_range_helper_uses_semver_prerelease_ordering(self) -> None:
        self.assertTrue(version_satisfies_range("1.0.0-alpha.10", ">1.0.0-alpha.2"))
        self.assertTrue(version_satisfies_range("1.0.0-alpha.2", "<1.0.0-alpha.10"))

    def test_execution_policy_defaults_unverified_skills_to_most_restrictive_tier(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_temp_skill_package(root, "community-skill", capabilities=["read_repo", "write_docs"])
            snapshot = build_skill_registry_snapshot(root)

            artifact = resolve_skill_execution_policy(snapshot, ["community-skill"], "codex", "community-skill")

            self.assertEqual(artifact["trust_tier"], "unverified")
            self.assertEqual(artifact["effective_policy"]["files"]["read_scopes"], ["repo"])
            self.assertEqual(artifact["effective_policy"]["files"]["write_scopes"], [])

    def test_execution_policy_honors_repository_capability_narrowing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_temp_skill_package(
                root,
                "official-skill",
                capabilities=["read_repo", "write_docs"],
                trust_tier_hint="official",
            )
            snapshot = build_skill_registry_snapshot(root)

            artifact = resolve_skill_execution_policy(
                snapshot,
                ["official-skill"],
                "codex",
                "official-skill",
                repository_policy={"deny_capabilities": ["write_docs"]},
            )

            self.assertEqual(artifact["trust_tier"], "official")
            self.assertEqual(artifact["effective_policy"]["files"]["write_scopes"], [])

    def test_execution_policy_denies_undeclared_capability_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_temp_skill_package(root, "reader-skill", capabilities=["read_repo"], trust_tier_hint="official")
            snapshot = build_skill_registry_snapshot(root)
            artifact = resolve_skill_execution_policy(snapshot, ["reader-skill"], "codex", "reader-skill")

            with self.assertRaisesRegex(PermissionError, "not allowed"):
                assert_policy_allows_action(artifact, "shell", "execute")

    def test_execution_policy_fails_closed_when_backend_cannot_map_capability(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_temp_skill_package(
                root,
                "connector-skill",
                capabilities=["read_repo", "invoke_connector"],
                trust_tier_hint="official",
            )
            snapshot = build_skill_registry_snapshot(root)

            with self.assertRaisesRegex(ValueError, "cannot safely map"):
                resolve_skill_execution_policy(snapshot, ["connector-skill"], "antigravity", "connector-skill")


class SnapshotRootPathFormTests(unittest.TestCase):
    """Regression: snapshot must tolerate unresolved root path forms.

    GitHub windows-latest runners hand out %TEMP% as an 8.3 short path
    (RUNNER~1); build_skill_registry_snapshot resolved skill_root but not
    root, so every manifest relative_to(root) raised ValueError the first
    time this suite was CI-gated on Windows (PR #211).
    """

    @unittest.skipUnless(sys.platform == "win32", "8.3 short paths are Windows-only")
    def test_snapshot_accepts_8dot3_short_path_root(self) -> None:
        import ctypes

        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            write_temp_skill_package(root, "alpha-skill")
            buf = ctypes.create_unicode_buffer(260)
            if ctypes.windll.kernel32.GetShortPathNameW(str(root), buf, 260) == 0:
                self.skipTest("GetShortPathNameW failed")
            short_root = Path(buf.value)
            if str(short_root) == str(root):
                self.skipTest("filesystem has 8.3 name generation disabled")

            snapshot = build_skill_registry_snapshot(short_root)

            ids = [p["id"] for p in snapshot.get("packages", [])]
            self.assertIn("alpha-skill", ids)

    def test_snapshot_accepts_unresolved_relative_root(self) -> None:
        """Cross-platform cousin of the same defect class."""
        import os

        with tempfile.TemporaryDirectory() as base:
            write_temp_skill_package(Path(base), "beta-skill")
            cwd = os.getcwd()
            os.chdir(base)
            try:
                snapshot = build_skill_registry_snapshot(Path("."))
            finally:
                os.chdir(cwd)
            ids = [p["id"] for p in snapshot.get("packages", [])]
            self.assertIn("beta-skill", ids)


if __name__ == "__main__":
    unittest.main()
