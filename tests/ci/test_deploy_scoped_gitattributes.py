"""The installed .gitattributes leaves the product's own files alone (#215, 2026-09-27).

deploy.sh used to install the source repository's own .gitattributes, whose rules are
repo-wide (``* text=auto``; ``*.md``/``*.py``/``*.json``/``*.sh`` ``text eol=lf``;
``*.ps1``/``*.cmd``/``*.bat`` ``eol=crlf``). In a product that commits CRLF, every product
file then showed as a whole-file line-ending rewrite as soon as an editor or build tool
touched it. deploy.sh now installs ``.agentcortex/templates/downstream.gitattributes``: line
endings only for the files Agentic OS installs and the top-level Markdown its validators
read. A clone checked out under the old rules gets a one-time re-checkout command.
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

# The product's own files, committed with CRLF (core.autocrlf=false).
PRODUCT_FILES = {
    "app.py": b"print(1)\r\n",
    "config.json": b'{"a": 1}\r\n',
    "README.md": b"# Product\r\n",
    "scripts/run.sh": b"echo hi\r\n",
    "scripts/tool.ps1": b"Write-Host hi\r\n",
    "docs/guide.md": b"# Guide\r\n",
    "docs/adr/0001-record.md": b"# Product ADR\r\n",
}
# Top-level Markdown the validators read; it must stay LF on autocrlf=true checkouts.
GOVERNED_DOCS = [
    "docs/specs/feature.md",
    "docs/architecture/api.log.md",
    "docs/adr/ADR-001-stack.md",
    "docs/reviews/2026-01-01-audit.md",
]
# Scaffolds installed only when absent and then owned by the product.
PRODUCT_OWNED = (".gitattributes", ".claude/settings.json")

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


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout


def _attr(repo: Path, attr: str, paths: list[str]) -> dict[str, str]:
    # NUL-separated bytes: text-mode stdin on Windows would turn "\n" into "\r\n",
    # and git would then look up "AGENTS.md\r", which no rule names.
    out = subprocess.run(
        ["git", "-C", str(repo), "check-attr", "-z", "--stdin", attr],
        input=("\0".join(paths) + "\0").encode("utf-8"), capture_output=True, check=True,
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


def _remedy_command() -> str:
    """The one-time re-checkout command exactly as deploy.sh prints it."""
    lines = [l.strip() for l in DEPLOY_SH.read_text(encoding="utf-8").splitlines()]
    matches = [l for l in lines if l.startswith("git ls-files --eol |")]
    assert len(matches) == 1, matches
    return matches[0]


@requires_bash
@pytest.mark.slow
def test_installed_gitattributes_leaves_product_files_alone(tmp_path: Path) -> None:
    target = tmp_path / "product"
    target.mkdir()
    _git(target, "init", "-q")
    _git(target, "config", "core.autocrlf", "false")
    for rel, data in PRODUCT_FILES.items():
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        (target / rel).write_bytes(data)
    _git(target, "add", "-A")
    _git(target, *GIT_ID, "commit", "-qm", "product")

    _deploy(target)
    _git(target, "add", "-A")
    _git(target, *GIT_ID, "commit", "-qm", "install")

    # The product's own files get no line-ending rule from the framework ...
    product = list(PRODUCT_FILES)
    assert set(_attr(target, "text", product).values()) == {"unspecified"}
    assert set(_attr(target, "eol", product).values()) == {"unspecified"}
    # ... so an editor or build tool touching them changes nothing git reports.
    time.sleep(1.1)
    for rel in product:
        os.utime(target / rel)
    status = _git(target, "status", "--porcelain")
    assert status == "", f"touching product files made git report changes:\n{status}"

    # Every file Agentic OS installed resolves a line ending, and so do the governed docs.
    installed = [
        parts[1]
        for parts in (line.split() for line in (target / ".agentcortex-manifest").read_text(encoding="utf-8").splitlines())
        if len(parts) >= 2 and parts[0] in ("core", "scaffold", "wrapper")
    ]
    framework = [p for p in installed if p not in PRODUCT_OWNED and not p.startswith(".github/")]
    assert len(framework) > 150, len(framework)
    eol = _attr(target, "eol", framework + [".agentcortex-manifest"] + GOVERNED_DOCS)
    uncovered = sorted(p for p, v in eol.items() if v not in ("lf", "crlf"))
    assert not uncovered, f"installed paths without a line-ending rule: {uncovered}"
    assert all(eol[p] == "lf" for p in GOVERNED_DOCS + [".agentcortex-manifest"])
    assert all(eol[p] == "lf" for p in framework if p.endswith(".sh"))
    windows = [p for p in framework if p.endswith((".ps1", ".cmd"))]
    assert windows and all(eol[p] == "crlf" for p in windows), {p: eol[p] for p in windows}


@requires_bash
@pytest.mark.slow
def test_update_from_the_old_rules_prints_the_recheckout_notice_once(tmp_path: Path) -> None:
    target = tmp_path / "product"
    target.mkdir()
    _deploy(target)
    gitattributes = target / ".gitattributes"
    manifest = target / ".agentcortex-manifest"

    # An install by v1.8.28 or earlier that the adopter never edited.
    gitattributes.write_bytes(OLD_INSTALLED.encode("utf-8"))
    _set_manifest_hash(manifest, ".gitattributes", OLD_INSTALLED.encode("utf-8"))
    update = _deploy(target)
    assert NOTICE in update.stdout, update.stdout[-1500:]
    assert _remedy_command() in update.stdout
    assert gitattributes.read_bytes().replace(b"\r", b"") == TEMPLATE.read_bytes().replace(b"\r", b"")
    assert "still has the old rules" not in update.stdout

    assert NOTICE not in _deploy(target).stdout, "the notice must not repeat once the old rules are gone"

    # An adopter who customized the old file keeps it and is told what to replace.
    gitattributes.write_bytes((OLD_INSTALLED + "*.bin binary\n").encode("utf-8"))
    customized = _deploy(target)
    assert NOTICE in customized.stdout
    assert "still has the old rules" in customized.stdout
    assert b"*.bin binary" in gitattributes.read_bytes(), "a customized .gitattributes is never overwritten"


def test_template_covers_governed_markdown_and_nothing_of_the_product(tmp_path: Path) -> None:
    """Review of #215: rules on whole docs/ trees also rewrote the product's own Markdown
    there. Only the top-level files the validators read are covered, and nothing else."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / ".gitattributes").write_bytes(TEMPLATE.read_bytes())
    product = [
        "app.py", "src/web.js", "config.json", "deploy.yaml", "scripts/run.sh", "scripts/tool.ps1",
        "build.cmd", "Makefile", "README.md", "docs/guide.md", "docs/specs/diagram.png",
        "docs/specs/archive/2019-prd.md", "docs/architecture/c4/context.md", "docs/adr/drafts/x.md",
    ]
    text = _attr(repo, "text", GOVERNED_DOCS + product)
    eol = _attr(repo, "eol", GOVERNED_DOCS + product)
    assert all(text[p] == "auto" and eol[p] == "lf" for p in GOVERNED_DOCS), {p: (text[p], eol[p]) for p in GOVERNED_DOCS}
    touched = {p: (text[p], eol[p]) for p in product if (text[p], eol[p]) != ("unspecified", "unspecified")}
    assert not touched, f"product paths with a framework line-ending rule: {touched}"


