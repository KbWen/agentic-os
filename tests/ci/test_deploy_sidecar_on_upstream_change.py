"""ADR-005 amendment (2026-09-26, backlog #201): a scaffold sidecar is written only when
the framework changed the file since the adopter's baseline, `updated` counts only
writes, and a no-op update leaves the tracked manifest byte-identical.

spec_ref: docs/specs/scaffold-sidecar-on-upstream-change.md

"The framework changed the file" is simulated the way the tiering tests do it: the old
manifest's baseline hash for the file is rewritten, so the unchanged source now differs
from the recorded baseline.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DEPLOY_SH = ROOT / ".agentcortex" / "bin" / "deploy.sh"
SSOT = ".agentcortex/context/current_state.md"
MERGE_BLOCK = "merge each *.acx-incoming into its target"

git = shutil.which("git")
git_root = Path(git).parent.parent if git else None
bash_candidates = [
    str(git_root / "bin" / "bash.exe") if git_root else None,
    str(git_root / "usr" / "bin" / "bash.exe") if git_root else None,
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
    shutil.which("bash"),
]
bash = next((c for c in bash_candidates if c and "WindowsApps" not in c and Path(c).exists()), None)
pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(bash is None or git is None, reason="bash and git are required"),
]


def _deploy(target: Path) -> str:
    r = subprocess.run([bash, str(DEPLOY_SH), str(target)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(ROOT))
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout


def _summary(out: str) -> dict[str, int]:
    m = re.search(r"Summary: (\d+) updated .*?/ (\d+) skipped / (\d+) new / (\d+) removed / "
                  r"(\d+) unchanged / (\d+) kept", out)
    assert m, out[-1500:]
    keys = ("updated", "skipped", "new", "removed", "unchanged", "kept")
    return dict(zip(keys, map(int, m.groups())))


def _sidecars(target: Path) -> list[str]:
    return sorted(p.relative_to(target).as_posix() for p in target.rglob("*.acx-incoming")
                  if ".git" not in p.parts)


def _set_baseline(target: Path, rel: str, digest: str) -> None:
    manifest = target / ".agentcortex-manifest"
    lines = manifest.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        parts = line.split()
        if len(parts) >= 3 and parts[1] == rel:
            parts[2] = f"sha256:{digest}"
            lines[i] = " ".join(parts)
            break
    else:
        raise AssertionError(f"manifest row not found: {rel}")
    manifest.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))


@pytest.fixture()
def installed(tmp_path: Path) -> Path:
    target = tmp_path / "proj"
    target.mkdir()
    subprocess.run([git, "init", "-q", "-b", "main"], cwd=target, check=True)
    _deploy(target)
    with (target / SSOT).open("a", encoding="utf-8") as fh:
        fh.write("\n## Project notes\n\n- the adopter's own content\n")
    subprocess.run([git, "add", "-A"], cwd=target, check=True)
    subprocess.run([git, "-c", "user.email=t@example.invalid", "-c", "user.name=t", "-c", "commit.gpgsign=false",
                    "commit", "-qm", "install"],
                   cwd=target, check=True)
    return target


def test_local_edit_without_a_framework_change_is_kept_without_a_sidecar(installed: Path) -> None:
    """AC-1, AC-3, AC-4, AC-5."""
    manifest_before = (installed / ".agentcortex-manifest").read_bytes()
    ssot_before = (installed / SSOT).read_bytes()

    out = _deploy(installed)
    counts = _summary(out)

    assert _sidecars(installed) == [], "no framework change -> nothing to merge"
    assert "[SKIP]" not in out and MERGE_BLOCK not in out
    assert counts["kept"] == 1 and counts["skipped"] == 0
    assert counts["updated"] == 0, "a no-op update writes nothing"
    assert (installed / SSOT).read_bytes() == ssot_before
    assert (installed / ".agentcortex-manifest").read_bytes() == manifest_before, "manifest must not churn"
    status = subprocess.run(
        [git, "status", "--porcelain"], cwd=installed,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    ).stdout
    assert status == "", status


def test_local_edit_with_a_framework_change_still_gets_a_sidecar(installed: Path) -> None:
    """AC-2, AC-3: the framework changed the file since the baseline -> unchanged behaviour."""
    old_baseline = hashlib.sha256(b"an older template").hexdigest()
    _set_baseline(installed, SSOT, old_baseline)

    out = _deploy(installed)
    counts = _summary(out)

    assert _sidecars(installed) == [SSOT + ".acx-incoming"]
    assert f"[SKIP] {SSOT}" in out and MERGE_BLOCK in out
    assert counts["skipped"] == 1 and counts["kept"] == 0
    offered = hashlib.sha256((ROOT / ".agentcortex" / "templates" / "current_state.md").read_bytes()
                             .replace(b"\r\n", b"\n")).hexdigest()
    assert f"scaffold {SSOT} sha256:{offered}" in (installed / ".agentcortex-manifest").read_text(
        encoding="utf-8"), "the offered version becomes the baseline (review F3)"


def test_an_unmerged_offer_repeats_and_a_deleted_one_does_not(installed: Path) -> None:
    """AC-2a (review F2/F3): the offered version becomes the baseline; the sidecar is
    written again while it still exists, and not after the adopter deletes it."""
    _set_baseline(installed, SSOT, hashlib.sha256(b"an older template").hexdigest())
    first = _deploy(installed)
    assert _sidecars(installed) == [SSOT + ".acx-incoming"], first[-800:]

    again = _deploy(installed)  # the adopter has not dealt with it yet
    assert _sidecars(installed) == [SSOT + ".acx-incoming"], "an unmerged offer must stay"
    assert _summary(again)["skipped"] == 1

    (installed / (SSOT + ".acx-incoming")).unlink()  # merged, then deleted
    after = _deploy(installed)
    assert _sidecars(installed) == [], "a merged-and-deleted offer must not come back"
    assert _summary(after)["kept"] == 1 and MERGE_BLOCK not in after
