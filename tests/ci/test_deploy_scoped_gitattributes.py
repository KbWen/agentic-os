"""The installed .gitattributes covers Agentic OS paths only (downstream check, 2026-09-27).

deploy.sh used to install the source repository's own .gitattributes, whose rules are
repo-wide (``*.md``/``*.py``/``*.json``/``*.sh`` ``text eol=lf``, ``*.ps1`` ``eol=crlf``).
In a product that commits CRLF, every product file then showed as a whole-file
line-ending rewrite as soon as an editor or build tool touched it. deploy.sh now installs
``.agentcortex/templates/downstream.gitattributes``: Git's ``* text=auto`` default for
the product's files (it never rewrites a file committed with CRLF), and line endings only
for the files Agentic OS installs and the Markdown its validators read.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DEPLOY_SH = ROOT / ".agentcortex" / "bin" / "deploy.sh"

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
}
# Product-side docs the validators read; they must stay LF on autocrlf=true checkouts.
GOVERNED_DOCS = [
    "docs/specs/feature.md",
    "docs/architecture/api.log.md",
    "docs/adr/ADR-001-stack.md",
    "docs/reviews/2026-01-01-audit.md",
]
# Scaffolds installed only when absent and then owned by the product.
PRODUCT_OWNED = (".gitattributes", ".claude/settings.json")


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


@requires_bash
@pytest.mark.slow
def test_installed_gitattributes_covers_framework_paths_only(tmp_path: Path) -> None:
    target = tmp_path / "product"
    target.mkdir()
    _git(target, "init", "-q")
    _git(target, "config", "core.autocrlf", "false")
    for rel, data in PRODUCT_FILES.items():
        (target / rel).parent.mkdir(parents=True, exist_ok=True)
        (target / rel).write_bytes(data)
    _git(target, "add", "-A")
    _git(target, *GIT_ID, "commit", "-qm", "product")

    deploy = subprocess.run(
        [bash, str(DEPLOY_SH), str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(ROOT),
    )
    assert deploy.returncode == 0, deploy.stderr[-2000:]
    _git(target, "add", "-A")
    _git(target, *GIT_ID, "commit", "-qm", "install")

    # The product's own files get only Git's `text=auto` default, never a line ending ...
    product = list(PRODUCT_FILES)
    assert set(_attr(target, "text", product).values()) == {"auto"}
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
TEMPLATE = ROOT / ".agentcortex" / "templates" / "downstream.gitattributes"


def test_template_normalizes_governed_markdown_and_nothing_of_the_product(tmp_path: Path) -> None:
    """Review of #215: under `text=auto` a governed spec committed with CRLF would stay
    CRLF forever, and the `$`-anchored validators misread it on an LF checkout. Governed
    Markdown is always `text`; everything else of the product keeps Git's default."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / ".gitattributes").write_bytes(TEMPLATE.read_bytes())
    governed = ["docs/specs/a.md", "docs/specs/sub/b.md", "docs/architecture/api.log.md",
                "docs/adr/ADR-001-x.md", "docs/reviews/r.md"]
    product = ["app.py", "src/web.js", "README.md", "docs/guide.md", "docs/specs/diagram.png", "build.cmd"]
    text = _attr(repo, "text", governed + product)
    eol = _attr(repo, "eol", governed + product)
    assert all(text[p] == "set" and eol[p] == "lf" for p in governed), {p: (text[p], eol[p]) for p in governed}
    assert all(text[p] == "auto" and eol[p] == "unspecified" for p in product), {p: (text[p], eol[p]) for p in product}


@pytest.mark.parametrize(
    "eol, autocrlf",
    [("lf", "false"), ("crlf", "false"), ("native", "true")],
    ids=["linux-default", "windows-autocrlf-false", "windows-autocrlf-true"],
)
def test_upgrading_from_the_repo_wide_rules_leaves_every_file_clean(
    tmp_path: Path, eol: str, autocrlf: str
) -> None:
    """Review of #215: dropping `* text=auto` left the working copies the old rules had
    written with CRLF (`*.ps1`/`*.cmd` everywhere, every text file under Windows
    `core.autocrlf=false`) modified against their LF blobs on an update."""
    origin = tmp_path / "origin"
    files = {
        "build.cmd": b"@echo off\n", "run.bat": b"@echo off\n", "scripts/tool.ps1": b"Write-Host hi\n",
        "src/web.js": b"x\n", "README.md": b"# P\n", "app.py": b"print(1)\n",
        "docs/specs/feature.md": b"---\nstatus: draft\n---\n",
        ".agentcortex/bin/validate.sh": b"echo ok\n", ".agentcortex/bin/validate.ps1": b"Write-Host ok\n",
        ".agent/skills/stub": b"stub\n",
    }
    origin.mkdir()
    _git(origin, "init", "-q")
    _git(origin, "config", "core.autocrlf", "false")
    for rel, data in files.items():
        (origin / rel).parent.mkdir(parents=True, exist_ok=True)
        (origin / rel).write_bytes(data)
    (origin / ".gitattributes").write_text(OLD_INSTALLED, encoding="utf-8", newline="\n")
    _git(origin, "add", "-A")
    _git(origin, *GIT_ID, "commit", "-qm", "installed with the old rules")

    clone = tmp_path / "clone"
    cfg = ["-c", f"core.autocrlf={autocrlf}", "-c", f"core.eol={eol}"]
    subprocess.run(["git", *cfg, "clone", "-q", *cfg, str(origin), str(clone)], capture_output=True, check=True)

    (origin / ".gitattributes").write_bytes(TEMPLATE.read_bytes())
    _git(origin, "add", "-A")
    _git(origin, *GIT_ID, "commit", "-qm", "updated to the scoped rules")
    _git(clone, "pull", "-q", "--ff-only")

    time.sleep(1.1)
    for rel in files:
        os.utime(clone / rel)
    status = _git(clone, "status", "--porcelain")
    assert status == "", f"the update left files modified ({eol=}, {autocrlf=}):\n{status}"
