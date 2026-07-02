"""Downstream file-preservation tiering tests (ADR-005) + override activation
structural tests (ADR-004).

Spec: docs/specs/downstream-fork-accommodation.md (AC-1..AC-10).

Behavioral tests shell out to the real deploy.sh into a temp target and assert:
  - AC-6: a user-modified framework SKILL is preserved via .acx-incoming sidecar
    (skills are scaffold-tier), and a net-new custom-* skill is never touched.
  - AC-5: a user-modified framework-authoritative core file (a rule) is
    force-updated with NO sidecar (governance must not drift).
Structural tests guard the wiring/parity against silent deletion.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


def _lf_sha256(path: Path) -> str:
    """Return the hex SHA-256 of ``path`` after normalizing CRLF → LF.

    This mirrors what ``compute_sha256_normalized`` in deploy.sh does
    (``tr -d '\\r'`` before hashing).  Used in EOL-hash mutation guards
    to assert that the manifest stores LF-normalized hashes.
    """
    raw = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"")
    return hashlib.sha256(raw).hexdigest()


def _manifest_hash(manifest: Path, rel: str) -> str | None:
    """Parse the .agentcortex-manifest and return the hash for *rel*, or None."""
    if not manifest.exists():
        return None
    for line in manifest.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        # format: <tier> <rel_path> sha256:<hash>
        if len(parts) >= 3 and parts[1] == rel:
            h = parts[2]
            return h.removeprefix("sha256:") if h.startswith("sha256:") else h
    return None

# Every test here shells out to real deploy.sh/validate.sh (fidelity by design).
pytestmark = pytest.mark.slow

ROOT = Path(__file__).resolve().parents[2]
DEPLOY_SH = ROOT / ".agentcortex" / "bin" / "deploy.sh"
BOOTSTRAP = ROOT / ".agent" / "workflows" / "bootstrap.md"
DOC_GOV = ROOT / ".agentcortex" / "docs" / "guides" / "doc-governance.md"
ROUTING = ROOT / ".agent" / "workflows" / "routing.md"
VALIDATE_SH = ROOT / ".agentcortex" / "bin" / "validate.sh"
VALIDATE_PS1 = ROOT / ".agentcortex" / "bin" / "validate.ps1"
README = ROOT / "README.md"
README_ZH = ROOT / "docs" / "README_zh-TW.md"
INSTALL = ROOT / "docs" / "INSTALL.md"


git_path = shutil.which("git")
git_root = Path(git_path).parent.parent if git_path else None
bash_candidates = [
    str(git_root / "bin" / "bash.exe") if git_root else None,
    str(git_root / "usr" / "bin" / "bash.exe") if git_root else None,
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
    shutil.which("bash"),
]
bash = next(
    (
        candidate for candidate in bash_candidates
        if candidate and "WindowsApps" not in candidate and Path(candidate).exists()
    ),
    None,
)
requires_bash = pytest.mark.skipif(bash is None, reason="bash not available")
powershell = shutil.which("powershell") or shutil.which("pwsh")
requires_powershell = pytest.mark.skipif(powershell is None, reason="PowerShell not available")


def _deploy(target: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    run_env = {**os.environ, **env} if env else None
    return subprocess.run(
        [bash, str(DEPLOY_SH), str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT), env=run_env,
    )


def _deploy_dry_run(target: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [bash, str(DEPLOY_SH), "--dry-run", str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT),
    )


def _deploy_ps1(target: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            powershell,
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / ".agentcortex" / "bin" / "deploy.ps1"),
            str(target),
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(ROOT),
    )


# ---------------------------------------------------------------------------
# Behavioral (AC-5 / AC-6) — the core of ADR-005
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("rel_path", "setup_mode", "env"),
    [
        (".github/copilot-instructions.md", "update_missing_manifest", None),
        ("installers/deploy_brain.sh", "fresh_preexisting", {"ACX_FORCE_PERFILE": "1"}),
    ],
    ids=["scaffold-update-missing-manifest", "wrapper-fresh-preexisting-perfile"],
)
@requires_bash
def test_preexisting_sidecar_file_stays_preserved_across_repeated_deploys(
    rel_path: str,
    setup_mode: str,
    env: dict[str, str] | None,
) -> None:
    """A missing manifest baseline must never turn user bytes into an overwrite grant."""
    with tempfile.TemporaryDirectory() as td:
        source_root = Path(td) / "source"
        deploy_script = source_root / ".agentcortex" / "bin" / "deploy.sh"
        deploy_script.parent.mkdir(parents=True)
        shutil.copy2(DEPLOY_SH, deploy_script)

        # deploy.sh fail-closes unless the downstream current_state template is
        # present in the source repo; seed it so the precheck passes and this
        # test can exercise the sidecar-preservation path it actually targets.
        state_template = source_root / ".agentcortex" / "templates" / "current_state.md"
        state_template.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / ".agentcortex" / "templates" / "current_state.md", state_template)

        source = source_root / rel_path
        source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel_path, source)

        target = Path(td) / "proj"
        target.mkdir()

        deployed = target / rel_path
        sidecar = deployed.with_name(f"{deployed.name}.acx-incoming")
        manifest = target / ".agentcortex-manifest"
        user_bytes = b"# downstream-owned file\nkeep these exact bytes\n"

        def deploy() -> subprocess.CompletedProcess:
            run_env = {**os.environ, **env} if env else None
            return subprocess.run(
                [bash, str(deploy_script), str(target)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=str(source_root),
                env=run_env,
            )

        if setup_mode == "update_missing_manifest":
            assert deploy().returncode == 0
            manifest_lines = manifest.read_text(encoding="utf-8").splitlines()
            manifest.write_text(
                "\n".join(
                    line
                    for line in manifest_lines
                    if not (
                        len(parts := line.split()) >= 2
                        and parts[1] == rel_path
                    )
                )
                + "\n",
                encoding="utf-8",
            )

        deployed.parent.mkdir(parents=True, exist_ok=True)
        deployed.write_bytes(user_bytes)

        first = deploy()
        assert first.returncode == 0, f"first preserving deploy failed:\n{first.stderr}"
        assert deployed.read_bytes() == user_bytes
        assert sidecar.read_bytes() == source.read_bytes()
        first_manifest_hash = _manifest_hash(manifest, rel_path)

        second = deploy()
        assert second.returncode == 0, f"second preserving deploy failed:\n{second.stderr}"
        assert deployed.read_bytes() == user_bytes, \
            "the second deploy must not overwrite pre-existing user bytes"
        assert sidecar.read_bytes() == source.read_bytes(), \
            "each deploy must refresh the upstream version in .acx-incoming"

        source_hash = _lf_sha256(source)
        assert first_manifest_hash == source_hash, \
            "the first preserving deploy must record the upstream baseline, not the user hash"
        assert _manifest_hash(manifest, rel_path) == source_hash, \
            "the preserved manifest baseline must keep later deploys from overwriting user bytes"


@requires_bash
def test_skill_edit_sidecars_and_core_rule_force_updates() -> None:
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()

        first = _deploy(target)
        assert first.returncode == 0, f"first deploy failed:\n{first.stderr}"
        assert (target / ".agentcortex-manifest").exists(), "manifest not created"

        skill = target / ".agents" / "skills" / "api-design" / "SKILL.md"
        rule = target / ".agent" / "rules" / "engineering_guardrails.md"
        assert skill.exists(), "framework skill not deployed"
        assert rule.exists(), "framework rule not deployed"

        # User customizes a framework skill (the R1 scenario) and a core rule.
        skill.write_text(skill.read_text(encoding="utf-8") + "\n<!-- downstream edit -->\n", encoding="utf-8")
        rule.write_text(rule.read_text(encoding="utf-8") + "\n<!-- downstream edit -->\n", encoding="utf-8")

        # A net-new custom-* skill (reserved namespace, never in framework source).
        custom = target / ".agents" / "skills" / "custom-acme" / "SKILL.md"
        custom.parent.mkdir(parents=True, exist_ok=True)
        custom.write_text("# custom-acme\nproject-only skill\n", encoding="utf-8")

        second = _deploy(target)
        assert second.returncode == 0, f"update deploy failed:\n{second.stderr}"

        # AC-6: edited framework skill is PRESERVED via sidecar (not silently lost).
        assert skill.with_name("SKILL.md.acx-incoming").exists(), \
            "edited framework skill should produce a .acx-incoming sidecar"
        assert "<!-- downstream edit -->" in skill.read_text(encoding="utf-8"), \
            "user's skill edit must be preserved, not overwritten"

        # AC-6: net-new custom-* skill is never touched.
        assert custom.exists() and "project-only skill" in custom.read_text(encoding="utf-8"), \
            "custom-* skill must be preserved untouched"

        # AC-5: edited framework-authoritative core rule is FORCE-UPDATED, no sidecar.
        assert not rule.with_name("engineering_guardrails.md.acx-incoming").exists(), \
            "core rule must NOT produce a sidecar (governance must force-update)"
        assert "<!-- downstream edit -->" not in rule.read_text(encoding="utf-8"), \
            "core rule edit must be overwritten by the framework version"


@requires_bash
def test_modified_core_rule_backs_up_to_acx_local_and_is_not_silent() -> None:
    """#173: a locally-modified core file is force-updated (ADR-005 invariant),
    but its previous version is backed up to a .acx-local sidecar and the
    overwrite is surfaced in deploy output — never silently lost."""
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()

        assert _deploy(target).returncode == 0
        rule = target / ".agent" / "rules" / "engineering_guardrails.md"
        assert rule.exists()

        marker = "<!-- downstream core tweak 173 -->"
        rule.write_text(rule.read_text(encoding="utf-8") + f"\n{marker}\n", encoding="utf-8")

        second = _deploy(target)
        assert second.returncode == 0, f"update failed:\n{second.stderr}"

        backup = rule.with_name("engineering_guardrails.md.acx-local")
        # The user's edit is recoverable from the .acx-local backup ...
        assert backup.exists(), "modified core file must back up to .acx-local"
        assert marker in backup.read_text(encoding="utf-8"), \
            "the .acx-local backup must contain the user's edit"
        # ... while the live file is force-updated (ADR-005 invariant preserved) ...
        assert marker not in rule.read_text(encoding="utf-8"), \
            "core rule must still be force-updated to the framework version"
        # ... using .acx-local, NOT .acx-incoming (parity with the AC-5 contract).
        assert not rule.with_name("engineering_guardrails.md.acx-incoming").exists()
        # ... and the overwrite is NOT silent.
        assert "acx-local" in second.stdout, \
            "deploy must surface the core overwrite (non-silent)"

        # Idempotency: a second update (file now matches framework) must NOT
        # re-flag or create another backup.
        backup.unlink()
        third = _deploy(target)
        assert third.returncode == 0
        assert not backup.exists(), \
            "unmodified core file must not be flagged as locally-modified"
        assert "acx-local" not in third.stdout


@requires_bash
def test_core_backup_not_skipped_under_cp_flag_n() -> None:
    """#173 regression: the .acx-local backup must ALWAYS land, even with
    CP_FLAG=-n. .acx-local is never auto-cleaned, so a stale one + `cp -n`
    would silently skip the backup and lose the newest local edits — exactly
    the data loss this fix closes."""
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()
        assert _deploy(target).returncode == 0
        rule = target / ".agent" / "rules" / "engineering_guardrails.md"
        backup = rule.with_name("engineering_guardrails.md.acx-local")
        base = rule.read_text(encoding="utf-8")

        # First local edit, then a no-clobber (CP_FLAG=-n) update creates .acx-local(A).
        rule.write_text(base + "\n<!-- edit A -->\n", encoding="utf-8")
        assert _deploy(target, env={"CP_FLAG": "-n"}).returncode == 0
        assert backup.exists() and "edit A" in backup.read_text(encoding="utf-8")

        # Second local edit, then another -n update. The stale backup must be
        # replaced with edit B — NOT skipped by `cp -n`.
        rule.write_text(base + "\n<!-- edit B -->\n", encoding="utf-8")
        assert _deploy(target, env={"CP_FLAG": "-n"}).returncode == 0
        bk = backup.read_text(encoding="utf-8")
        assert "edit B" in bk, "newest local edits must be backed up, not skipped under CP_FLAG=-n"
        assert "edit A" not in bk, "stale backup must be replaced, not retained"


def test_deploy_gitignores_acx_local_sidecar() -> None:
    """#173: the .acx-local backup is deploy-generated; it must be in the
    managed downstream .gitignore block (parity with *.acx-incoming) so it
    does not pollute the downstream working tree."""
    s = DEPLOY_SH.read_text(encoding="utf-8")
    assert "*.acx-local" in s, "deploy.sh must add *.acx-local to the managed .gitignore block"


@requires_powershell
def test_deploy_ps1_entrypoint_resolves_real_bash() -> None:
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()

        result = _deploy_ps1(target)
        assert result.returncode == 0, (
            f"deploy.ps1 failed:\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert (target / ".agentcortex-manifest").exists(), "deploy.ps1 should create manifest"


@requires_bash
def test_deployed_governance_referenced_tools_are_deployed() -> None:
    """Regression: every `.agentcortex/tools/<name>.py` that a DEPLOYED governance
    doc instructs a downstream agent to run MUST itself be deployed. The runtime-
    tools whitelist in deploy.sh is hand-maintained, so a new feature that adds a
    workflow tool but forgets the whitelist ships a dangling `python ...` command
    that fails with 'No such file' in every downstream bootstrap/review.
    Found via downstream simulation (recover_worklog_lock.py + lint_spec_drift.py
    were referenced by bootstrap.md / review.md but absent from the deployed tree).
    """
    import re

    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()
        assert _deploy(target).returncode == 0, "deploy failed"

        gov_files: list[Path] = [target / "AGENTS.md", target / "CLAUDE.md"]
        for sub in (".agent/workflows", ".agent/rules"):
            d = target / sub
            if d.exists():
                gov_files.extend(sorted(d.glob("*.md")))

        pat = re.compile(r"\.agentcortex/tools/([A-Za-z0-9_]+\.py)")
        referenced: set[str] = set()
        for f in gov_files:
            if f.exists():
                referenced.update(pat.findall(f.read_text(encoding="utf-8")))

        tools_dir = target / ".agentcortex" / "tools"
        missing = sorted(name for name in referenced if not (tools_dir / name).exists())
        assert not missing, (
            "deployed governance docs reference tools that deploy.sh did not ship "
            f"(add them to the runtime_tools whitelist in deploy.sh): {missing}"
        )
        # Sanity: the two tools this regression was opened for are now shipped.
        assert (tools_dir / "recover_worklog_lock.py").exists()
        assert (tools_dir / "lint_spec_drift.py").exists()


@requires_bash
def test_downstream_current_state_comes_from_template_only() -> None:
    """AC-1: downstream runtime SSoT must be seeded from the template, never from
    the source repo's live `.agentcortex/context/current_state.md`."""
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()

        first = _deploy(target)
        assert first.returncode == 0, f"deploy failed:\n{first.stderr}"

        deployed = target / ".agentcortex" / "context" / "current_state.md"
        template = ROOT / ".agentcortex" / "templates" / "current_state.md"
        source_live = ROOT / ".agentcortex" / "context" / "current_state.md"
        assert deployed.read_text(encoding="utf-8") == template.read_text(encoding="utf-8")
        assert deployed.read_text(encoding="utf-8") != source_live.read_text(encoding="utf-8")
        assert "Self-managed Agent OS for AI coding agents" not in deployed.read_text(encoding="utf-8")


