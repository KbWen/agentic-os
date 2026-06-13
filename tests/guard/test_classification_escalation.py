"""Contract-regression test: classification & escalation rules.

Locks the governance contract in `.agent/rules/engineering_guardrails.md §10`
(Escalation Rules / Gate Standards / fast-path exclusions) and its cross-file
agreement with `AGENTS.md`, so a careless edit cannot silently drop an
escalation trigger, weaken a governance-file exclusion, or let the two files
drift apart. Part of #16 (test coverage for critical governance paths).

Like `test_state_machine_contract.py`, this verifies the *contract text is
present and self-consistent*, NOT that a running agent obeys it. Assertions
anchor on stable structural markers (section headings, file-path tokens, tier
names), not prose sentences.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARDRAILS = ROOT / ".agent" / "rules" / "engineering_guardrails.md"
AGENTS = ROOT / "AGENTS.md"
ROUTING = ROOT / ".agent" / "workflows" / "routing.md"
BOOTSTRAP = ROOT / ".agent" / "workflows" / "bootstrap.md"
STATE_MACHINE = ROOT / ".agent" / "rules" / "state_machine.md"

# Governance files that MUST always escalate above tiny-fix. These appear in
# BOTH engineering_guardrails §10.3 and AGENTS.md's tiny-fix exclusions — the
# drift guard below asserts neither list silently loses one.
GOVERNANCE_EXCLUSION_TOKENS = [
    "AGENTS.md",
    ".agent/rules/",
    ".agent/config.yaml",
    ".agentcortex/templates/",
    ".agentcortex/bin/validate.",
    "specs/",
    "architecture/",
    "CLAUDE.md",
    "GEMINI.md",
]

CLASSIFICATION_TIERS = ["tiny-fix", "quick-win", "feature", "architecture-change", "hotfix"]


def _subsection(text: str, heading_prefix: str) -> str:
    """Body of a `### <heading_prefix>...` section up to the next `### ` / `## `."""
    m = re.search(
        rf"^###\s+{re.escape(heading_prefix)}.*?$(.*?)(?=^###\s|^##\s|\Z)",
        text, flags=re.MULTILINE | re.DOTALL,
    )
    assert m, f"engineering_guardrails.md is missing the '### {heading_prefix}' section"
    return m.group(1)


def _heading_section(text: str, heading_prefix: str) -> str:
    """Body of a `##` or `###` section up to the next heading at the same or higher level."""
    m = re.search(
        rf"^(##+)\s+{re.escape(heading_prefix)}.*?$(.*?)(?=^\1\s|^##\s|\Z)",
        text, flags=re.MULTILINE | re.DOTALL,
    )
    assert m, f"missing heading section: {heading_prefix}"
    return m.group(2)


class ClassificationEscalationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = GUARDRAILS.read_text(encoding="utf-8")
        cls.agents = AGENTS.read_text(encoding="utf-8")
        cls.routing = ROUTING.read_text(encoding="utf-8")
        cls.bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        cls.state_machine = STATE_MACHINE.read_text(encoding="utf-8")
        cls.escalation = _subsection(cls.text, "10.1")
        cls.gate_standards = _subsection(cls.text, "10.2")
        cls.tiny_fix = _subsection(cls.text, "10.3")
        cls.quick_win = _subsection(cls.text, "10.4")

    # --- §10.1 escalation table -----------------------------------------
    def test_escalation_table_has_canonical_triggers(self) -> None:
        """Each trigger→minimum-classification row MUST be present."""
        required_rows = [
            (r"<\s*3 files", "tiny-fix"),
            (r"1-2 modules", "quick-win"),
            (r"exports.*public API.*signature|signature", "feature"),
            (r">1 module|import graph", "feature"),
            (r"new directories", "feature"),
            (r"default configs", "feature"),
            (r"data-flow|system boundaries", "architecture-change"),
        ]
        for trigger_re, tier in required_rows:
            row = next(
                (ln for ln in self.escalation.splitlines()
                 if re.search(trigger_re, ln) and f"`{tier}`" in ln),
                None,
            )
            self.assertIsNotNone(
                row, f"§10.1 missing escalation row: /{trigger_re}/ → {tier}",
            )

    def test_escalation_minimum_classifications_are_known_tiers(self) -> None:
        """Every value in the table's minimum-classification (last) column MUST be a
        known tier — catches a typo'd or invented tier name. Extracts the backtick
        token immediately before each row's closing pipe (NOT every backtick token,
        since trigger cells also contain backticked words like `exports`)."""
        cited = re.findall(r"`([a-z][a-z-]*)`\s*\|\s*$", self.escalation, re.MULTILINE)
        self.assertTrue(cited, "no minimum-classification tiers parsed from §10.1 table")
        bogus = sorted(set(cited) - set(CLASSIFICATION_TIERS))
        self.assertFalse(bogus, f"unknown tier in §10.1 minimum-classification column: {bogus}")

    # --- §10.2 gate/evidence standards ----------------------------------
    def test_gate_standards_cover_every_tier(self) -> None:
        for tier in CLASSIFICATION_TIERS:
            self.assertIn(tier, self.gate_standards,
                          f"§10.2 Gate Standards table missing tier '{tier}'")

    def test_heavy_tiers_require_review_and_test_in_gate_order(self) -> None:
        """feature / architecture-change phase order MUST include review + test."""
        for tier in ("feature", "architecture-change"):
            row = next((ln for ln in self.gate_standards.splitlines()
                        if f"**{tier}**" in ln), None)
            self.assertIsNotNone(row, f"§10.2 missing gate row for {tier}")
            self.assertIn("review", row, f"{tier} gate order must include review")
            self.assertIn("test", row, f"{tier} gate order must include test")

    # --- §10.3 governance-file exclusions -------------------------------
    def test_governance_file_exclusions_listed(self) -> None:
        """Every governance-file token MUST appear in §10.3's exclusion list."""
        for token in GOVERNANCE_EXCLUSION_TOKENS:
            self.assertIn(token, self.tiny_fix,
                          f"§10.3 tiny-fix exclusions missing governance token '{token}'")

    # --- §10.4 escalation triggers --------------------------------------
    def test_security_escalation_rule_present(self) -> None:
        """auth/security logic in a quick-win MUST escalate to >= hotfix."""
        self.assertIn("Security Escalation", self.quick_win)
        self.assertIn("hotfix", self.quick_win)

    def test_root_cause_escalation_rule_present(self) -> None:
        """regression-class quick-win MUST record a root cause."""
        self.assertIn("Root-Cause Escalation", self.quick_win)
        self.assertRegex(self.quick_win, r"Root Cause:")

    def test_supply_chain_provenance_escalation_rule_present(self) -> None:
        """installer/updater/source-provenance changes MUST not stay quick-win."""
        required = [
            "Supply-Chain / Provenance Escalation",
            "hotfix",
            "source_repo",
            "--source",
            "cache origin",
            "manifest integrity",
            "remote fetch/download/clone/pull/checkout",
            "trust boundary",
            "docs that merely mention deploy commands do not trigger",
        ]
        for token in required:
            self.assertIn(
                token,
                self.quick_win,
                f"§10.4 supply-chain/provenance escalation missing token: {token!r}",
            )

        escalation_rules = _heading_section(self.state_machine, "Classification Escalation Rules")
        self.assertRegex(
            escalation_rules,
            r"Supply-Chain / Provenance Escalation.*source_repo.*escalate to `hotfix` minimum.*REVIEWED \+ TESTED",
            "state_machine.md must require supply-chain/provenance quick-wins to escalate to hotfix review/test gates",
        )
        for token in (
            "implementation logic",
            "source_repo",
            "--source",
            "cache origin",
            "manifest integrity",
            "remote fetch/download/clone/pull/checkout",
            "executing framework code from a resolved source",
            "Docs-only exempt",
        ):
            self.assertIn(
                token,
                escalation_rules,
                f"state_machine.md escalation rules missing token: {token!r}",
            )

        for token in (
            "implementation logic",
            "source_repo",
            "--source",
            "cache origin",
            "manifest integrity",
            "remote fetch/download/clone/pull/checkout",
            "executing framework code from a resolved source",
            "minimum `hotfix`",
            "docs-only exempt",
        ):
            self.assertIn(
                token,
                self.bootstrap,
                f"bootstrap.md pre-classification fast check missing token: {token!r}",
            )

        table_lines = [
            line for line in self.bootstrap.splitlines()
            if line.startswith("| modifies ") or line.startswith("| IF the task")
        ]
        self.assertGreaterEqual(len(table_lines), 2, "bootstrap fast-check table must have data rows")
        first_data_row = table_lines[1]
        self.assertIn(
            "source selection/provenance",
            first_data_row,
            "bootstrap first-match table must make supply-chain/provenance the first data row",
        )
        supply_index = next(
            i for i, line in enumerate(table_lines)
            if "source selection/provenance" in line and "minimum `hotfix`" in line
        )
        first_quickwin_index = next(
            i for i, line in enumerate(table_lines)
            if "minimum `quick-win`" in line
        )
        self.assertLess(
            supply_index,
            first_quickwin_index,
            "bootstrap.md first-match table must check supply-chain/provenance hotfix before quick-win rows",
        )

    # --- cross-file drift guard (the core #16 protection) ---------------
    def test_agents_md_tinyfix_exclusions_match_guardrails(self) -> None:
        """AGENTS.md's tiny-fix exclusion CLAUSE MUST list the same governance files
        as §10.3 — a drift between the two files is exactly the silent regression
        #16 exists to catch. Scope the match to the exclusion clause itself, NOT the
        whole file: most tokens also appear elsewhere in AGENTS.md, so a whole-file
        match would silently pass even after a token is dropped from the list."""
        m = re.search(r"ADDITIONAL TINY-FIX EXCLUSIONS.*?§10\.3", self.agents, re.DOTALL)
        self.assertIsNotNone(
            m, "AGENTS.md is missing the 'ADDITIONAL TINY-FIX EXCLUSIONS … §10.3' clause",
        )
        clause = m.group(0)
        for token in GOVERNANCE_EXCLUSION_TOKENS:
            self.assertIn(
                token, clause,
                f"AGENTS.md tiny-fix exclusion clause drifted from §10.3: missing '{token}'",
            )

    def test_routing_escalation_rule_matches_guardrails(self) -> None:
        """routing.md §4's tiny-fix↔quick-win escalation rule MUST enumerate the
        same governance files as §10.3 — site 3 of the 4-way mirror. Scope to the
        rule clause, not the whole file, so a dropped token cannot hide elsewhere."""
        m = re.search(
            r"tiny-fix vs quick-win escalation.*?always escalates to quick-win minimum",
            self.routing, re.DOTALL,
        )
        self.assertIsNotNone(
            m, "routing.md is missing the 'tiny-fix vs quick-win escalation … always escalates' rule",
        )
        clause = m.group(0)
        for token in GOVERNANCE_EXCLUSION_TOKENS:
            self.assertIn(
                token, clause,
                f"routing.md escalation rule drifted from §10.3: missing '{token}'",
            )

    def test_bootstrap_fastcheck_table_matches_guardrails(self) -> None:
        """bootstrap.md §0 fast-check decision table MUST enumerate the same
        governance files as §10.3 — site 4 of the 4-way mirror. Scope to the table
        block (tokens are spread across multiple rows, so match the whole table)."""
        m = re.search(r"\| IF the task.*?(?=\n\n|\n##)", self.bootstrap, re.DOTALL)
        self.assertIsNotNone(
            m, "bootstrap.md is missing the §0 '| IF the task...' fast-check decision table",
        )
        table = m.group(0)
        for token in GOVERNANCE_EXCLUSION_TOKENS:
            self.assertIn(
                token, table,
                f"bootstrap.md fast-check table drifted from §10.3: missing '{token}'",
            )


if __name__ == "__main__":
    unittest.main()
