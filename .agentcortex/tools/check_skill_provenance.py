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
    SKILL.md`` must begin with closed YAML frontmatter, declare ``name`` +
    ``description``, and use a ``name`` equal to the directory name. Scaffold
    Skills follow the same portable discovery contract as every other Skill.

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
import json
import re
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
    """True when a closed ``---`` block starts at the first decoded byte."""
    lines = text.splitlines()
    return len(lines) >= 2 and lines[0] == "---" and "---" in lines[1:]


def _has_forbidden_yaml_character(text: str) -> bool:
    """Return whether *text* contains a character excluded by YAML 1.2."""
    for char in text:
        codepoint = ord(char)
        if codepoint in {0x09, 0x0A, 0x0D} or 0x20 <= codepoint <= 0x7E or codepoint == 0x85:
            continue
        if 0xA0 <= codepoint <= 0xD7FF or 0xE000 <= codepoint <= 0xFFFD:
            continue
        if 0x10000 <= codepoint <= 0x10FFFF:
            continue
        return True
    return False


# A plain (unquoted) space-free scalar is a STRING unless YAML's implicit
# resolver would read it as a number. Mirroring the resolver is what makes the
# fallback safe to widen: anything this pattern does NOT match cannot come back
# from PyYAML as a non-string, so accepting it cannot break the differential
# oracle in tests/ci/test_skill_provenance.py. Null/bool/int/timestamp forms are
# handled by their own branches before this is consulted.
_IMPLICIT_NUMERIC = re.compile(
    r"""^[-+]?(?:
          0[bB][01_]+                                   # binary
        | 0[xX][0-9a-fA-F_]+                            # hex
        | 0[oO][0-7_]+                                  # octal (YAML 1.2)
        | [0-9][0-9_]*(?::[0-5]?[0-9])+(?:\.[0-9_]*)?   # sexagesimal (YAML 1.1)
        | [0-9][0-9_]*\.[0-9_]*(?:[eE][-+]?[0-9]+)?     # float
        | \.[0-9][0-9_]*(?:[eE][-+]?[0-9]+)?            # .5
        | [0-9][0-9_]*(?:[eE][-+]?[0-9]+)?              # int / exponent
        | \.(?:inf|Inf|INF|nan|NaN|NAN)                 # specials
    )$""",
    re.VERBOSE,
)

# Characters that cannot open a YAML plain scalar. Anything else may, so the
# old "first character must be alphanumeric" rule rejected ordinary values such
# as "(beta) applies when ..." or "_internal".
_PLAIN_SCALAR_FORBIDDEN_FIRST = set("-?:,[]{}#&*!|>'\"%@`")