@requires_bash
def test_deploy_fails_closed_when_current_state_template_missing() -> None:
    with tempfile.TemporaryDirectory() as td:
        source_root = Path(td) / "source"
        deploy_script = source_root / ".agentcortex" / "bin" / "deploy.sh"
        live_state = source_root / ".agentcortex" / "context" / "current_state.md"
        deploy_script.parent.mkdir(parents=True)
        live_state.parent.mkdir(parents=True)
        shutil.copy2(DEPLOY_SH, deploy_script)
        live_state.write_text("source live state must never deploy\n", encoding="utf-8")

        target = Path(td) / "proj"
        target.mkdir()
        result = subprocess.run(
            [bash, str(deploy_script), str(target)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(source_root),
        )

        assert result.returncode != 0
        assert "Missing downstream current_state template" in result.stderr
        assert not (target / ".agentcortex" / "context" / "current_state.md").exists()


@requires_bash
def test_dry_run_discloses_generated_current_state_artifact() -> None:
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()
        result = _deploy_dry_run(target)
        assert result.returncode == 0, f"dry-run failed:\n{result.stderr}"
        assert ".agentcortex/context/current_state.md" in result.stdout
        assert ".agentcortex/templates/current_state.md" in result.stdout


def test_source_and_downstream_ignore_guard_receipt_directory() -> None:
    source_ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    deploy_sh = DEPLOY_SH.read_text(encoding="utf-8")
    assert ".agentcortex/context/.guard_receipts/" in source_ignore
    assert ".agentcortex/context/.guard_receipts/" in deploy_sh


@pytest.mark.docs_pin
def test_text_only_install_does_not_copy_runtime_context() -> None:
    install = INSTALL.read_text(encoding="utf-8")
    text_only = install.split("<summary><b>Text-only usage", 1)[1].split("</details>", 1)[0]
    assert "Copy the `.agent/`, `.agents/`, and `AGENTS.md` files" in text_only
    assert "copy `.agentcortex/context/`" not in text_only
    assert "templates/current_state.md" in text_only


@requires_bash
def test_downstream_adaptability_files_deploy_at_correct_tier() -> None:
    """PR #238 (ADR-007/008): the new safety-floor + credential tools ship core
    (force-update, reach all downstream); the committed AGENTS.safety.md nucleus
    ships core; the present-only downstream-capabilities.yaml is NEVER shipped."""
    deploy_sh = (ROOT / ".agentcortex" / "bin" / "deploy.sh").read_text(encoding="utf-8")
    # AC-S5: scan_credentials.py in BOTH whitelist spots (the L725 string + the array)
    assert deploy_sh.count("scan_credentials.py") >= 2, "scan_credentials.py must be in both deploy.sh whitelist spots"
    for tool in ("credential_floor.sh", "credential_floor.ps1",
                 "generate_safety_nucleus.py", "validate_downstream_capabilities.py"):
        assert tool in deploy_sh, f"{tool} missing from deploy.sh runtime whitelist"

    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()
        assert _deploy(target).returncode == 0, "deploy failed"
        tools = target / ".agentcortex" / "tools"
        # AC-S5: scanner + floors + generators are deployed
        for tool in ("scan_credentials.py", "credential_floor.sh", "credential_floor.ps1",
                     "generate_safety_nucleus.py", "validate_downstream_capabilities.py"):
            assert (tools / tool).exists(), f"{tool} not deployed (AC-S5)"
        # AC-S2: the committed safety nucleus ships as a core file
        assert (target / ".agentcortex" / "AGENTS.safety.md").exists(), "AGENTS.safety.md not deployed (AC-S2)"
        # AC-D12: the present-only capabilities file is NEVER shipped
        assert not (target / ".agentcortex" / "context" / "private" / "downstream-capabilities.yaml").exists(), \
            "downstream-capabilities.yaml must never be shipped (AC-D12)"


def test_downstream_capabilities_yaml_is_gitignored() -> None:
    """AC-D12 (inherent): downstream-capabilities.yaml lives under the gitignored
    .agentcortex/context/private/ tree, so deploy/commit never touch it."""
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".agentcortex/context/private/" in gitignore, \
        "context/private/ must be gitignored so downstream-capabilities.yaml is never committed/shipped"


@requires_bash
def test_deploy_does_not_scaffold_docs_architecture() -> None:
    """`docs/architecture/` is intentionally capability-by-presence, NOT a fixed
    anchor like docs/adr/ + docs/specs/. It is created on demand by /app-init;
    bootstrap.md keys the "skip all Domain Doc steps, zero extra reads"
    optimization on its ABSENCE. Scaffolding it empty on deploy would silently
    flip that optimization off for every downstream project. This guard locks in
    the no-scaffold design so a well-meaning "fix" cannot regress it.
    (engineering_guardrails.md §4.2 / bootstrap.md capability-by-presence.)
    """
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()
        assert _deploy(target).returncode == 0, "deploy failed"

        # The two fixed anchors ARE scaffolded ...
        assert (target / "docs" / "adr").is_dir(), "docs/adr/ is a fixed anchor"
        assert (target / "docs" / "specs").is_dir(), "docs/specs/ is a fixed anchor"
        # ... but docs/architecture/ must NOT be (capability-by-presence).
        assert not (target / "docs" / "architecture").exists(), (
            "deploy must NOT scaffold docs/architecture/ — it is created on demand "
            "by /app-init; its absence drives bootstrap's zero-read optimization"
        )


# ---------------------------------------------------------------------------
# Structural — guard the wiring + cross-platform parity against silent drift
# ---------------------------------------------------------------------------

def test_deploy_classifies_skills_as_scaffold() -> None:
    s = DEPLOY_SH.read_text(encoding="utf-8")
    assert ".agent/skills/*|.agents/skills/*) echo \"scaffold\"" in s, \
        "deploy.sh must classify skills as scaffold (ADR-005)"


def test_bootstrap_ships_override_load_step() -> None:
    assert "Load Override Layer" in BOOTSTRAP.read_text(encoding="utf-8")


def test_doc_governance_override_is_active() -> None:
    txt = DOC_GOV.read_text(encoding="utf-8")
    assert "soft-launch" not in txt.split("## Override Layer", 1)[-1].split("##", 1)[0], \
        "override section must no longer be labeled soft-launch"
    assert "MUST read override files at session start" in txt


def test_routing_reserves_custom_namespace() -> None:
    txt = ROUTING.read_text(encoding="utf-8")
    assert "ship a skill whose name begins with" in txt and "custom-" in txt


def test_validators_check_override_step_parity() -> None:
    assert "Load Override Layer" in VALIDATE_SH.read_text(encoding="utf-8")
    assert "Load Override Layer" in VALIDATE_PS1.read_text(encoding="utf-8")


@pytest.mark.docs_pin
def test_readme_fork_guidance_parity() -> None:
    """Fork/clone customization guidance (ADR-004/ADR-005) must stay reachable
    from both language entry points. The English README was slimmed to a
    landing page, so the guidance now lives in the dedicated install guide
    (docs/INSTALL.md) and is linked from the README; the zh-TW README still
    carries it inline (its lean overhaul is tracked separately)."""
    readme = README.read_text(encoding="utf-8")
    install = (ROOT / "docs" / "INSTALL.md").read_text(encoding="utf-8")
    # English: guidance in INSTALL.md, reachable via a README link.
    assert "Customizing without conflicts" in install
    assert "docs/INSTALL.md" in readme
    # zh-TW: still inline in the localized README.
    assert "客製化而不衝突" in README_ZH.read_text(encoding="utf-8")


def test_framework_ships_no_custom_namespace_skill() -> None:
    """ADR-005 contract: the framework MUST NEVER ship a skill under the reserved
    custom-* downstream namespace. Regression guard (G-005) so a future framework
    PR adding such a skill fails CI instead of silently breaking the guarantee."""
    for base in (ROOT / ".agents" / "skills", ROOT / ".agent" / "skills"):
        if not base.exists():
            continue
        offenders = [p.name for p in base.iterdir() if p.name.startswith("custom-")]
        assert not offenders, f"framework must not ship custom-* skills (ADR-005): {offenders}"


# ---------------------------------------------------------------------------
# EOL-hash correctness (fix for CRLF hash mismatch on Windows autocrlf)
# ---------------------------------------------------------------------------

@requires_bash
def test_crlf_deployed_md_does_not_spuriously_sidecar() -> None:
    """EOL-hash fix: a deployed .md file CRLF-ified by git autocrlf must NOT be
    classified as 'locally modified' on the next deploy. The normalized hash
    (tr -d '\\r') must match the manifest entry so the update lands in-place
    rather than being sidecarred to .acx-incoming (the original regression
    that caused silent framework updates to fail on Windows)."""
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()

        assert _deploy(target).returncode == 0

        # Pick a scaffold-tier .md (AGENTS.md) — the exact file that was
        # misclassified on CRLF checkouts.
        agents_md = target / "AGENTS.md"
        assert agents_md.exists(), "AGENTS.md not deployed"

        # --- Mutation guard: manifest must store the LF-normalized hash -------
        # compute_sha256_normalized (the fix) strips \r before hashing, so the
        # manifest entry for AGENTS.md MUST equal the LF-normalized hash of the
        # *source* file.  If someone reverts to compute_sha256 (raw), the
        # manifest will store the CRLF hash on Windows CI and this assertion
        # fails — exactly the regression we are guarding against.
        src_agents_md = ROOT / "AGENTS.md"
        expected_lf_hash = _lf_sha256(src_agents_md)
        manifest = target / ".agentcortex-manifest"
        stored_hash = _manifest_hash(manifest, "AGENTS.md")
        assert stored_hash == expected_lf_hash, (
            f"manifest must store the LF-normalized hash of AGENTS.md "
            f"(got {stored_hash!r}, expected {expected_lf_hash!r}); "
            "revert to compute_sha256 (raw) = regression"
        )
        # --- End mutation guard -----------------------------------------------

        # Simulate git autocrlf converting the deployed file to CRLF.
        # Normalize to LF first (in case CI checkout already CRLF-ified the
        # source tree), then CRLF-ify — guarantees exactly one \r\n per line
        # regardless of the host git autocrlf setting.
        raw = agents_md.read_bytes()
        lf_content = raw.replace(b"\r\n", b"\n")   # strip any existing CRs
        crlf_content = lf_content.replace(b"\n", b"\r\n")
        agents_md.write_bytes(crlf_content)

        # Re-deploy: the CRLF-ified (but otherwise unmodified) file must update
        # in-place — NOT sidecar to .acx-incoming and NOT warn about local edits.
        second = _deploy(target)
        assert second.returncode == 0, f"re-deploy failed:\n{second.stderr}"

        # No sidecar must exist (the EOL-only difference is not a user edit).
        sidecar = agents_md.with_name("AGENTS.md.acx-incoming")
        assert not sidecar.exists(), (
            "CRLF-only difference must NOT produce a .acx-incoming sidecar "
            "(normalized hash must match manifest)"
        )
        # The update must have landed (framework content is in place).
        assert agents_md.exists(), "AGENTS.md must still exist after re-deploy"


@requires_bash
def test_genuine_content_edit_still_sidecars_after_eol_fix() -> None:
    """Preservation invariant: a scaffold-tier file with a genuine content edit
    (not just EOL) must still be sidecarred on re-deploy — normalized hashing
    must not mask real user modifications."""
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()

        assert _deploy(target).returncode == 0

        # Pick a framework skill (scaffold tier) and add a real content edit.
        skill = target / ".agents" / "skills" / "api-design" / "SKILL.md"
        assert skill.exists(), "api-design skill not deployed"

        # --- Mutation guard: manifest must store the LF-normalized hash -------
        # Same principle as test_crlf_deployed_md_does_not_spuriously_sidecar:
        # if deploy.sh reverts to raw compute_sha256, the manifest hash on a
        # CRLF checkout will be a CRLF hash — verify it is the LF-normalized one.
        src_skill = ROOT / ".agents" / "skills" / "api-design" / "SKILL.md"
        expected_lf_hash = _lf_sha256(src_skill)
        manifest = target / ".agentcortex-manifest"
        stored_hash = _manifest_hash(manifest, ".agents/skills/api-design/SKILL.md")
        assert stored_hash == expected_lf_hash, (
            f"manifest must store the LF-normalized hash of api-design/SKILL.md "
            f"(got {stored_hash!r}, expected {expected_lf_hash!r}); "
            "revert to compute_sha256 (raw) = regression"
        )
        # --- End mutation guard -----------------------------------------------

        # Write bytes directly to avoid text-mode CRLF conversion on Windows:
        # append LF-terminated marker so the normalized hash differs from the
        # manifest entry regardless of the CI checkout EOL setting.
        skill.write_bytes(
            skill.read_bytes().replace(b"\r\n", b"\n")  # normalize to LF baseline
            + b"\n<!-- genuine user edit -->\n"
        )

        second = _deploy(target)
        assert second.returncode == 0, f"re-deploy failed:\n{second.stderr}"

        # Genuine content edit → sidecar must be written (preservation intact).
        sidecar = skill.with_name("SKILL.md.acx-incoming")
        assert sidecar.exists(), (
            "A skill with a genuine content edit must still produce a .acx-incoming sidecar "
            "— normalized hashing must not suppress real user modifications"
        )
        # User's edit must be preserved in the live file.
        assert "<!-- genuine user edit -->" in skill.read_text(encoding="utf-8"), \
            "user's genuine edit must be preserved in the skill file"


@requires_bash
def test_stale_skill_warning_for_retired_framework_skill() -> None:
    """Stale-skill detection: an orphan skill present in target, absent from the
    current framework skill set, AND present in the OLD manifest (simulating a
    framework-retired skill) must produce a [STALE SKILL] warning on deploy."""
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()

        assert _deploy(target).returncode == 0

        # Plant an orphan directory-based skill not in the framework.
        orphan = target / ".agents" / "skills" / "executing-plans"
        orphan.mkdir(parents=True, exist_ok=True)
        skill_file = orphan / "SKILL.md"
        skill_file.write_text(
            "# executing-plans\nRetired skill — simulating stale upstream.\n",
            encoding="utf-8",
        )

        # Simulate this skill having been framework-managed: append a matching
        # OLD-manifest line so _skill_in_old_manifest returns true.
        # The hash must be the LF-normalized hash of the planted SKILL.md.
        manifest = target / ".agentcortex-manifest"
        lf_hash = _lf_sha256(skill_file)
        with manifest.open("a", encoding="utf-8") as mf:
            mf.write(f"scaffold .agents/skills/executing-plans/SKILL.md sha256:{lf_hash}\n")

        second = _deploy(target)
        assert second.returncode == 0, f"re-deploy failed:\n{second.stderr}"

        # The warning must name the stale skill and say "retired upstream".
        assert "[STALE SKILL]" in second.stdout, \
            "deploy must emit [STALE SKILL] for a framework-retired skill"
        assert "executing-plans" in second.stdout, \
            "the stale skill warning must name the specific skill directory"
        assert "retired upstream" in second.stdout, \
            "the warning must say 'retired upstream' for a manifest-present skill"


@requires_bash
def test_user_created_skill_is_not_accused_as_stale() -> None:
    """Item B: a non-custom-* skill planted by the user AFTER deploy (absent from
    the old manifest) must NOT receive a per-skill [STALE SKILL] warning and must
    NOT say 'retired upstream' or 'delete it'.  It must instead be named in the
    aggregated 'local skill(s) not framework-managed' note."""
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()

        assert _deploy(target).returncode == 0

        # Plant a non-custom-* skill that was never in the manifest.
        user_skill = target / ".agents" / "skills" / "my-project-helper"
        user_skill.mkdir(parents=True, exist_ok=True)
        (user_skill / "SKILL.md").write_text(
            "# my-project-helper\nProject-specific skill not from framework.\n",
            encoding="utf-8",
        )
        # Do NOT add it to the manifest — it was never deployed by the framework.

        second = _deploy(target)
        assert second.returncode == 0, f"re-deploy failed:\n{second.stderr}"

        out = second.stdout
        # Must NOT produce a per-skill [STALE SKILL] line naming this skill.
        stale_lines = [ln for ln in out.splitlines() if "[STALE SKILL]" in ln and "my-project-helper" in ln]
        assert not stale_lines, \
            "user-created skill (absent from manifest) must not get a [STALE SKILL] warning"
        # Must not contain 'retired upstream' adjacent to the skill name.
        retired_lines = [ln for ln in out.splitlines() if "retired upstream" in ln and "my-project-helper" in ln]
        assert not retired_lines, \
            "user-created skill must not be labelled 'retired upstream'"
        # Must appear in the aggregated 'local skill' note.
        assert "local skill" in out, \
            "user-created skills must produce the aggregated 'local skill(s) not framework-managed' note"
        assert "my-project-helper" in out, \
            "the aggregated note must name the user-created skill"


@requires_bash
def test_custom_namespace_skill_is_silent_in_stale_detection() -> None:
    """Custom-* namespace exemption: a project-owned skill prefixed with 'custom-'
    must NEVER produce a [STALE SKILL] warning, even if absent from the framework."""
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()

        assert _deploy(target).returncode == 0

        # Plant a custom-* project skill — should be silently ignored.
        custom = target / ".agents" / "skills" / "custom-my-project-skill"
        custom.mkdir(parents=True, exist_ok=True)
        (custom / "SKILL.md").write_text(
            "# custom-my-project-skill\nProject-owned skill.\n",
            encoding="utf-8",
        )

        second = _deploy(target)
        assert second.returncode == 0, f"re-deploy failed:\n{second.stderr}"

        # No stale warning for custom-* skills.
        assert "custom-my-project-skill" not in second.stdout, \
            "custom-* skills must never produce a [STALE SKILL] warning"


@requires_bash
def test_gemini_md_is_deployed() -> None:
    """GEMINI.md is a first-class agent entry point (it @imports AGENTS.md per
    multi-agent-review-guidelines AC-2) but was absent from deploy.sh's root-file
    list — downstream Gemini/Antigravity users got no entry point. (sim A1, 2026-06-11)"""
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()
        assert _deploy(target).returncode == 0, "deploy failed"
        for entry in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
            assert (target / entry).is_file(), f"{entry} must be deployed to downstream root"
        # GEMINI.md is scaffold tier (user-editable, like AGENTS/CLAUDE).
        manifest = (target / ".agentcortex-manifest").read_text(encoding="utf-8")
        assert "GEMINI.md" in manifest, "GEMINI.md must be recorded in the manifest"


@requires_bash
def test_copilot_instructions_is_deployed() -> None:
    """`.github/copilot-instructions.md` is GitHub Copilot's repo-wide entry point
    (it points at AGENTS.md). AGENTS.md alone only covers Copilot's coding-agent
    surface; the IDE custom-instructions surface reads copilot-instructions.md. It
    was absent from deploy.sh's .github list — downstream Copilot users got no
    governance entry point. Scaffold tier (user-customizable, preserved as
    .acx-incoming). (cross-platform entry-point diagnosis, 2026-06-20)"""
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()
        assert _deploy(target).returncode == 0, "deploy failed"
        instr = target / ".github" / "copilot-instructions.md"
        assert instr.is_file(), ".github/copilot-instructions.md must be deployed downstream"
        manifest = (target / ".agentcortex-manifest").read_text(encoding="utf-8")
        assert ".github/copilot-instructions.md" in manifest, "copilot-instructions.md must be in the manifest"


@requires_bash
def test_no_migration_banner_on_clean_update() -> None:
    """A bare .agentcortex-manifest is the normal installed state; announcing
    'Migrating from legacy paths' on every routine re-deploy was pure noise.
    (sim A1, 2026-06-11) — banner must only appear when real legacy artifacts exist."""
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()
        first = _deploy(target)
        assert first.returncode == 0
        assert "Migrating from legacy paths" not in first.stdout, \
            "fresh deploy into an empty dir must not print the migration banner"
        second = _deploy(target)
        assert second.returncode == 0
        assert "Migrating from legacy paths" not in second.stdout, \
            "routine re-deploy (manifest present, no legacy dirs) must not print the migration banner"


# ---------------------------------------------------------------------------
# AC-13: anchored deploy-manifest snapshot (demonstration over green gates)
# ---------------------------------------------------------------------------

FIXTURES_DIR = ROOT / "tests" / "ci" / "fixtures"
DEPLOY_MANIFEST_GOLDEN = FIXTURES_DIR / "deploy_manifest_golden.txt"


def _normalize_manifest(manifest_path: Path) -> list[str]:
    """Return sorted 'tier rel_path' lines from the manifest.

    Normalizes away: sha256 hashes, version strings, timestamps, and temp
    paths — so the golden is stable across redeploys and version bumps.
    Only the tier classification and relative path are asserted.

    To regenerate the golden after a legitimate deploy-set change:
        python -m pytest tests/ci/test_deploy_tiering.py \
            -k test_deploy_manifest_snapshot --regen-golden
    Or manually:
        grep -E '^(core|scaffold|wrapper) ' <manifest> | awk '{print $1,$2}' | sort \
            > tests/ci/fixtures/deploy_manifest_golden.txt
    """
    lines = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] in ("core", "scaffold", "wrapper"):
            lines.append(f"{parts[0]} {parts[1]}")
    return sorted(lines)


