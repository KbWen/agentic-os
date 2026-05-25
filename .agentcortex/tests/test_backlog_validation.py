from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from test_helpers import sanitize_deployed_ssot
from test_ssot_completeness import (
    has_bash_launcher,
    init_git_repo,
    run_deploy,
    run_validate,
)

VALID_BACKLOG = """---
title: Product Backlog
created: 2026-04-12
status: living
---

# Product Backlog

## Feature Inventory

| # | Feature | Kind | Labels | Priority | Spec File | Tier | Status | Dependencies |
|---|---|---|---|---|---|---|---|---|
| 1 | Sample feature one | framework | core | P1 | — | feature | Pending | — |
| 2 | Sample feature two | — | — | — | — | quick-win | Shipped | — |

## Status Key

- Pending: not yet started
- Shipped: feature shipped
"""

# Same as VALID_BACKLOG but row 2 uses a Status outside the allowed enum.
INVALID_ENUM_BACKLOG = VALID_BACKLOG.replace(
    "| 2 | Sample feature two | — | — | — | — | quick-win | Shipped | — |",
    "| 2 | Sample feature two | — | — | — | — | quick-win | Done | — |",
)

# Same as VALID_BACKLOG but the frontmatter is missing the `created` field.
MISSING_FRONTMATTER_BACKLOG = VALID_BACKLOG.replace("created: 2026-04-12\n", "")


def _write_backlog(target: Path, text: str) -> None:
    (target / "docs/specs").mkdir(parents=True, exist_ok=True)
    (target / "docs/specs/_product-backlog.md").write_text(text, encoding="utf-8")


def _point_ssot_to_backlog(target: Path) -> None:
    ssot = target / ".agentcortex" / "context" / "current_state.md"
    content = ssot.read_text(encoding="utf-8")
    content = re.sub(
        r"(\*\*Active Backlog\*\*:)\s*none",
        r"\1 `docs/specs/_product-backlog.md`",
        content,
    )
    ssot.write_text(content, encoding="utf-8")


@unittest.skipUnless(has_bash_launcher(), "shell launcher unavailable for validate smoke")
class BacklogValidationTests(unittest.TestCase):
    def test_invalid_status_enum_fails(self) -> None:
        """A Feature Inventory row with an unknown Status → validator must fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            deploy = run_deploy(target)
            self.assertEqual(deploy.returncode, 0, deploy.stderr or deploy.stdout)
            sanitize_deployed_ssot(target)
            init_git_repo(target)

            _write_backlog(target, INVALID_ENUM_BACKLOG)

            validate = run_validate(target)
            self.assertNotEqual(validate.returncode, 0, validate.stdout)
            self.assertIn("backlog Status enum", validate.stdout)
            self.assertIn("FAIL", validate.stdout)

    def test_missing_frontmatter_field_fails(self) -> None:
        """A backlog whose frontmatter omits a required field → validator must fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            deploy = run_deploy(target)
            self.assertEqual(deploy.returncode, 0, deploy.stderr or deploy.stdout)
            sanitize_deployed_ssot(target)
            init_git_repo(target)

            _write_backlog(target, MISSING_FRONTMATTER_BACKLOG)

            validate = run_validate(target)
            self.assertNotEqual(validate.returncode, 0, validate.stdout)
            self.assertIn("backlog frontmatter", validate.stdout)
            self.assertIn("created", validate.stdout)

    def test_valid_backlog_passes(self) -> None:
        """A well-formed backlog referenced by SSoT → new structure checks must pass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir)
            deploy = run_deploy(target)
            self.assertEqual(deploy.returncode, 0, deploy.stderr or deploy.stdout)
            sanitize_deployed_ssot(target)

            _write_backlog(target, VALID_BACKLOG)
            _point_ssot_to_backlog(target)
            init_git_repo(target)

            validate = run_validate(target)
            self.assertEqual(validate.returncode, 0, validate.stdout)
            self.assertIn("backlog Status enum: all Feature Inventory rows use valid Status values", validate.stdout)
            self.assertIn("backlog frontmatter: required fields", validate.stdout)


if __name__ == "__main__":
    unittest.main()
