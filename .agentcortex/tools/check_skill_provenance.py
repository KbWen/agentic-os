#!/usr/bin/env python3
"""Skill provenance + compatibility-floor checker (source-repo only).

Two source-repo-only checks over first-party skills in ``.agents/skills/``:

  (G1b / backlog #81) Provenance inventory: a static manifest at
    ``.agentcortex/metadata/skill-provenance.yaml`` records, per skill, its
    origin / source+revision / license / license-status. This check verifies
    the manifest is COMPLETE (exactly one row per skill dir, no orphan rows,
    no duplicates) and that each row uses only allowed enum values (origin,
    license-status) via a strict, fail-closed allowlist.

  (G1a / backlog #80) Compatibility floor: every ``.agents/skills/<name>/
    SKILL.md`` that HAS YAML frontmatter must declare ``name`` + ``description``
    and ``name`` must equal the directory name. SCAFFOLD skills (whose SKILL.md
    leads with an HTML comment and carries no ``---`` frontmatter block -- their
    metadata lives in the flat ``.agent/skills/<name>`` stub, already validated
    by validate_trigger_metadata.py) are EXEMPT.

Scope: SOURCE REPO ONLY. When a ``.agentcortex-manifest`` is present (a deployed
downstream project), this check is skipped (returns 0): the manifest is a
source-only artifact that deploy.sh does not ship, and a downstream fork
customizes its own skill set. This is the inverse of check_command_sync.py's
source-repo gate.

Out of scope (deferred to G2, gated on a separately-approved external
skill-installation capability): content digests, per-skill file manifests,
downloaded-byte verification, security-exception schemas.

Exit codes:
  0  no FAIL findings (PASS), or skipped (downstream)
  1  one or more FAIL findings
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Reuse the framework's dependency-free YAML/JSON loader (no hard PyYAML dep).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _yaml_loader import load_data  # noqa: E402

SKILLS_DIR = ".agents/skills"
MANIFEST_PATH = ".agentcortex/metadata/skill-provenance.yaml"

# Strict, fail-closed allowlists. Expand ONLY when a producer for the new value
# exists -- e.g. add "detected"/"reviewed" to LICENSE_STATUSES when a license
# scanner or human-review process is actually wired (see the G2 reopen-trigger).
ALLOWED_ORIGINS = {"first-party", "adapted"}
ALLOWED_LICENSE_STATUSES = {"asserted"}
REQUIRED_ENTRY_KEYS = {"skill", "origin", "source", "license", "license-status"}


def has_frontmatter(text: str) -> bool:
    """True if the file's first non-empty line is a ``---`` frontmatter fence."""
    for line in text.splitlines():
        if line.strip() == "":
            continue
        return line.strip() == "---"
    return False


def parse_frontmatter(text: str) -> dict[str, str]:
    """Extract top-level ``key: value`` pairs from a leading ``---`` block."""
    lines = text.splitlines()
    opening = None
    for i, line in enumerate(lines):
        if line.strip() == "":
            continue
        if line.strip() == "---":
            opening = i
        break
    if opening is None:
        return {}
    fields: dict[str, str] = {}
    for line in lines[opening + 1:]:
        if line.strip() == "---":
            break
        if line and line[0] not in (" ", "\t") and ":" in line:
            key, _, value = line.partition(":")
            value = value.strip()
            if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
                value = value[1:-1]  # tolerate a quoted scalar (name: "x")
            fields[key.strip()] = value
    return fields


def _check_compatibility_floor(skills_dir: Path, skill_dirs: list[str],
                               failures: list[str], notes: list[str]) -> None:
    """G1a #80: frontmatter-present SKILL.md must declare name+description, name==dir."""
    for name in skill_dirs:
        # utf-8-sig tolerates a leading BOM so a BOM'd SKILL.md is still seen as
        # having frontmatter (and validated) rather than mistaken for a scaffold.
        text = (skills_dir / name / "SKILL.md").read_text(encoding="utf-8-sig")
        if not has_frontmatter(text):
            notes.append(
                f"{name}: scaffold SKILL.md (no frontmatter) -- compatibility floor "
                f"exempt (metadata in flat .agent/skills/{name})"
            )
            continue
        fm = parse_frontmatter(text)
        if not fm.get("name"):
            failures.append(f"{SKILLS_DIR}/{name}/SKILL.md: frontmatter missing required `name`")
        elif fm["name"] != name:
            failures.append(
                f"{SKILLS_DIR}/{name}/SKILL.md: frontmatter name '{fm['name']}' != directory '{name}'"
            )
        if not fm.get("description"):
            failures.append(f"{SKILLS_DIR}/{name}/SKILL.md: frontmatter missing required `description`")


