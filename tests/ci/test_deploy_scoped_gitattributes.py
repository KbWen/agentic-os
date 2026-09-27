"""The installed .gitattributes leaves the product's own files alone (#215, 2026-09-27).

deploy.sh used to install the source repository's own .gitattributes, whose rules are
repo-wide (``* text=auto``; ``*.md``/``*.py``/``*.json``/``*.sh`` ``text eol=lf``;
``*.ps1``/``*.cmd``/``*.bat`` ``eol=crlf``). In a product that commits CRLF, every product
file then showed as a whole-file line-ending rewrite as soon as an editor or build tool
touched it. deploy.sh now installs ``.agentcortex/templates/downstream.gitattributes``,
which sets line endings only for the files Agentic OS installs (and ``.githooks/``).
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DEPLOY_SH = ROOT / ".agentcortex" / "bin" / "deploy.sh"
TEMPLATE = ROOT / ".agentcortex" / "templates" / "downstream.gitattributes"

git_path = shutil.which("git")
git_root = Path(git_path).parent.parent if git_path else None
bash_candidates = [
    str(git_root / "bin" / "bash.exe") if git_root else None,
    str(git_root / "usr" / "bin" / "bash.exe") if git_root else None,
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    shutil.which("bash"),
]
bash = next(
    (c for c in bash_candidates if c and "WindowsApps" not in c and Path(c).exists()),
    None,
)
requires_bash = pytest.mark.skipif(bash is None, reason="bash not available")

GIT_ID = ["-c", "user.name=acx-test", "-c", "user.email=acx-test@example.invalid"]

# The product's own files, committed with CRLF (core.autocrlf=false), including Markdown in
# the folders the framework writes to and in the tool folders it shares with the product.
PRODUCT_FILES = {
    "app.py": b"print(1)\r\n",
    "config.json": b'{"a": 1}\r\n',
    "README.md": b"# Product\r\n",
    "scripts/run.sh": b"echo hi\r\n",
    "scripts/tool.ps1": b"Write-Host hi\r\n",
    "docs/guide.md": b"# Guide\r\n",
    "docs/adr/0001-record.md": b"# Product ADR\r\n",
    "docs/specs/checkout.md": b"# Product spec\r\n",
    ".claude/commands/our-release.md": b"# Our release\r\n",
}
# Installed only when absent, then owned by the product; or shared with the product's own files
# (Claude Code reads either line ending, and deploy hashes ignore CRs).
NOT_COVERED_BY_DESIGN = (".gitattributes", ".claude/settings.json")
NOT_COVERED_PREFIXES = (".github/", ".claude/commands/", ".claude/agents/")

# The rules v1.8.28 and earlier installed (the repository's own file at the time).
OLD_INSTALLED = """\
* text=auto
*.sh text eol=lf
*.ps1 text eol=crlf
*.cmd text eol=crlf
*.bat text eol=crlf
*.py text eol=lf
*.json text eol=lf
*.md text eol=lf
*.yaml text eol=lf
*.yml text eol=lf
.agentcortex-manifest text eol=lf
.githooks/** text eol=lf
"""
NOTICE = ".gitattributes no longer sets line endings for your own files"


def _git_env(tmp_path: Path) -> dict:
    """Keep the host's system and global git config (e.g. core.autocrlf) out of the fixture."""
    empty = tmp_path / "empty.gitconfig"
    empty.write_text("", encoding="utf-8")
    return {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": str(empty)}


def _git(repo: Path, env: dict, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, env=env
    ).stdout


def _attr(repo: Path, env: dict, attr: str, paths: list[str]) -> dict[str, str]:
    # NUL-separated bytes: text-mode stdin on Windows would turn "\n" into "\r\n",
    # and git would then look up "AGENTS.md\r", which no rule names.
    out = subprocess.run(
        ["git", "-C", str(repo), "check-attr", "-z", "--stdin", attr],
        input=("\0".join(paths) + "\0").encode("utf-8"), capture_output=True, check=True, env=env,
    ).stdout.decode("utf-8")
    fields = out.split("\0")
    values = {fields[i]: fields[i + 2] for i in range(0, len(fields) - 2, 3)}
    assert set(values) == set(paths), sorted(set(paths) ^ set(values))
    return values


def _deploy(target: Path) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [bash, str(DEPLOY_SH), str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr[-2000:]
    return result


def _set_manifest_hash(manifest: Path, rel: str, data: bytes) -> None:
    digest = hashlib.sha256(data.replace(b"\r", b"")).hexdigest()
    lines = manifest.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        parts = line.split()
        if len(parts) >= 3 and parts[1] == rel:
            parts[2] = f"sha256:{digest}"
            lines[index] = " ".join(parts)
            break
    else:
        raise AssertionError(f"manifest row not found: {rel}")
    manifest.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))


@requires_bash
@pytest.mark.slow
def test_installed_gitattributes_leaves_product_files_alone(tmp_path: Path) -> None:
    env = _git_env(tmp_path)
    target = tmp_path / "product"
    target.mkdir()
    _git(target, env, "init", "-q")
    _git(target, env, "config", "core.autocrlf", "false")
    for rel, data in PRODUCT_FILES.items():
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        (target / rel).write_bytes(data)
    _git(target, env, "add", "-A")
    _git(target, env, *GIT_ID, "commit", "-qm", "product")

    _deploy(target)
    _git(target, env, "add", "-A")
    _git(target, env, *GIT_ID, "commit", "-qm", "install")

    # The product's own files get no line-ending rule from the framework ...
    product = list(PRODUCT_FILES)
    assert set(_attr(target, env, "text", product).values()) == {"unspecified"}
    assert set(_attr(target, env, "eol", product).values()) == {"unspecified"}
    # ... so an editor or build tool touching them changes nothing git reports.
    time.sleep(1.1)
    for rel in product:
        os.utime(target / rel)
    status = _git(target, env, "status", "--porcelain")
    assert status == "", f"touching product files made git report changes:\n{status}"

    # Every other file Agentic OS installed resolves a line ending.
    installed = [
        parts[1]
        for parts in (line.split() for line in (target / ".agentcortex-manifest").read_text(encoding="utf-8").splitlines())
        if len(parts) >= 2 and parts[0] in ("core", "scaffold", "wrapper")
    ]
    framework = [
        p for p in installed
        if p not in NOT_COVERED_BY_DESIGN and not p.startswith(NOT_COVERED_PREFIXES)
    ]
    assert len(framework) > 120, len(framework)
    eol = _attr(target, env, "eol", framework + [".agentcortex-manifest"])
    uncovered = sorted(p for p, v in eol.items() if v not in ("lf", "crlf"))
    assert not uncovered, f"installed paths without a line-ending rule: {uncovered}"
    assert eol[".agentcortex-manifest"] == "lf"
    assert all(eol[p] == "lf" for p in framework if p.endswith(".sh"))
    windows = [p for p in framework if p.endswith((".ps1", ".cmd"))]
    assert windows and all(eol[p] == "crlf" for p in windows), {p: eol[p] for p in windows}


@requires_bash
@pytest.mark.slow
def test_update_notice_only_when_the_old_repo_wide_file_is_replaced(tmp_path: Path) -> None:
    target = tmp_path / "product"
    target.mkdir()
    _deploy(target)
    gitattributes = target / ".gitattributes"
    manifest = target / ".agentcortex-manifest"

    # An install by v1.8.28 or earlier that the adopter never edited: replaced, notice once.
    gitattributes.write_bytes(OLD_INSTALLED.encode("utf-8"))
    _set_manifest_hash(manifest, ".gitattributes", OLD_INSTALLED.encode("utf-8"))
    update = _deploy(target)
    assert NOTICE in update.stdout, update.stdout[-1500:]
    assert gitattributes.read_bytes().replace(b"\r", b"") == TEMPLATE.read_bytes().replace(b"\r", b"")
    assert NOTICE not in _deploy(target).stdout, "the notice must not repeat once the old rules are gone"

    # A .gitattributes the deploy keeps (edited, or the product's own with a similar rule)
    # is never overwritten and gets no notice: nothing changed for its clones.
    own = "* text=auto\n*.md text eol=lf\n*.bin binary\n"
    gitattributes.write_bytes(own.encode("utf-8"))
    kept = _deploy(target)
    assert NOTICE not in kept.stdout, kept.stdout[-1500:]
    assert gitattributes.read_bytes().replace(b"\r", b"") == own.encode("utf-8")


def test_template_sets_no_rule_on_product_files(tmp_path: Path) -> None:
    """Review of #215: `* text=auto` checked product files out CRLF under Windows
    core.autocrlf=false, and rules on docs/ rewrote the product's own Markdown."""
    env = _git_env(tmp_path)
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, env, "init", "-q")
    (repo / ".gitattributes").write_bytes(TEMPLATE.read_bytes())
    product = [
        "app.py", "src/web.js", "config.json", "deploy.yaml", "scripts/run.sh", "scripts/tool.ps1",
        "build.cmd", "run.bat", "Makefile", "README.md", "docs/guide.md", "docs/specs/diagram.png",
        "docs/specs/checkout.md", "docs/architecture/c4/context.md", "docs/adr/0001-record.md",
        "docs/reviews/q1.md", ".claude/commands/our-release.md", ".claude/agents/our-agent.md",
    ]
    framework = {
        "AGENTS.md": "lf", ".agentcortex/bin/validate.sh": "lf", ".agent/workflows/ship.md": "lf",
        ".agents/skills/api-design/SKILL.md": "lf", ".githooks/pre-commit": "lf",
        ".agentcortex/bin/validate.ps1": "crlf", "installers/deploy_brain.cmd": "crlf",
    }
    text = _attr(repo, env, "text", product)
    eol = _attr(repo, env, "eol", product + list(framework))
    touched = {p: (text[p], eol[p]) for p in product if (text[p], eol[p]) != ("unspecified", "unspecified")}
    assert not touched, f"product paths with a framework line-ending rule: {touched}"
    assert {p: eol[p] for p in framework} == framework


@pytest.mark.parametrize(
    "eol, autocrlf, leftover",
    [("lf", "false", True), ("crlf", "false", True), ("native", "true", False)],
    ids=["linux-default", "windows-autocrlf-false", "windows-autocrlf-true"],
)
def test_the_update_notice_advice_restores_a_leftover_and_keeps_real_edits(
    tmp_path: Path, eol: str, autocrlf: str, leftover: bool
) -> None:
    """Review of #215: once the old rules are gone, a clone they checked out keeps CRLF
    working copies of LF blobs (*.ps1/*.cmd/*.bat everywhere; every text file under Windows
    core.autocrlf=false). The notice's advice: a file git shows as modified whose
    `git diff --ignore-cr-at-eol` is empty is such a leftover, and `git checkout --` restores it."""
    env = _git_env(tmp_path)
    origin = tmp_path / "origin"
    files = {"build.cmd": b"@echo off\n", "src/web.js": b"a\nb\n", "app.py": b"print(1)\n"}
    origin.mkdir()
    _git(origin, env, "init", "-q")
    _git(origin, env, "config", "core.autocrlf", "false")
    for rel, data in files.items():
        (origin / rel).parent.mkdir(parents=True, exist_ok=True)
        (origin / rel).write_bytes(data)
    (origin / ".gitattributes").write_bytes(OLD_INSTALLED.encode("utf-8"))
    _git(origin, env, "add", "-A")
    _git(origin, env, *GIT_ID, "commit", "-qm", "installed with the old rules")

    clone = tmp_path / "clone"
    cfg = ["-c", f"core.autocrlf={autocrlf}", "-c", f"core.eol={eol}"]
    subprocess.run(["git", *cfg, "clone", "-q", *cfg, str(origin), str(clone)], capture_output=True, check=True, env=env)
    (origin / ".gitattributes").write_bytes(TEMPLATE.read_bytes())
    _git(origin, env, "add", "-A")
    _git(origin, env, *GIT_ID, "commit", "-qm", "updated to the scoped rules")
    _git(clone, env, "pull", "-q", "--ff-only")

    web = clone / "src" / "web.js"  # a real edit made after the update
    newline = b"\r\n" if b"\r\n" in web.read_bytes() else b"\n"
    web.write_bytes(web.read_bytes() + b"c" + newline)
    time.sleep(1.1)
    for rel in files:
        os.utime(clone / rel)

    modified = sorted(line[3:] for line in _git(clone, env, "status", "--porcelain").splitlines())
    leftovers = [
        f for f in modified
        if subprocess.run(["git", "-C", str(clone), "diff", "--quiet", "--ignore-cr-at-eol", "--", f], env=env).returncode == 0
    ]
    assert "src/web.js" in modified and "src/web.js" not in leftovers, (modified, leftovers)
    assert ("build.cmd" in leftovers) == leftover, (eol, autocrlf, leftovers)
    for f in leftovers:
        _git(clone, env, "checkout", "--", f)
    assert _git(clone, env, "status", "--porcelain").splitlines() == [" M src/web.js"]
    assert "+c" in _git(clone, env, "diff", "--ignore-cr-at-eol", "--", "src/web.js"), "the real edit must survive"
