"""Tests for check_skill_provenance.py (backlog #80 G1a + #81 G1b).

Runs the REAL tool against temp fixture roots and asserts:
  - a complete manifest + conformant skills PASS;
  - each fail mode is caught (missing/orphan row, bad enum, bad/missing
    frontmatter, name!=dir, unknown/missing key, absent manifest file);
  - a SCAFFOLD SKILL.md (HTML-comment header, no frontmatter) is EXEMPT from the
    compatibility floor (its metadata lives in the flat .agent/skills stub);
  - the source-repo gate: a present .agentcortex-manifest (downstream) SKIPS even
    a broken manifest;
  - the REAL repo manifest parses under the no-PyYAML subset parser (D1 guard);
  - the REAL repo currently PASSes end-to-end.

Each fail-mode test doubles as a mutation guard: if the corresponding check were
removed from the tool, that test would go green-on-broken (i.e. fail to fail).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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
    _write_skill(root, "beta-scaffold", frontmatter=False)
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


def test_scaffold_without_frontmatter_is_exempt(tmp_path) -> None:
    # beta-scaffold has no frontmatter; with a valid manifest the run still PASSes
    # (the compatibility floor must NOT fail a scaffold for missing name/description).
    code, out = _run(_good_root(tmp_path))
    assert code == 0, out
    assert "beta-scaffold" in out and "exempt" in out


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

def test_bom_frontmatter_is_validated_not_exempted(tmp_path) -> None:
    # A BOM-prefixed SKILL.md must still be read as HAVING frontmatter (and thus
    # validated), not mistaken for a frontmatter-less scaffold and wrongly exempted.
    root = _good_root(tmp_path)
    d = root / ".agents" / "skills" / "alpha-skill"
    (d / "SKILL.md").write_text(chr(0xFEFF) + "---\nname: wrong\ndescription: x\n---\n# a\n", encoding="utf-8")
    code, out = _run(root)
    assert code == 1
    assert "!= directory" in out


def test_quoted_frontmatter_name_accepted(tmp_path) -> None:
    # A quoted YAML scalar (name: "x") must not be mistaken for a name mismatch.
    root = _good_root(tmp_path)
    d = root / ".agents" / "skills" / "alpha-skill"
    (d / "SKILL.md").write_text('---\nname: "alpha-skill"\ndescription: "x"\n---\n# a\n', encoding="utf-8")
    code, out = _run(root)
    assert code == 0, out