@requires_bash
@pytest.mark.parametrize(
    "eol, autocrlf",
    [("lf", "false"), ("crlf", "false"), ("native", "true")],
    ids=["linux-default", "windows-autocrlf-false", "windows-autocrlf-true"],
)
def test_the_printed_recheckout_command_cleans_an_old_clone_and_keeps_real_edits(
    tmp_path: Path, eol: str, autocrlf: str
) -> None:
    """Review of #215: after the old rules are gone, a clone they checked out keeps CRLF
    working copies of LF blobs (*.ps1/*.cmd/*.bat everywhere; every text file under Windows
    core.autocrlf=false), which git then reports as modified."""
    origin = tmp_path / "origin"
    files = {
        "build.cmd": b"@echo off\n", "run.bat": b"@echo off\n", "scripts/tool.ps1": b"Write-Host hi\n",
        "src/web.js": b"a\nb\n", "README.md": b"# P\n", "app.py": b"print(1)\n", "Makefile": b"all:\n\techo hi\n",
        "docs/specs/feature.md": b"---\nstatus: draft\n---\n", ".agentcortex/bin/validate.sh": b"echo ok\n",
    }
    origin.mkdir()
    _git(origin, "init", "-q")
    _git(origin, "config", "core.autocrlf", "false")
    for rel, data in files.items():
        (origin / rel).parent.mkdir(parents=True, exist_ok=True)
        (origin / rel).write_bytes(data)
    (origin / ".gitattributes").write_bytes(OLD_INSTALLED.encode("utf-8"))
    _git(origin, "add", "-A")
    _git(origin, *GIT_ID, "commit", "-qm", "installed with the old rules")

    clone = tmp_path / "clone"
    cfg = ["-c", f"core.autocrlf={autocrlf}", "-c", f"core.eol={eol}"]
    subprocess.run(["git", *cfg, "clone", "-q", *cfg, str(origin), str(clone)], capture_output=True, check=True)

    (origin / ".gitattributes").write_bytes(TEMPLATE.read_bytes())
    _git(origin, "add", "-A")
    _git(origin, *GIT_ID, "commit", "-qm", "updated to the scoped rules")
    _git(clone, "pull", "-q", "--ff-only")

    # A real edit made after the update; the editor keeps the file's line endings.
    web = clone / "src" / "web.js"
    newline = b"\r\n" if b"\r\n" in web.read_bytes() else b"\n"
    web.write_bytes(web.read_bytes() + b"c" + newline)

    subprocess.run([bash, "-c", _remedy_command()], cwd=str(clone), capture_output=True, check=True)

    time.sleep(1.1)
    for rel in files:
        os.utime(clone / rel)
    status = _git(clone, "status", "--porcelain").splitlines()
    assert status == [" M src/web.js"], f"({eol=}, {autocrlf=}) {status}"
    assert "+c" in _git(clone, "diff", "--ignore-cr-at-eol", "--", "src/web.js"), "the real edit must survive"