@requires_bash
def test_deploy_manifest_snapshot(request: pytest.FixtureRequest) -> None:
    """AC-13: the normalized deploy-manifest (tier + rel-path) must match the
    committed golden snapshot.

    This is the CI-enforced anchor for demonstration over green gates: a hand-
    faked golden diverges from what deploy.sh actually produces and stays red.
    When deploy intentionally changes (new file added, tier reclassified, file
    removed), regenerate the golden via the instructions in _normalize_manifest.

    Regen flag: pass --regen-golden on the pytest command line to write the
    golden in-place instead of asserting (requires --co not to be set).
    """
    regen = request.config.getoption("--regen-golden", default=False)
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "proj"
        target.mkdir()
        result = _deploy(target)
        assert result.returncode == 0, (
            f"deploy failed (cannot snapshot a broken deploy):\n{result.stderr}"
        )
        manifest = target / ".agentcortex-manifest"
        assert manifest.exists(), "manifest not written by deploy"

        actual = _normalize_manifest(manifest)

        if regen:
            FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
            DEPLOY_MANIFEST_GOLDEN.write_text(
                "\n".join(actual) + "\n", encoding="utf-8"
            )
            pytest.skip(f"golden regenerated at {DEPLOY_MANIFEST_GOLDEN} ({len(actual)} entries)")
            return

        assert DEPLOY_MANIFEST_GOLDEN.exists(), (
            f"Golden fixture missing: {DEPLOY_MANIFEST_GOLDEN}\n"
            "Run with --regen-golden to create it from a real deploy."
        )
        expected = sorted(
            line
            for line in DEPLOY_MANIFEST_GOLDEN.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )

        added = sorted(set(actual) - set(expected))
        removed = sorted(set(expected) - set(actual))
        if added or removed:
            diff_lines = []
            for entry in added:
                diff_lines.append(f"  + {entry}")
            for entry in removed:
                diff_lines.append(f"  - {entry}")
            pytest.fail(
                "Deploy manifest diverged from golden "
                f"(tests/ci/fixtures/deploy_manifest_golden.txt).\n"
                "If this change is intentional, regenerate with --regen-golden.\n"
                "Diff:\n" + "\n".join(diff_lines)
            )
