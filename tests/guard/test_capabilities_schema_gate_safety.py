"""Schema gate-safety validator tests - ADR-007 AC-D6.

Gate-relaxation must be UNREPRESENTABLE: a malicious / over-cap
downstream-capabilities.yaml is REJECTED (exit 1, naming the offending field), NOT
silently clamped. A gate-safe file -> exit 0; absent / empty -> exit 0 (inert).
The reject-vs-clamp parametrization IS the mutation guard: if anyone weakens the
validator to lower a value instead of rejecting, these exit-1 assertions fail.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / ".agentcortex" / "tools" / "validate_downstream_capabilities.py"


def _check(tmp_path, body):
    f = tmp_path / "downstream-capabilities.yaml"
    f.write_text(textwrap.dedent(body), encoding="utf-8")
    return subprocess.run([sys.executable, str(VALIDATOR), str(f)],
                          capture_output=True, encoding="utf-8", errors="replace")


_SAFE = """\
version: 1
skills:
  - id: custom-terraform-safety
    load_policy: on-match
    phase_scope: [implement, review]
subagent_policy: read-only
trackers:
  - id: custom-jira
    skill: custom-jira-sync
"""


def test_gate_safe_file_passes(tmp_path):
    r = _check(tmp_path, _SAFE)
    assert r.returncode == 0, f"gate-safe file must pass: {r.stderr!r}"


def test_default_load_policy_is_gate_safe(tmp_path):
    r = _check(tmp_path, "skills:\n  - id: custom-default\n")
    assert r.returncode == 0, f"omitted load_policy should default to on-match: {r.stderr!r}"


def test_absent_file_is_safe(tmp_path):
    r = subprocess.run([sys.executable, str(VALIDATOR), str(tmp_path / "nope.yaml")],
                       capture_output=True, encoding="utf-8", errors="replace")
    assert r.returncode == 0


def test_empty_file_is_safe(tmp_path):
    assert _check(tmp_path, "").returncode == 0


@pytest.mark.parametrize("body,needle", [
    ("skills:\n  - id: red-team-adversarial\n    load_policy: on-match\n", "custom-"),
    ("skills:\n  - id: custom-x\n    load_policy: phase-entry\n", "on-match"),
    ("skills:\n  - id: custom-x\n    load_policy: on-failure\n", "on-match"),
    ("skills:\n  - id: custom-x\n    load_policy: always\n", "ceiling"),
    ("skills:\n  - id: custom-x\n    block_if_missed: true\n", "block_if_missed"),
    ("skills:\n  - id: custom-x\n    gate: ship\n", "gate"),
    ("subagent_policy: anything-goes\n", "subagent_policy"),
    ("trackers:\n  - id: custom-j\n    blocking: true\n", "blocking"),
    ("trigger_priority: hard\n", "trigger_priority"),
    ("skip_confirmation: true\n", "unknown top-level"),
    ("ship_without_review: true\n", "unknown top-level"),
    ("skills:\n  - id: custom-x\n    autonomy: full\n", "unknown key"),
    # ADR-009 knowledge_sources: advisory-ONLY; gate-relaxation unrepresentable (rejected, not clamped)
    ("knowledge_sources:\n  - path: ../kb\n    role: authority\n", "advisory"),
    ("knowledge_sources:\n  - path: ../kb\n    role: [advisory]\n", "advisory"),  # unhashable role -> clean reject, not traceback
    ("knowledge_sources:\n  - path: ../kb\n    required: true\n", "unknown key"),
    ("knowledge_sources:\n  - id: k\n", "path"),
    ("knowledge_sources:\n  - path: ../kb\n    manifest_trusted: yes\n", "manifest_trusted"),
    ("knowledge_sources:\n  - path: ../kb\n    gate: ship\n", "gate"),
])
def test_unsafe_file_is_rejected_not_clamped(tmp_path, body, needle):
    r = _check(tmp_path, body)
    assert r.returncode == 1, f"must REJECT (not clamp) {body!r} -> rc={r.returncode}, err={r.stderr!r}"
    assert needle in r.stderr, f"reason must name {needle!r}: {r.stderr!r}"


_KS_SAFE = """\
version: 1
skills:
  - id: custom-x
    load_policy: on-match
knowledge_sources:
  - id: kb-main
    path: ../knowledge-base
    entrypoint: outputs/manifest.json
    role: advisory
    manifest_trusted: false