def _parse_frontmatter_subset(block: str) -> dict[str, object]:
    """Strict dependency-free parser for the scalar frontmatter we require."""
    fields: dict[str, object] = {}
    lines = block.splitlines()
    index = 0
    while index < len(lines):
        raw = lines[index]
        if "\t" in raw:
            raise ValueError(f"raw tab is not supported by the YAML fallback: {raw!r}")
        if _has_forbidden_yaml_character(raw):
            raise ValueError(f"control character is not valid YAML: {raw!r}")
        indent_prefix = raw[: len(raw) - len(raw.lstrip(" \t"))]
        if "\t" in indent_prefix:
            raise ValueError(f"tab indentation is not valid YAML: {raw!r}")
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if raw.startswith((" ", "\t")) or ":" not in raw:
            raise ValueError(f"unsupported or invalid YAML line: {raw!r}")
        key, _, raw_value = raw.partition(":")
        if raw_value and not raw_value.startswith(" "):
            raise ValueError(f"mapping colon must be followed by whitespace: {raw!r}")
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]+", key) or key in fields:
            raise ValueError(f"invalid or duplicate YAML key: {key!r}")
        value = raw_value.strip()
        if not value.startswith(("'", '"')) and re.search(r"(?:^| )#", value):
            raise ValueError(f"inline comments are not supported by the YAML fallback: {raw!r}")
        if re.fullmatch(r"[>|][-+]?", value):
            parts: list[str] = []
            block_indent: int | None = None
            index += 1
            while index < len(lines) and lines[index].startswith((" ", "\t")):
                continuation = lines[index]
                if "\t" in continuation:
                    raise ValueError(
                        f"raw tab is not supported by the YAML fallback: {continuation!r}"
                    )
                if _has_forbidden_yaml_character(continuation):
                    raise ValueError(
                        f"control character is not valid YAML: {continuation!r}"
                    )
                indent_prefix = continuation[: len(continuation) - len(continuation.lstrip(" \t"))]
                if "\t" in indent_prefix:
                    raise ValueError(f"tab indentation is not valid YAML: {continuation!r}")
                part = continuation.strip()
                if part:
                    current_indent = len(indent_prefix)
                    if block_indent is None:
                        block_indent = current_indent
                    elif current_indent < block_indent:
                        raise ValueError(
                            f"decreasing block indentation is not valid YAML: {continuation!r}"
                        )
                    parts.append(part)
                index += 1
            fields[key] = " ".join(parts)
            continue
        lowered = value.lower()
        # `key:` with nothing after it is YAML null. Without this branch the
        # empty string fell through to the plain-scalar arm and crashed on
        # value[0]; a nested block or sequence underneath still fails on its
        # own indented line, which is the message the reader needs.
        if not value or lowered in {"null", "~"}:
            fields[key] = None
        elif lowered in {"true", "false", "yes", "no", "on", "off"}:
            fields[key] = lowered in {"true", "yes", "on"}
        elif value.startswith(("[", "{")):
            raise ValueError(f"collection or malformed scalar is not supported for {key!r}")
        elif value.startswith('"'):
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid double-quoted scalar for {key!r}") from exc
            if not isinstance(parsed_value, str):
                raise ValueError(f"invalid double-quoted scalar for {key!r}")
            if _has_forbidden_yaml_character(parsed_value):
                raise ValueError(f"control character is not valid YAML for {key!r}")
            fields[key] = parsed_value
        elif value.startswith("'"):
            if len(value) < 2 or value[-1] != "'":
                raise ValueError(f"unterminated single-quoted scalar for {key!r}")
            inner = value[1:-1]
            if "'" in inner.replace("''", ""):
                raise ValueError(f"invalid single-quoted scalar for {key!r}")
            fields[key] = inner.replace("''", "'")
        elif re.fullmatch(r"[-+]?\d+", value):
            fields[key] = int(value)
        else:
            if value[0] in _PLAIN_SCALAR_FORBIDDEN_FIRST or re.search(r":(?:[ \t]|$)", value):
                raise ValueError(f"unsafe or invalid plain scalar for {key!r}")
            if re.match(r"^\d{4}-\d{1,2}-\d{1,2}(?:$|[Tt \t])", value):
                raise ValueError(f"implicit timestamp is not a string for {key!r}")
            if _IMPLICIT_NUMERIC.match(value):
                raise ValueError(f"plain scalar is not provably a string for {key!r}")
            fields[key] = value
        index += 1
    return fields


def parse_frontmatter(text: str) -> dict[str, object]:
    """Parse a closed leading YAML block, failing closed on malformed input."""
    lines = text.splitlines()
    if not has_frontmatter(text):
        return {}
    closing = lines[1:].index("---") + 1
    block = "\n".join(lines[1:closing])
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        return _parse_frontmatter_subset(block)
    try:
        parsed = yaml.safe_load(block)
    except Exception as exc:  # noqa: BLE001 - parser-specific exception types are optional
        raise ValueError(f"invalid YAML ({exc})") from exc
    if not isinstance(parsed, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return parsed


def _check_compatibility_floor(skills_dir: Path, skill_dirs: list[str],
                               failures: list[str]) -> None:
    """G1a #80: every SKILL.md must declare portable frontmatter."""
    for name in skill_dirs:
        # Native discovery requires the opening fence to be the file's first
        # bytes. Decode as plain UTF-8 so a BOM cannot be silently discarded.
        text = (skills_dir / name / "SKILL.md").read_text(encoding="utf-8")
        if not has_frontmatter(text):
            failures.append(
                f"{SKILLS_DIR}/{name}/SKILL.md: missing or unclosed leading YAML frontmatter"
            )
            continue
        try:
            fm = parse_frontmatter(text)
        except ValueError as exc:
            failures.append(f"{SKILLS_DIR}/{name}/SKILL.md: invalid frontmatter: {exc}")
            continue
        fm_name = fm.get("name")
        fm_description = fm.get("description")
        if not isinstance(fm_name, str) or not fm_name.strip():
            failures.append(
                f"{SKILLS_DIR}/{name}/SKILL.md: frontmatter `name` must be a non-empty string"
            )
        elif fm_name != name:
            failures.append(
                f"{SKILLS_DIR}/{name}/SKILL.md: frontmatter name '{fm_name}' != directory '{name}'"
            )
        if not isinstance(fm_description, str) or not fm_description.strip():
            failures.append(
                f"{SKILLS_DIR}/{name}/SKILL.md: frontmatter `description` must be a non-empty string"
            )


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
    _check_compatibility_floor(skills_dir, skill_dirs, failures)
    _check_provenance_manifest(root, skill_dirs, failures)

    if failures:
        print(f"FAIL: {len(failures)} skill provenance/compatibility finding(s):")
        for finding in failures:
            print(f"  - {finding}")
        return 1
    print(f"PASS: provenance manifest complete ({len(skill_dirs)} skills) + compatibility floor satisfied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