def _check_provenance_manifest(root: Path, skill_dirs: list[str],
                               failures: list[str]) -> None:
    """G1b #81: manifest presence, strict-allowlist schema, completeness."""
    manifest_path = root / MANIFEST_PATH
    if not manifest_path.is_file():
        failures.append(f"provenance manifest missing: {MANIFEST_PATH}")
        return

    try:
        data = load_data(manifest_path)
    except Exception as exc:  # noqa: BLE001 - surface any parse error as a finding
        failures.append(f"{MANIFEST_PATH}: failed to parse ({exc})")
        return

    if not isinstance(data, dict) or not isinstance(data.get("skills"), list):
        failures.append(f"{MANIFEST_PATH}: expected a top-level mapping with a `skills:` list")
        return

    manifest_skills: list[str] = []
    for idx, entry in enumerate(data["skills"]):
        if not isinstance(entry, dict):
            failures.append(f"{MANIFEST_PATH}: skills[{idx}] is not a mapping")
            continue
        keys = set(entry.keys())
        extra = keys - REQUIRED_ENTRY_KEYS
        missing = REQUIRED_ENTRY_KEYS - keys
        if extra:
            failures.append(f"{MANIFEST_PATH}: skills[{idx}] has unexpected key(s): {sorted(extra)}")
        if missing:
            failures.append(f"{MANIFEST_PATH}: skills[{idx}] missing key(s): {sorted(missing)}")
            continue
        skill_name = str(entry["skill"])
        manifest_skills.append(skill_name)
        if entry["origin"] not in ALLOWED_ORIGINS:
            failures.append(
                f"{MANIFEST_PATH}: '{skill_name}' origin '{entry['origin']}' not in {sorted(ALLOWED_ORIGINS)}"
            )
        if entry["license-status"] not in ALLOWED_LICENSE_STATUSES:
            failures.append(
                f"{MANIFEST_PATH}: '{skill_name}' license-status '{entry['license-status']}' "
                f"not in {sorted(ALLOWED_LICENSE_STATUSES)}"
            )

    manifest_set = set(manifest_skills)
    if len(manifest_skills) != len(manifest_set):
        dupes = sorted({s for s in manifest_skills if manifest_skills.count(s) > 1})
        failures.append(f"{MANIFEST_PATH}: duplicate skill row(s): {dupes}")
    dir_set = set(skill_dirs)
    for missing_row in sorted(dir_set - manifest_set):
        failures.append(f"{MANIFEST_PATH}: missing provenance row for skill '{missing_row}'")
    for orphan in sorted(manifest_set - dir_set):
        failures.append(f"{MANIFEST_PATH}: orphan provenance row '{orphan}' (no matching skill dir)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Skill provenance + compatibility-floor checker (source-repo only)."
    )
    parser.add_argument("--root", default=".", help="Repository root (default: cwd)")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    # Source-repo gate: skip downstream (manifest present). Inverse of
    # check_command_sync.py -- the provenance manifest is a source-only artifact
    # deploy.sh does not ship, and forks customize their own skill set.
    if (root / ".agentcortex-manifest").is_file():
        print("Downstream deploy detected (.agentcortex-manifest present) -- "
              "skill provenance is source-repo-only; skipped.")
        return 0

    skills_dir = root / SKILLS_DIR
    if not skills_dir.is_dir():
        print(f"skills directory not found: {SKILLS_DIR} -- nothing to check.")
        return 0

    skill_dirs = sorted(
        p.name for p in skills_dir.iterdir()
        if p.is_dir() and (p / "SKILL.md").is_file()
    )

    failures: list[str] = []
    notes: list[str] = []
    _check_compatibility_floor(skills_dir, skill_dirs, failures, notes)
    _check_provenance_manifest(root, skill_dirs, failures)

    for note in notes:
        print(f"  note: {note}")
    if failures:
        print(f"FAIL: {len(failures)} skill provenance/compatibility finding(s):")
        for finding in failures:
            print(f"  - {finding}")
        return 1
    print(f"PASS: provenance manifest complete ({len(skill_dirs)} skills) + compatibility floor satisfied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