"""


def test_knowledge_sources_gate_safe(tmp_path):
    # ADR-009: a valid present-only knowledge_sources block (advisory, manifest_trusted
    # false) is gate-safe and coexists with skills/trackers (non-regression).
    r = _check(tmp_path, _KS_SAFE)
    assert r.returncode == 0, f"a valid knowledge_sources block must pass: {r.stderr!r}"


# --- Strict capabilities grammar (parse_strict) -------------------------------
# The validator parses with a dedicated STRICT allowlist mini-parser, NOT the shared
# lenient _yaml_loader and NOT PyYAML -- so behaviour is identical with or without
# PyYAML installed (no shadow harness needed). The security argument is an ALLOWLIST of
# syntax: a forbidden key in plain/simple-quoted form is RESOLVED and caught by the
# denylist (rc 1); a forbidden key hidden behind ANY exotic syntax the grammar refuses
# to interpret is a hard syntax error (rc 2, fail-closed) and can never reach a gate-safe
# verdict. Three review rounds found flow-map / quoted-key / flow-seq-k:v / mismatched-
# quote / double-quoted-escape / silent-drop-misindent fail-opens; the strict grammar
# closes all of them by construction.

_RICH_SAFE = """\
version: 1
skills:
  - id: custom-tf
    load_policy: on-match
    phase_scope: [implement, review]
    detect_by:
      classification: [feature]
    description: "validates, formats: and lints"
subagent_policy: governed
trackers:
  - id: custom-jira
    skill: custom-jira-sync
"""


def test_strict_parser_accepts_rich_safe_file(tmp_path):
    # Nested detect_by mapping, a flow-sequence, and a quoted value CONTAINING ':' and
    # ',' must all parse and be gate-safe (no false positive).
    r = _check(tmp_path, _RICH_SAFE)
    assert r.returncode == 0, f"rich safe file must pass: {r.stderr!r}"


@pytest.mark.parametrize("body,needle", [
    ("trackers:\n  - id: custom-j\n    blocking: true\n", "blocking"),                  # plain block
    ("version: 1\ntrackers:\n  - 'blocking': true\n", "blocking"),                      # simple single-quote key
    ('version: 1\ntrackers:\n  - "gate": ship\n', "gate"),                              # simple double-quote key
    ("skills:\n  - id: custom-x\n    detect_by:\n      ship_edge: x\n", "ship_edge"),   # nested key
    ("trigger_priority: hard\n", "trigger_priority"),                                   # top-level
])
def test_forbidden_key_in_clean_syntax_rejected(tmp_path, body, needle):
    # Cleanly-parseable forbidden key -> RESOLVED -> denylist -> rc 1 naming the key.
    r = _check(tmp_path, body)
    assert r.returncode == 1, f"forbidden key must reject: rc={r.returncode}, err={r.stderr!r}"
    assert needle in r.stderr, f"reason must name {needle!r}: {r.stderr!r}"


@pytest.mark.parametrize("body", [
    "version: 1\ntrackers:\n  - {id: x, blocking: true}\n",                             # flow mapping
    "version: 1\ntrackers:\n  - {worklog_writers: all}\n",                              # flow mapping
    'version: 1\ntrackers:\n  - "\\x62\\x6c\\x6f\\x63\\x6b\\x69\\x6e\\x67": true\n',     # \\x escape -> blocking
    'version: 1\ntrackers:\n  - "\\u0067ate": ship\n',                                  # \\u escape -> gate
    "version: 1\ntrackers:\n  - phase_scope: [blocking: true]\n",                       # flow-seq k:v
    "version: 1\ntrackers:\n  - 'blocking: true\n",                                     # unterminated quote
    "version: 1\ntrackers:\n  - id: custom-x\n     blocking: true\n",                   # silent-drop misindent (5sp)
    "version: 1\ntrackers:\n  - id: &a custom-x\n",                                     # anchor
    "version: 1\ntrackers:\n  - !!str gate: ship\n",                                    # tag
    "version: 1\ntrackers:\n  - <<: x\n",                                               # merge key
    "version: 1\ntrackers:\n  - ? blocking\n    : true\n",                              # explicit key
    "version: 1\nskills:\n  - id: custom-x\n    description: >\n      blocking: true\n", # block scalar
    "version: 1\ntrackers:\n\t- blocking: true\n",                                      # tab indentation
])
def test_unsupported_syntax_fails_closed(tmp_path, body):
    # Any syntax outside the minimal grammar -> hard syntax error (rc 2). A forbidden key
    # can never reach a gate-safe verdict by hiding behind exotic syntax.
    r = _check(tmp_path, body)
    assert r.returncode == 2, (
        f"unsupported syntax must fail-closed (rc 2): rc={r.returncode}, "
        f"out={r.stdout!r}, err={r.stderr!r}")


@pytest.mark.parametrize("body", [
    'skills:\n  - id: custom-x\n    description: "first, gate: second"\n',
    'skills:\n  - id: custom-x\n    description: "a hard: limit, gates: ok"\n',
    'trackers:\n  - id: custom-x\n    note: "blocking: only in prose"\n',
])
def test_forbidden_token_inside_value_is_not_false_positive(tmp_path, body):
    # A forbidden WORD inside a quoted VALUE (not a key) is gate-safe. The old raw-text
    # scan false-rejected these; the strict parser resolves them correctly -> no FP.
    r = _check(tmp_path, body)
    assert r.returncode == 0, f"forbidden token in a value must NOT false-reject: {r.stderr!r}"
