"""Contract-regression test: `.agent/rules/state_machine.md` transition graph.

Locks down the canonical phase-transition graph so a careless edit to
`state_machine.md` (or a wording drift between it and `AGENTS.md`) cannot
silently delete a legal edge, introduce an unknown state, or contradict the
Spec Gate. Part of #16 (test coverage for critical governance paths).

This verifies the *contract text is present and self-consistent*, NOT that a
running agent obeys it — same limitation (and same markdown-parsing style) as
`.agentcortex/tests/test_lifecycle_contract.py`. Assertions anchor on stable
structural markers (state names, section headings), not prose sentences.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SM_PATH = ROOT / ".agent" / "rules" / "state_machine.md"
AGENTS_PATH = ROOT / "AGENTS.md"

# Canonical state order from `## Defined States` (line 5 of state_machine.md).
EXPECTED_ORDER = [
    "INIT", "BOOTSTRAPPED", "CLASSIFIED", "SPECIFIED", "PLANNED",
    "IMPLEMENTABLE", "IMPLEMENTING", "REVIEWED", "TESTED", "HANDEDOFF", "SHIPPED",
]
TERMINAL_STATE = "SHIPPED"

# Edge form: `FROM` --(label)--> `TO`
EDGE_RE = re.compile(r"`([A-Z_]+)`\s*--\(.*?\)-->\s*`([A-Z_]+)`")
# Backtick-wrapped state token (used for the Defined-States order line).
STATE_TOKEN_RE = re.compile(r"`([A-Z_]+)`")


def _section(text: str, heading: str) -> str:
    """Return the body of a `## <heading>` section up to the next `## `."""
    m = re.search(
        rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)",
        text, flags=re.MULTILINE | re.DOTALL,
    )
    assert m, f"state_machine.md is missing the '## {heading}' section"
    return m.group(1)


class StateMachineContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SM_PATH.read_text(encoding="utf-8")
        cls.agents = AGENTS_PATH.read_text(encoding="utf-8")
        cls.transitions_body = _section(cls.text, "Allowed Transitions")
        cls.edges = set(EDGE_RE.findall(cls.transitions_body))

    # --- canonical order -------------------------------------------------
    def test_defined_states_order_is_canonical(self) -> None:
        """The `## Defined States` order line MUST match the canonical sequence."""
        order_line = next(
            (ln for ln in self.text.splitlines() if "`INIT`" in ln and "`SHIPPED`" in ln),
            None,
        )
        self.assertIsNotNone(order_line, "could not find the Defined States order line")
        states = STATE_TOKEN_RE.findall(order_line)
        self.assertEqual(
            states, EXPECTED_ORDER,
            f"Defined-States order drifted: {states} != {EXPECTED_ORDER}",
        )

    # --- graph integrity -------------------------------------------------
    def test_some_edges_were_parsed(self) -> None:
        """Guard against a regex/format drift that would silently parse zero edges."""
        self.assertGreaterEqual(len(self.edges), 10, "parsed too few transition edges")

    def test_all_edge_states_are_known(self) -> None:
        """Every state referenced in a transition MUST be a defined state (catches typos)."""
        known = set(EXPECTED_ORDER)
        for src, dst in sorted(self.edges):
            self.assertIn(src, known, f"unknown source state '{src}' in a transition")
            self.assertIn(dst, known, f"unknown target state '{dst}' in a transition")

    def test_every_non_terminal_state_has_an_outgoing_edge(self) -> None:
        """No defined state (except the terminal SHIPPED) may be a dead end."""
        sources = {src for src, _ in self.edges}
        for state in EXPECTED_ORDER:
            if state == TERMINAL_STATE:
                continue
            self.assertIn(state, sources, f"state '{state}' has no outgoing transition")

    def test_terminal_state_has_no_outgoing_edge(self) -> None:
        """SHIPPED is terminal — it MUST NOT have an outgoing transition."""
        sources = {src for src, _ in self.edges}
        self.assertNotIn(TERMINAL_STATE, sources, "SHIPPED must be terminal")

    # --- required forward edges -----------------------------------------
    def test_required_forward_edges_present(self) -> None:
        required = {
            ("BOOTSTRAPPED", "CLASSIFIED"),
            ("CLASSIFIED", "SPECIFIED"),
            ("SPECIFIED", "PLANNED"),
            ("CLASSIFIED", "PLANNED"),       # fast-path tiny-fix/quick-win/hotfix
            ("PLANNED", "IMPLEMENTABLE"),
            ("IMPLEMENTABLE", "IMPLEMENTING"),
            ("IMPLEMENTING", "REVIEWED"),
            ("REVIEWED", "TESTED"),
            ("TESTED", "HANDEDOFF"),
            ("HANDEDOFF", "SHIPPED"),
            ("TESTED", "SHIPPED"),           # fast-path quick-win/hotfix
        }
        missing = required - self.edges
        self.assertFalse(missing, f"missing required forward edges: {sorted(missing)}")

    # --- required reverse edges (gate progression depends on these) ------
    def test_required_reverse_edges_present(self) -> None:
        required = {
            ("REVIEWED", "IMPLEMENTING"),    # NOT READY review verdict
            ("TESTED", "IMPLEMENTING"),      # tests stay red
            ("HANDEDOFF", "IMPLEMENTING"),   # ship entry-condition fail
            ("IMPLEMENTING", "CLASSIFIED"),  # mid-execution scope creep
            ("IMPLEMENTABLE", "CLASSIFIED"), # pre-implementation scope creep
        }
        missing = required - self.edges
        self.assertFalse(missing, f"missing required reverse edges: {sorted(missing)}")

    def test_quick_win_fast_path_edge_present(self) -> None:
        """quick-win may ship straight from IMPLEMENTING."""
        self.assertIn(("IMPLEMENTING", "SHIPPED"), self.edges)

    # --- spec gate consistency ------------------------------------------
    def test_classified_to_planned_is_restricted_to_fast_path_tiers(self) -> None:
        """The direct CLASSIFIED->PLANNED edge MUST be annotated ONLY for fast-path tiers."""
        line = next(
            (ln for ln in self.transitions_body.splitlines()
             if "`CLASSIFIED`" in ln and "-->" in ln and "`PLANNED`" in ln and "ONLY" in ln),
            None,
        )
        self.assertIsNotNone(line, "CLASSIFIED->PLANNED fast-path annotation not found")
        for tier in ("tiny-fix", "quick-win", "hotfix"):
            self.assertIn(tier, line, f"fast-path edge should list '{tier}'")

    def test_spec_gate_requires_specified_for_heavy_tiers(self) -> None:
        """feature / architecture-change MUST reach SPECIFIED before planning."""
        gate = _section(self.text, "Spec Gate (Hard)")
        self.assertIn("feature", gate)
        self.assertIn("architecture-change", gate)
        self.assertIn("SPECIFIED", gate)

    # --- cross-file consistency with AGENTS.md ---------------------------
    def test_agents_md_ship_paths_match_state_machine(self) -> None:
        """AGENTS.md vNext ship-path claims MUST be backed by edges in state_machine.md."""
        # AGENTS.md: feature/arch-change -> TESTED->HANDEDOFF->SHIPPED; quick-win/hotfix -> TESTED->SHIPPED
        self.assertIn("TESTED→HANDEDOFF→SHIPPED", self.agents)
        self.assertIn("TESTED→SHIPPED", self.agents)
        self.assertIn(("TESTED", "HANDEDOFF"), self.edges)
        self.assertIn(("HANDEDOFF", "SHIPPED"), self.edges)
        self.assertIn(("TESTED", "SHIPPED"), self.edges)


if __name__ == "__main__":
    unittest.main()
