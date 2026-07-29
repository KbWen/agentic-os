"""Tests for check_skill_provenance.py (backlog #80 G1a + #81 G1b).

Runs the REAL tool against temp fixture roots and asserts:
  - a complete manifest + conformant skills PASS;
  - each fail mode is caught (missing/orphan row, bad enum, bad/missing
    frontmatter, name!=dir, unknown/missing key, absent manifest file);
  - every SKILL.md, including scaffolds, has standards-compatible frontmatter;
  - the source-repo gate: a present .agentcortex-manifest (downstream) SKIPS even
    a broken manifest;
  - the REAL repo manifest parses under the no-PyYAML subset parser (D1 guard);
  - the REAL repo currently PASSes end-to-end.

Each fail-mode test doubles as a mutation guard: if the corresponding check were
removed from the tool, that test would go green-on-broken (i.e. fail to fail).
"""

from __future__ import annotations

import runpy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agentcortex" / "tools" / "check_skill_provenance.py"
TOOLS_DIR = ROOT / ".agentcortex" / "tools"
MANIFEST = ROOT / ".agentcortex" / "metadata" / "skill-provenance.yaml"

GOOD_ROWS = [
    {"skill": "alpha-skill", "origin": "first-party", "source": "-", "license": "MIT", "license-status": "asserted"},
    {"skill": "beta-scaffold", "origin": "first-party", "source": "-", "license": "MIT", "license-status": "asserted"},
]


def _run(root: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root)],
        capture_output=True, text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout + proc.stderr


