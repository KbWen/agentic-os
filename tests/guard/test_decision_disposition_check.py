"""Guard tests for check_decision_disposition.py — the advisory decision-
disposition checker for archived Work Log `## Decisions` sections (spec AC-5/AC-8).

The tool is WARN-tier / never-FAIL (ADR-006 run_python_check contract): it
ALWAYS exits 0 and prints a single `WARN: ...` line only when a post-cutoff
archived log has a `### D-` entry missing all three disposition markers. Until
`document_lifecycle.decision_disposition_since` is set it is a silent no-op.

These tests drive the pure-Python tool as a real subprocess against synthetic
repo roots built under pytest tmp_path — deterministic, fast, no bash/PowerShell.
The tool derives its archive dir / INDEX / config from `--root`, so each test
assembles a miniature `.agentcortex/context/archive/` + `.agent/config.yaml`.

Coverage (spec AC-8):
  * post-cutoff unmarked          -> WARN naming the file + remediation text
  * fully-marked (all 3 markers)  -> clean, no WARN
  * pre-cutoff unmarked           -> grandfathered clean
  * config key absent / no file / empty -> "not configured — skipped"
  * filename `-YYYYMMDD` fallback when the log is absent from INDEX
  * marker vocabulary             -> 3 strict `→` forms + ASCII `->` variants
                                     accepted; true near-misses rejected
  * fenced-quote immunity         -> `## Decisions`/`### D-` inside ``` fences
                                     is quoted format, not structure
  * Signal A2                     -> disposed `→ local` naming an ADR id warns
                                     (promoted-ADR / no-ADR / fenced-ADR clean);
                                     both signals together = exactly 2 WARN lines
  * `## Decisions` with zero `### D-` entries -> not a finding
  * mixed marked+unmarked entries -> log flagged
  * multiple offenders            -> ONE aggregated WARN line per signal
  * excluded surfaces             -> ship-history-*, .gitkeep.md, work/ skipped
  * malformed INDEX line          -> skipped, never crashes
  * real-repo run                 -> clean (legacy Decisions logs predate cutoff)
  * sh + ps1 wiring parity        -> both validators carry tool + label
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / ".agentcortex" / "tools" / "check_decision_disposition.py"
VALIDATE_SH = ROOT / ".agentcortex" / "bin" / "validate.sh"
VALIDATE_PS1 = ROOT / ".agentcortex" / "bin" / "validate.ps1"

CUTOFF = "2026-07-16"
STD_CONFIG = "document_lifecycle:\n" f'  decision_disposition_since: "{CUTOFF}"\n'

# A post- and a pre-cutoff date for date-gating.
POST = "2026-07-20"
PRE = "2026-07-01"


# ---------------------------------------------------------------------------
# Synthetic-repo builders
# ---------------------------------------------------------------------------

def decisions_log(entries: list[tuple[str, str | None]]) -> str:
    """Build a Work Log body with a `## Decisions` section.

    entries: list of (title, marker_or_None). When marker is None the entry is
    left undisposed; otherwise the marker string is appended as a bullet.
    """
    parts = ["# Work Log — synthetic", "", "## Decisions", ""]
    for i, (title, marker) in enumerate(entries, start=1):
        parts.append(f"### D-{i}: {title}")
        parts.append("- **Decision**: did a thing on this branch.")
        parts.append("- **Impact**: local blast radius.")
        if marker is not None:
            parts.append(f"- **Disposition**: {marker}")
        parts.append("")
    parts += ["## Session Info", "- Owner: test", ""]
    return "\n".join(parts)


def build_root(
    tmp_path: Path,
    logs: dict[str, str],
    index: list[dict] | None,
    config: str | None = STD_CONFIG,
) -> Path:
    """Assemble a synthetic repo root and return it.

    logs   : {filename: markdown-content} written to archive root (or work/ if
             the key contains a slash, e.g. "work/foo.md").
    index  : list of INDEX.jsonl records, or None to omit the INDEX file.
    config : .agent/config.yaml content, or None to omit the config file.
    """
    archive = tmp_path / ".agentcortex" / "context" / "archive"
    archive.mkdir(parents=True)
    for rel, content in logs.items():
        dest = archive / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
    if index is not None:
        body = "\n".join(json.dumps(rec) for rec in index) + "\n"
        (archive / "INDEX.jsonl").write_text(body, encoding="utf-8")
    if config is not None:
        cfg = tmp_path / ".agent" / "config.yaml"
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(config, encoding="utf-8")
    return tmp_path


def run_tool(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), "--root", str(root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def idx(log: str, shipped: str) -> dict:
    return {"branch": "x", "log": log, "shipped": shipped, "specs": []}


# ---------------------------------------------------------------------------
# Core disposition behavior
# ---------------------------------------------------------------------------

def test_post_cutoff_unmarked_warns(tmp_path):
    log = "feat-thing-20260720.md"
    root = build_root(
        tmp_path,
        {log: decisions_log([("keep local scope", None)])},
        index=[idx(log, POST)],
    )
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    assert "WARN:" in r.stdout
    assert log in r.stdout
    assert f"shipped since {CUTOFF}" in r.stdout
    # Remediation guidance: archived logs are immutable — fix goes to ADR/L2.
    assert "do NOT edit them" in r.stdout
    assert "ship.md 2b" in r.stdout
    assert "accepted historical gap" in r.stdout
    # Non-clearing clause: the forward-fix cannot silence this WARN, and that
    # must never become a reason to edit the immutable archive.
    assert "does NOT clear" in r.stdout
    assert "never a reason to edit the archive" in r.stdout


def test_all_three_markers_clean(tmp_path):
    log = "feat-marked-20260720.md"
    body = decisions_log(
        [
            ("durable precedent", "→ promoted: ADR-011"),
            ("folded into domain", "→ consolidated: L2 document-governance"),
            ("branch local only", "→ local"),
        ]
    )
    root = build_root(tmp_path, {log: body}, index=[idx(log, POST)])
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    assert "WARN:" not in r.stdout
    assert "decision disposition OK" in r.stdout
    assert "1 logs checked" in r.stdout
    assert f"cutoff {CUTOFF}" in r.stdout


def test_pre_cutoff_unmarked_grandfathered(tmp_path):
    log = "feat-old-20260701.md"
    root = build_root(
        tmp_path,
        {log: decisions_log([("undisposed but old", None)])},
        index=[idx(log, PRE)],
    )
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    assert "WARN:" not in r.stdout
    assert log not in r.stdout
    assert "decision disposition OK" in r.stdout
    # Grandfathered logs are not counted as checked.
    assert "0 logs checked" in r.stdout


# ---------------------------------------------------------------------------
# Opt-in switch (config key)
# ---------------------------------------------------------------------------

def test_config_key_absent_not_configured(tmp_path):
    # Config file present but the key is missing → silent no-op.
    other_config = "document_lifecycle:\n  ship_history_max_entries: 10\n"
    log = "feat-thing-20260720.md"
    root = build_root(
        tmp_path,
        {log: decisions_log([("unmarked", None)])},
        index=[idx(log, POST)],
        config=other_config,
    )
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    assert "not configured — skipped" in r.stdout
    assert "WARN:" not in r.stdout


def test_no_config_file_not_configured(tmp_path):
    log = "feat-thing-20260720.md"
    root = build_root(
        tmp_path,
        {log: decisions_log([("unmarked", None)])},
        index=[idx(log, POST)],
        config=None,
    )
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    assert "not configured — skipped" in r.stdout
    assert "WARN:" not in r.stdout


def test_empty_cutoff_not_configured(tmp_path):
    empty_config = 'document_lifecycle:\n  decision_disposition_since: ""\n'
    log = "feat-thing-20260720.md"
    root = build_root(
        tmp_path,
        {log: decisions_log([("unmarked", None)])},
        index=[idx(log, POST)],
        config=empty_config,
    )
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    assert "not configured — skipped" in r.stdout
    assert "WARN:" not in r.stdout


# ---------------------------------------------------------------------------
# Date resolution
# ---------------------------------------------------------------------------

def test_filename_date_fallback_when_absent_from_index(tmp_path):
    # No INDEX file at all → the `-YYYYMMDD` filename suffix drives the date.
    log = "orphan-nolog-20260801.md"
    root = build_root(
        tmp_path,
        {log: decisions_log([("unmarked orphan", None)])},
        index=None,
    )
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    assert "WARN:" in r.stdout
    assert log in r.stdout


def test_malformed_index_line_is_skipped(tmp_path):
    # A garbage INDEX line must not crash the scan; the valid record still
    # date-gates the log (pre-cutoff → grandfathered clean).
    log = "feat-old-20260701.md"
    archive = tmp_path / ".agentcortex" / "context" / "archive"
    archive.mkdir(parents=True)
    (archive / log).write_text(decisions_log([("unmarked", None)]), encoding="utf-8")
    (archive / "INDEX.jsonl").write_text(
        "this is not json at all\n" + json.dumps(idx(log, PRE)) + "\n",
        encoding="utf-8",
    )
    cfg = tmp_path / ".agent" / "config.yaml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(STD_CONFIG, encoding="utf-8")
    r = run_tool(tmp_path)
    assert r.returncode == 0, r.stderr
    assert "Traceback" not in r.stderr
    assert "WARN:" not in r.stdout
    assert "decision disposition OK" in r.stdout


# ---------------------------------------------------------------------------
# Marker vocabulary exactness (regex-stable 4-surface API)
# ---------------------------------------------------------------------------

def test_marker_vocabulary_accepted(tmp_path):
    # The 3 strict `→` forms are the emit vocabulary; the ASCII `->` variants
    # are accept-side leniency (normalized to `→` before matching).
    accepted = (
        "→ promoted: ADR-011",
        "→ consolidated: L2 domain",
        "→ local",
        "-> promoted: ADR-9",
        "-> consolidated: L2 document-governance",
        "-> local",
    )
    for i, marker in enumerate(accepted):
        log = "feat-one-20260720.md"
        root = build_root(
            tmp_path / f"accepted_{i}",
            {log: decisions_log([("exact marker", marker)])},
            index=[idx(log, POST)],
        )
        r = run_tool(root)
        assert r.returncode == 0, r.stderr
        assert "WARN:" not in r.stdout, f"marker {marker!r} should be accepted"
        assert "decision disposition OK" in r.stdout


def test_marker_near_miss_rejected(tmp_path):
    # True near-misses stay undisposed → WARN: wrong word (`promote`), wrong
    # case (`Promoted`), missing space after the arrow, or no arrow at all.
    # (ASCII `->` alone is NOT a near-miss — it is normalized and accepted.)
    near_misses = (
        "→ promote: ADR-011",
        "→ Promoted: ADR-011",
        "→consolidated: L2 x",
        "promoted: ADR-011",
    )
    for i, near_miss in enumerate(near_misses):
        log = "feat-near-20260720.md"
        root = build_root(
            tmp_path / f"near_miss_{i}",
            {log: decisions_log([("near miss", near_miss)])},
            index=[idx(log, POST)],
        )
        r = run_tool(root)
        assert r.returncode == 0, r.stderr
        assert "WARN:" in r.stdout, f"near-miss {near_miss!r} must NOT be accepted"
        assert log in r.stdout


# ---------------------------------------------------------------------------
# Section / entry edge cases
# ---------------------------------------------------------------------------

def test_decisions_section_without_d_entries_not_a_finding(tmp_path):
    # A `## Decisions` header whose body has no `### D-` entries (the `none`
    # default) is not a finding — and is not counted as checked.
    body = "# Work Log\n\n## Decisions\n\nnone\n\n## Session Info\n- Owner: test\n"
    log = "feat-empty-decisions-20260720.md"
    root = build_root(tmp_path, {log: body}, index=[idx(log, POST)])
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    assert "WARN:" not in r.stdout
    assert "decision disposition OK" in r.stdout
    assert "0 logs checked" in r.stdout


def test_fenced_decisions_quote_not_a_finding(tmp_path):
    # A post-cutoff log whose ONLY `## Decisions`/`### D-` content sits inside
    # a ``` fenced code block is quoting the format (e.g. this feature's own
    # dogfood work log), not declaring decisions → never a finding.
    body = (
        "# Work Log — documents the disposition format\n"
        "\n"
        "## Notes\n"
        "\n"
        "The vocabulary, quoted for reference:\n"
        "\n"
        "```markdown\n"
        "## Decisions\n"
        "\n"
        "### D-1: quoted example\n"
        "- **Decision**: this is documentation, not a real decision entry.\n"
        "```\n"
        "\n"
        "## Session Info\n"
        "- Owner: test\n"
    )
    log = "feat-fenced-20260720.md"
    root = build_root(tmp_path, {log: body}, index=[idx(log, POST)])
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    assert "WARN:" not in r.stdout
    assert "decision disposition OK" in r.stdout
    # The fenced quote never opens a Decisions section → not even "checked".
    assert "0 logs checked" in r.stdout


def test_mixed_marked_and_unmarked_flags_log(tmp_path):
    # One disposed + one undisposed entry → the log is still flagged.
    log = "feat-mixed-20260720.md"
    body = decisions_log(
        [("disposed", "→ local"), ("forgotten", None)]
    )
    root = build_root(tmp_path, {log: body}, index=[idx(log, POST)])
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    assert "WARN:" in r.stdout
    assert log in r.stdout


def test_multiple_offenders_aggregate_single_warn(tmp_path):
    a = "feat-a-20260720.md"
    b = "feat-b-20260721.md"
    root = build_root(
        tmp_path,
        {
            a: decisions_log([("unmarked a", None)]),
            b: decisions_log([("unmarked b", None)]),
        },
        index=[idx(a, POST), idx(b, "2026-07-21")],
    )
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    warn_lines = [ln for ln in r.stdout.splitlines() if ln.startswith("WARN:")]
    assert len(warn_lines) == 1, f"expected ONE aggregated WARN line, got {warn_lines}"
    assert "2 archived log(s)" in warn_lines[0]
    assert a in warn_lines[0] and b in warn_lines[0]


# ---------------------------------------------------------------------------
# Signal A2 — suspicious `→ local` entries that name an ADR
# ---------------------------------------------------------------------------

def test_a2_local_naming_adr_warns(tmp_path):
    # Disposed `→ local` but the entry names ADR-007 → the A2 advisory fires;
    # Signal A stays silent (the entry IS disposed).
    log = "feat-rubberstamp-20260720.md"
    body = decisions_log(
        [("supersedes the ADR-007 lock policy for this repo", "→ local")]
    )
    root = build_root(tmp_path, {log: body}, index=[idx(log, POST)])
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    warn_lines = [ln for ln in r.stdout.splitlines() if ln.startswith("WARN:")]
    assert len(warn_lines) == 1, f"expected ONE A2 WARN line, got {warn_lines}"
    assert "`→ local`" in warn_lines[0]
    assert "ADR-007" in warn_lines[0]
    assert "review whether → promoted/→ consolidated applies" in warn_lines[0]
    assert log in warn_lines[0]
    # No Signal-A line and no OK line alongside a WARN.
    assert "undisposed" not in r.stdout
    assert "decision disposition OK" not in r.stdout


def test_a2_promoted_adr_fully_clean(tmp_path):
    # The same ADR-naming entry disposed `→ promoted: ADR-007` is the correct
    # call → neither signal fires.
    log = "feat-promoted-20260720.md"
    body = decisions_log(
        [("supersedes the ADR-007 lock policy for this repo", "→ promoted: ADR-007")]
    )
    root = build_root(tmp_path, {log: body}, index=[idx(log, POST)])
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    assert "WARN:" not in r.stdout
    assert "decision disposition OK" in r.stdout


def test_a2_local_without_adr_clean(tmp_path):
    # `→ local` with no ADR mention anywhere → A2 silent.
    log = "feat-plain-local-20260720.md"
    body = decisions_log([("branch-local naming convention", "→ local")])
    root = build_root(tmp_path, {log: body}, index=[idx(log, POST)])
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    assert "WARN:" not in r.stdout
    assert "decision disposition OK" in r.stdout


def test_a2_fenced_adr_mention_clean(tmp_path):
    # The ONLY ADR mention sits inside a ``` fence within the entry body →
    # fenced content never reaches the entry text → A2 silent.
    body = (
        "# Work Log\n"
        "\n"
        "## Decisions\n"
        "\n"
        "### D-1: local decision quoting an ADR id\n"
        "- **Decision**: stays branch-local.\n"
        "```text\n"
        "see ADR-007 for background (quoted example, not a reference)\n"
        "```\n"
        "- **Disposition**: → local\n"
        "\n"
        "## Session Info\n"
        "- Owner: test\n"
    )
    log = "feat-fenced-adr-20260720.md"
    root = build_root(tmp_path, {log: body}, index=[idx(log, POST)])
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    assert "WARN:" not in r.stdout
    assert "decision disposition OK" in r.stdout
    assert "1 logs checked" in r.stdout


def test_both_signals_fire_as_two_warn_lines(tmp_path):
    # Signal A (undisposed) + Signal A2 (suspicious `→ local`) in different
    # logs → exactly TWO physical WARN lines (one aggregate per signal).
    a = "feat-undisposed-20260720.md"
    b = "feat-suspicious-20260721.md"
    root = build_root(
        tmp_path,
        {
            a: decisions_log([("forgotten entry", None)]),
            b: decisions_log([("reverses ADR-9 guidance", "-> local")]),
        },
        index=[idx(a, POST), idx(b, "2026-07-21")],
    )
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    warn_lines = [ln for ln in r.stdout.splitlines() if ln.startswith("WARN:")]
    assert len(warn_lines) == 2, f"expected exactly TWO WARN lines, got {warn_lines}"
    assert "undisposed" in warn_lines[0] and a in warn_lines[0]
    assert "`→ local`" in warn_lines[1] and "ADR-9" in warn_lines[1] and b in warn_lines[1]
    assert "decision disposition OK" not in r.stdout


# ---------------------------------------------------------------------------
# Excluded surfaces
# ---------------------------------------------------------------------------

def test_ship_history_and_gitkeep_excluded(tmp_path):
    # Both carry post-cutoff INDEX dates + unmarked Decisions; only the name
    # exclusion keeps them from being flagged.
    logs = {
        "ship-history-2026.md": decisions_log([("history noise", None)]),
        ".gitkeep.md": decisions_log([("placeholder", None)]),
    }
    root = build_root(
        tmp_path,
        logs,
        index=[idx("ship-history-2026.md", POST), idx(".gitkeep.md", POST)],
    )
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    assert "WARN:" not in r.stdout
    assert "decision disposition OK" in r.stdout


def test_work_subdir_is_not_scanned(tmp_path):
    # archive/work/ holds gitignored/compaction offloads — the non-recursive
    # root glob must never descend into it.
    log = "work/active-session-20260720.md"
    root = build_root(
        tmp_path,
        {log: decisions_log([("active undisposed", None)])},
        index=[idx("active-session-20260720.md", POST)],
    )
    r = run_tool(root)
    assert r.returncode == 0, r.stderr
    assert "WARN:" not in r.stdout
    assert "decision disposition OK" in r.stdout
    assert "0 logs checked" in r.stdout


# ---------------------------------------------------------------------------
# Real-repo run + validator wiring parity
# ---------------------------------------------------------------------------

def test_real_repo_is_clean():
    # Every legacy `## Decisions` log predates the 2026-07-16 cutoff (3 archive-
    # root logs carry the section, only 1 with real `### D-` entries; 2 more sit
    # under the excluded work/ subdir), so a run against the actual repo root
    # must be clean.
    r = run_tool(ROOT)
    assert r.returncode == 0, r.stderr
    assert "WARN:" not in r.stdout
    assert "decision disposition OK" in r.stdout
    assert f"cutoff {CUTOFF}" in r.stdout


def test_validator_wiring_parity():
    sh = VALIDATE_SH.read_text(encoding="utf-8")
    ps1 = VALIDATE_PS1.read_text(encoding="utf-8")
    label = "decision disposition (archived work logs)"
    tool = "check_decision_disposition.py"
    assert tool in sh, "validate.sh must wire check_decision_disposition.py"
    assert label in sh, "validate.sh must use the shared label"
    assert tool in ps1, "validate.ps1 must wire check_decision_disposition.py"
    assert label in ps1, "validate.ps1 must use the shared label"
