"""Release metadata must stay aligned across every canonical version surface."""

from datetime import date
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
VERSION_PATTERN = r"\d+\.\d+\.\d+"


def _single_match(relative_path: str, pattern: str) -> str:
    path = ROOT / relative_path
    matches = re.findall(pattern, path.read_text(encoding="utf-8-sig"), re.MULTILINE)
    assert len(matches) == 1, (
        f"{relative_path} must contain exactly one canonical release-version value; "
        f"found {len(matches)}"
    )
    return matches[0]


def test_release_version_surfaces_match_deploy_source() -> None:
    expected = _single_match(
        ".agentcortex/bin/deploy.sh",
        rf'^ACX_VERSION="({VERSION_PATTERN})"$',
    )
    surfaces = {
        "CITATION.cff": rf"^version:\s*({VERSION_PATTERN})\s*$",
        ".agentcortex/docs/TESTING_PROTOCOL.md": rf"^# Testing Protocol v({VERSION_PATTERN})\s*$",
        ".agentcortex/docs/TESTING_PROTOCOL_zh-TW.md": rf"^# Testing Protocol \(測試教戰守則\) v({VERSION_PATTERN})\s*$",
        ".agentcortex/docs/guides/antigravity-v5-runtime.md": rf"framework release version \(v({VERSION_PATTERN})\)",
        "docs/AGENT_MODEL_GUIDE.md": rf"^# Agentic OS v({VERSION_PATTERN}) — Model Selection Guide$",
        "docs/AGENT_MODEL_GUIDE_zh-TW.md": rf"^# Agentic OS v({VERSION_PATTERN}) — 模型選擇指南$",
    }

    observed = {
        path: _single_match(path, pattern)
        for path, pattern in surfaces.items()
    }
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8-sig")
    newest_heading = re.search(
        rf"^## \[({VERSION_PATTERN})\] - \d{{4}}-\d{{2}}-\d{{2}}$",
        changelog,
        re.MULTILINE,
    )
    assert newest_heading is not None, "CHANGELOG.md has no release heading"
    observed["CHANGELOG.md"] = newest_heading.group(1)
    mismatches = {path: version for path, version in observed.items() if version != expected}

    assert not mismatches, f"release version {expected} is inconsistent: {mismatches}"


def test_citation_release_date_is_not_older_than_changelog() -> None:
    citation_date = _single_match(
        "CITATION.cff",
        r"^date-released:\s*(\d{4}-\d{2}-\d{2})\s*$",
    )
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8-sig")
    newest_heading = re.search(
        rf"^## \[({VERSION_PATTERN})\] - (\d{{4}}-\d{{2}}-\d{{2}})$",
        changelog,
        re.MULTILINE,
    )
    assert newest_heading is not None, "CHANGELOG.md has no release heading"

    assert date.fromisoformat(citation_date) >= date.fromisoformat(newest_heading.group(2)), (
        f"CITATION.cff date-released {citation_date} predates newest CHANGELOG release "
        f"{newest_heading.group(1)} ({newest_heading.group(2)})"
    )