def _run_without_site_packages(root: Path) -> tuple[int, str]:
    """Exercise the dependency-free parser path even when PyYAML is installed."""
    proc = subprocess.run(
        [sys.executable, "-S", str(TOOL), "--root", str(root)],
        capture_output=True, text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout + proc.stderr


def _write_skill(root: Path, name: str, *, frontmatter: bool = True,
                 fm_name: str | None = None, description: str = "A test skill.") -> None:
    d = root / ".agents" / "skills" / name
    d.mkdir(parents=True, exist_ok=True)
    if frontmatter:
        nm = name if fm_name is None else fm_name
        body = f"---\nname: {nm}\ndescription: {description}\n---\n\n# {name}\n"
    else:
        body = f"<!-- This is a SCAFFOLD skill -->\n\n# {name}\n\nGeneric guidance.\n"
    (d / "SKILL.md").write_text(body, encoding="utf-8")


def _write_manifest(root: Path, rows: list[dict[str, str]]) -> None:
    d = root / ".agentcortex" / "metadata"
    d.mkdir(parents=True, exist_ok=True)
    out = ["skills:"]
    for r in rows:
        ordered: list[tuple[str, str]] = []
        if "skill" in r:
            ordered.append(("skill", r["skill"]))
        ordered.extend((k, v) for k, v in r.items() if k != "skill")
        first = True
        for k, v in ordered:
            val = f'"{v}"' if k == "source" else v
            out.append(f"  - {k}: {val}" if first else f"    {k}: {val}")
            first = False
    (d / "skill-provenance.yaml").write_text("\n".join(out) + "\n", encoding="utf-8")


def _good_root(tmp: Path) -> Path:
    root = tmp / "proj"
    _write_skill(root, "alpha-skill", frontmatter=True)
    _write_skill(root, "beta-scaffold", frontmatter=True)
    _write_manifest(root, [dict(r) for r in GOOD_ROWS])
    return root


# --- happy paths -----------------------------------------------------------

def test_real_repo_passes() -> None:
    code, out = _run(ROOT)
    assert code == 0, out
    assert "PASS" in out


def test_good_fixture_passes(tmp_path) -> None:
    code, out = _run(_good_root(tmp_path))
    assert code == 0, out
    assert "PASS" in out


def test_dependency_free_parser_passes_valid_scalars_and_fails_closed(tmp_path) -> None:
    code, out = _run_without_site_packages(ROOT)
    assert code == 0, out

    root = _good_root(tmp_path)
    code, out = _run_without_site_packages(root)
    assert code == 0, out

    skill = root / ".agents" / "skills" / "alpha-skill" / "SKILL.md"
    for valid_description in (
        '"quoted text"',
        '"quoted # text"',
        "'quoted text'",
        "'quoted # text'",
        "'don''t'",
        "hello",
        "on call",
    ):
        skill.write_text(
            f"---\nname: alpha-skill\ndescription: {valid_description}\n---\n\n# alpha\n",
            encoding="utf-8",
        )
        code, out = _run_without_site_packages(root)
        assert code == 0, (valid_description, out)

    skill.write_text(
        "---\nname: alpha-skill\ndescription: >\n  valid folded text\n---\n\n# alpha\n",
        encoding="utf-8",
    )
    code, out = _run_without_site_packages(root)
    assert code == 0, out

    skill.write_text(
        "---\nname: alpha-skill\ndescription: >\n\tinvalid tab indent\n---\n\n# alpha\n",
        encoding="utf-8",
    )
    code, out = _run_without_site_packages(root)
    assert code == 1
    assert "frontmatter" in out

    skill.write_text(
        "---\nname: alpha-skill\ndescription: >\n  first line\n second line\n---\n\n# alpha\n",
        encoding="utf-8",
    )
    code, out = _run_without_site_packages(root)
    assert code == 1
    assert "frontmatter" in out

    for invalid_description in (
        "[]",
        "valid: invalid",
        "# comment",
        "&anchor",
        "*alias",
        r'"bad\q"',
        "'don't'",
        "1.25",
        "2026-07-28",
        "2026-07-28 09:30:00",
        "yes",
        "on",
        "bad\tvalue",
        "bad\x01value",
        "bad\u0080value",
        "1 # comment",
        "true # comment",
        "null # comment",
        "0x10 # comment",
    ):
        skill.write_text(
            f"---\nname: alpha-skill\ndescription: {invalid_description}\n---\n\n# alpha\n",
            encoding="utf-8",
        )
        code, out = _run_without_site_packages(root)
        assert code == 1, invalid_description
        assert "frontmatter" in out or "description" in out


def test_dependency_free_scalar_corpus_never_accepts_pyyaml_invalid_or_non_string() -> None:
    yaml = pytest.importorskip("yaml")
    parse_subset = runpy.run_path(str(TOOL))["_parse_frontmatter_subset"]
    values = [
        "A capability used when a matching task runs.",
        "hello",
        "on call",
        '"quoted text"',
        "'don''t'",
        "null",
        "NULL",
        "true",
        "YES",
        "off",
        "1",
        "1.25",
        "1e3",
        "0x10",
        "012",
        "1:20",
        ".inf",
        ".NaN",
        "2026-07-28",
        "2026-07-28 09:30:00",
        "[]",
        "{}",
        "[unterminated",
        "valid: invalid",
        "# comment",
        "&anchor",
        "*alias",
        "!tag value",
        r'"bad\q"',
        "'don't'",
        "bad\tvalue",
        "bad\x01value",
        "bad\u0080value",
        "1 # comment",
        "true # comment",
        "null # comment",
        "0x10 # comment",
    ]
    blocks = [f"description: {value}" for value in values]
    blocks.extend(
        [
            "description: >\n  valid folded text",
            "description: >",
            "description: >\n\tinvalid tab indent",
            "description: >\n  first line\n second line",
            "name:alpha-skill\ndescription: valid text",
            "name: alpha-skill\ndescription:valid text",
        ]
    )

    for block in blocks:
        try:
            parsed = yaml.safe_load(block)
            pyyaml_accepts_string = (
                isinstance(parsed, dict)
                and isinstance(parsed.get("description"), str)
                and bool(parsed["description"].strip())
            )
        except yaml.YAMLError:
            pyyaml_accepts_string = False

        try:
            fallback = parse_subset(block)
            fallback_accepts_string = (
                isinstance(fallback.get("description"), str)
                and bool(fallback["description"].strip())
            )
        except ValueError:
            fallback_accepts_string = False

        assert not fallback_accepts_string or pyyaml_accepts_string, block


def test_fallback_does_not_reject_frontmatter_pyyaml_accepts() -> None:
    """The REVERSE direction of the oracle above.

    The one-directional assert (`not fallback_accepts_string or pyyaml_accepts_string`)
    is structurally incapable of catching a fallback that REJECTS valid YAML, which is
    the failure that actually reaches contributors: `Framework Validation` runs
    `validate.sh` on a bare `actions/setup-python` with no `pip install`, so PyYAML is
    absent and the fallback IS the checker for a gate wired at FAIL severity. A skill
    named `oauth2-hardening` used to pass locally and fail in CI with a message that
    named neither the digit nor PyYAML.
    """
    yaml = pytest.importorskip("yaml")
    parse_subset = runpy.run_path(str(TOOL))["_parse_frontmatter_subset"]

    descriptions = [
        "Apply when reviewing auth flows.",
        "(beta) Apply when reviewing auth flows.",
        "_internal helper applied during review.",
        "/api/v2 conventions applied when editing routes.",
        ".env handling applied when configuring deploys.",
        "Applies to x.y.z releases.",
        "Applies when handling key#values in configs.",
        "Inf",
        "NaN",
    ]
    blocks = [f"name: oauth2-hardening\ndescription: {d}" for d in descriptions]
    blocks.extend(
        [
            "name: web3-signing\ndescription: Apply when signing transactions.",
            "name: s3-buckets\ndescription: Apply when provisioning storage.",
            "name: alpha\ndescription: >-\n  Folded with a strip chomping indicator.",
            "name: alpha\ndescription: >+\n  Folded with a keep chomping indicator.",
            "name: alpha\ndescription: |-\n  Literal with a strip chomping indicator.",
            "name: alpha\ndescription: |+\n  Literal with a keep chomping indicator.",
        ]
    )

    for block in blocks:
        parsed = yaml.safe_load(block)
        assert isinstance(parsed.get("description"), str), f"test corpus bug: {block!r}"
        fallback = parse_subset(block)
        assert isinstance(fallback.get("description"), str), (
            f"fallback rejected frontmatter that PyYAML reads as a string: {block!r}"
        )
        assert isinstance(fallback.get("name"), str), block


def test_fallback_empty_value_does_not_crash() -> None:
    """`key:` with no value reached the plain-scalar arm and raised IndexError.

    `_check_compatibility_floor` catches only ValueError, so this escaped as a raw
    traceback where a finding belonged.
    """
    parse_subset = runpy.run_path(str(TOOL))["_parse_frontmatter_subset"]

    assert parse_subset("name: alpha\ndescription:")["description"] is None

    # A nested sequence underneath must still fail, but on its own indented line
    # and with a message that points at the unsupported construct.
    with pytest.raises(ValueError, match="unsupported or invalid YAML line"):
        parse_subset("name: alpha\ndescription: ok\nallowed-tools:\n  - Read")


def test_fallback_still_rejects_implicit_non_strings() -> None:
    """Widening the plain-scalar rule must not let a number through as a string."""
    parse_subset = runpy.run_path(str(TOOL))["_parse_frontmatter_subset"]

    for value in ["1.5", ".5", "1e3", "0x1f", "0b1011", "0o17", "12:30", ".inf", ".nan",
                  "3.14159", "1_000", "2026-07-29"]:
        with pytest.raises(ValueError):
            parse_subset(f"name: alpha\ndescription: {value}")


def test_scaffold_without_frontmatter_fails(tmp_path) -> None:
    root = _good_root(tmp_path)
    _write_skill(root, "beta-scaffold", frontmatter=False)
    code, out = _run(root)
    assert code == 1
    assert "frontmatter" in out and "beta-scaffold" in out


def test_real_repo_all_skills_have_frontmatter() -> None:
    skill_files = sorted((ROOT / ".agents" / "skills").glob("*/SKILL.md"))
    assert len(skill_files) == 14
    missing = [
        path.parent.name
        for path in skill_files
        if not path.read_bytes().startswith(b"---\n")
    ]
    assert missing == []


def test_app_init_scaffold_contract_is_frontmatter_first() -> None:
    workflow = (ROOT / ".agent" / "workflows" / "app-init.md").read_text(encoding="utf-8")
    minimum = workflow.split("## 5. Skill Scaffold Minimum Structure", 1)[1].split(
        "## 6. Update Spec Intake Awareness", 1
    )[0]
    assert "```markdown\n---\nname: <skill-id>\ndescription:" in minimum
    assert "<!-- This is a SCAFFOLD skill -->" in minimum
    assert "do not put HTML comments before it" in minimum
    assert "Signal tier" in minimum and "machine-enforced" in minimum


def test_app_init_representative_generated_scaffold_passes_checker(tmp_path) -> None:
    workflow = (ROOT / ".agent" / "workflows" / "app-init.md").read_text(encoding="utf-8")
    minimum = workflow.split("## 5. Skill Scaffold Minimum Structure", 1)[1].split(
        "## 6. Update Spec Intake Awareness", 1
    )[0]
    template = minimum.split("```markdown\n", 1)[1].split("```", 1)[0]
    generated = template.replace("<skill-id>", "beta-scaffold").replace(
        "<What the skill does and the task context that should activate it.>",
        "Apply representative conventions when a matching project task is implemented or reviewed.",
    )
    root = _good_root(tmp_path)
    (root / ".agents" / "skills" / "beta-scaffold" / "SKILL.md").write_text(
        generated, encoding="utf-8"
    )
    code, out = _run(root)
    assert code == 0, out


# --- #81 manifest fail modes ----------------------------------------------

def test_missing_manifest_row_fails(tmp_path) -> None:
    root = _good_root(tmp_path)
    _write_manifest(root, [dict(GOOD_ROWS[0])])  # drop beta-scaffold's row
    code, out = _run(root)
    assert code == 1
    assert "missing provenance row" in out and "beta-scaffold" in out


def test_orphan_row_fails(tmp_path) -> None:
    root = _good_root(tmp_path)
    rows = [dict(r) for r in GOOD_ROWS]
    rows.append({"skill": "ghost", "origin": "first-party", "source": "-", "license": "MIT", "license-status": "asserted"})
    _write_manifest(root, rows)
    code, out = _run(root)
    assert code == 1
    assert "orphan" in out and "ghost" in out


def test_bad_license_status_fails(tmp_path) -> None:
    root = _good_root(tmp_path)
    rows = [dict(r) for r in GOOD_ROWS]
    rows[0]["license-status"] = "reviewed"  # not in fail-closed allowlist {asserted}
    _write_manifest(root, rows)
    code, out = _run(root)
    assert code == 1
    assert "license-status" in out


def test_bad_origin_fails(tmp_path) -> None:
    root = _good_root(tmp_path)
    rows = [dict(r) for r in GOOD_ROWS]
    rows[0]["origin"] = "vendored"  # not in {first-party, adapted}
    _write_manifest(root, rows)
    code, out = _run(root)
    assert code == 1
    assert "origin" in out


def test_unknown_key_fails(tmp_path) -> None:
    root = _good_root(tmp_path)
    rows = [dict(r) for r in GOOD_ROWS]
    rows[0]["digest"] = "deadbeef"  # a G2 field; strict allowlist must reject it
    _write_manifest(root, rows)
    code, out = _run(root)
    assert code == 1
    assert "unexpected key" in out


def test_missing_required_key_fails(tmp_path) -> None:
    root = _good_root(tmp_path)
    rows = [dict(r) for r in GOOD_ROWS]
    del rows[0]["license"]
    _write_manifest(root, rows)
    code, out = _run(root)
    assert code == 1
    assert "missing key" in out


def test_missing_manifest_file_fails(tmp_path) -> None:
    root = tmp_path / "proj"
    _write_skill(root, "alpha-skill", frontmatter=True)
    code, out = _run(root)
    assert code == 1
    assert "manifest missing" in out


# --- #80 compatibility-floor fail modes -----------------------------------

def test_frontmatter_name_mismatch_fails(tmp_path) -> None:
    root = _good_root(tmp_path)
    _write_skill(root, "alpha-skill", frontmatter=True, fm_name="wrong-name")
    code, out = _run(root)
    assert code == 1
    assert "!= directory" in out


def test_missing_description_fails(tmp_path) -> None:
    root = _good_root(tmp_path)
    d = root / ".agents" / "skills" / "alpha-skill"
    (d / "SKILL.md").write_text("---\nname: alpha-skill\n---\n\n# alpha\n", encoding="utf-8")
    code, out = _run(root)
    assert code == 1
    assert "description" in out


def test_empty_description_fails(tmp_path) -> None:
    root = _good_root(tmp_path)
    d = root / ".agents" / "skills" / "alpha-skill"
    (d / "SKILL.md").write_text("---\nname: alpha-skill\ndescription:\n---\n\n# alpha\n", encoding="utf-8")
    code, out = _run(root)
    assert code == 1
    assert "description" in out


def test_unclosed_frontmatter_fails(tmp_path) -> None:
    root = _good_root(tmp_path)
    d = root / ".agents" / "skills" / "alpha-skill"
    (d / "SKILL.md").write_text("---\nname: alpha-skill\ndescription: broken\n# alpha\n", encoding="utf-8")
    code, out = _run(root)
    assert code == 1
    assert "frontmatter" in out


@pytest.mark.parametrize(
    "description",
    ["null", "false", "[]", "[unterminated", ">"],
    ids=["null", "boolean", "list", "invalid-yaml", "folded-empty"],
)
def test_non_string_or_invalid_description_fails(tmp_path, description: str) -> None:
    root = _good_root(tmp_path)
    d = root / ".agents" / "skills" / "alpha-skill"
    (d / "SKILL.md").write_text(
        f"---\nname: alpha-skill\ndescription: {description}\n---\n\n# alpha\n",
        encoding="utf-8",
    )
    code, out = _run(root)
    assert code == 1
    assert "frontmatter" in out or "description" in out


# --- source-repo gate (D3) -------------------------------------------------

def test_downstream_manifest_present_skips(tmp_path) -> None:
    root = _good_root(tmp_path)
    # Break the manifest so it WOULD fail in a source repo...
    _write_manifest(root, [{"skill": "ghost", "origin": "BAD", "source": "-", "license": "MIT", "license-status": "BAD"}])
    # ...but mark the tree as a deployed downstream project:
    (root / ".agentcortex-manifest").write_text("core AGENTS.md sha256:0\n", encoding="utf-8")
    code, out = _run(root)
    assert code == 0, out
    assert "source-repo-only" in out


# --- D1: manifest parses without PyYAML (subset parser) --------------------

def test_real_manifest_parses_without_pyyaml(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "yaml", None)  # force ImportError in load_data
    monkeypatch.syspath_prepend(str(TOOLS_DIR))
    import _yaml_loader

    data = _yaml_loader.load_data(MANIFEST)
    skills = {s["skill"]: s for s in data["skills"]}
    assert "karpathy-principles" in skills
    karpathy = skills["karpathy-principles"]
    assert karpathy["origin"] == "adapted"
    # special chars (parens, semicolon) must survive the dependency-free parser:
    assert "no root LICENSE artifact" in karpathy["license"]
    assert karpathy["license-status"] == "asserted"


# --- robustness (review LOW findings) --------------------------------------

def test_bom_before_frontmatter_fails_first_bytes_contract(tmp_path) -> None:
    root = _good_root(tmp_path)
    d = root / ".agents" / "skills" / "alpha-skill"
    (d / "SKILL.md").write_text(chr(0xFEFF) + "---\nname: alpha-skill\ndescription: x\n---\n# a\n", encoding="utf-8")
    code, out = _run(root)
    assert code == 1
    assert "leading YAML frontmatter" in out


def test_quoted_frontmatter_name_accepted(tmp_path) -> None:
    # A quoted YAML scalar (name: "x") must not be mistaken for a name mismatch.
    root = _good_root(tmp_path)
    d = root / ".agents" / "skills" / "alpha-skill"
    (d / "SKILL.md").write_text('---\nname: "alpha-skill"\ndescription: "x"\n---\n# a\n', encoding="utf-8")
    code, out = _run(root)
    assert code == 0, out
