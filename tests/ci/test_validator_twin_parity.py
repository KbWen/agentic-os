r"""Structural sh/ps1 parity guards for backlog #174.

Three places where `validate.sh` and `validate.ps1` reported different things about the
same tree: the backlog row set the label-vocabulary check reads, the ruler used for
archive size, and a PASS gated on a bare glob that counted placeholder files.

**Why source-text assertions.** A behavioural tally comparison already exists --
the `count_parity_on_framework` case in `test_validator_false_positives.py` runs both
validators and asserts identical pass/warn/fail. (Its full name is spelled short here on
purpose: `test_` followed by exactly 35 characters trips TruffleHog's Lob-key detector,
which reports it as a VERIFIED secret. Confirmed by experiment, not assumed.) What cannot be built is a *Linux* one:
`validate.ps1` is the native Windows validator and `Normalize-PathString` rewrites `/`
to backslash unconditionally, so under Linux `pwsh` it mis-resolves `$root`. That module's
`requires_windows` skip reason says outright that the Linux CI job must NOT execute the
native PS validator, and names structural tests as the cross-platform guard -- which is
the style these follow.

**What is still missing, recorded rather than glossed.** The existing behavioural test
runs against the framework repo, so it could not have caught defect (c): the vacuous PASS
only appears on a tree whose `docs/specs/` holds meta files and no governed spec. Backlog
#174's prescribed "dominating substitute" was tally parity **on a fixture tree**, and that
is not built here -- these guards pin the shape of today's fix, not tomorrow's divergence.
The fixture-tree variant stays open on the row.

**Honest ceiling**: `CI Structural Tests`, `Pytest (Windows)` and `Framework Validation
(Windows)` are all non-required contexts, so no parity guard -- these or the behavioural
one -- can block a merge today. Making one blocking is a branch-protection setting, not
something this file can reach.
"""

from __future__ import annotations

import re
from pathlib import Path

TAB = chr(9)

ROOT = Path(__file__).resolve().parents[2]
VALIDATE_SH = ROOT / ".agentcortex" / "bin" / "validate.sh"
VALIDATE_PS1 = ROOT / ".agentcortex" / "bin" / "validate.ps1"

# The exact SKIP text, kept as one literal so the twins cannot drift apart silently.
NO_GOVERNED_SPECS = (
    "docs/specs/ status frontmatter -- no governed specs present "
    "(meta/_* and .gitkeep.md excluded)"
)


def _sh() -> str:
    return VALIDATE_SH.read_text(encoding="utf-8")


def _ps1() -> str:
    return VALIDATE_PS1.read_text(encoding="utf-8")


def _line_starting(text: str, prefix: str) -> str:
    """The single source line whose stripped form starts with `prefix`.

    Assertions bind to the USE site, not the whole file: each fix carries a comment that
    legitimately names the form it replaced, and a naive whole-file substring search hits
    those comments instead of the code. That false positive cost a red run here already.
    """
    hits = [ln for ln in text.splitlines() if ln.lstrip().startswith(prefix)]
    assert len(hits) == 1, f"expected exactly 1 line starting with {prefix!r}, found {len(hits)}"
    return hits[0]


def test_archive_size_uses_the_same_ruler_and_the_same_rounding() -> None:
    """Both validators must measure logical bytes and both must FLOOR.

    They disagreed twice over: `du -sk` reports disk-allocated blocks (measured ~27%
    above the logical sum on this repo -- 2326KB vs 1835KB), and even after switching to
    a byte sum, awk's int() truncates while PowerShell's [int] rounds -- half-to-even at
    that -- so identical bytes still produced different KB and could straddle the
    threshold from opposite sides.
    """
    sh_assign = _line_starting(_sh(), 'archive_kb="$(find')
    assert "du -sk" not in sh_assign, (
        "validate.sh is back on du -sk: that measures allocated blocks, not the ingestion "
        "cost this threshold proxies, and it disagrees with validate.ps1's byte sum"
    )
    assert "--apparent-size" not in sh_assign, (
        "du --apparent-size is GNU-only and would break macOS/BSD adopters"
    )
    assert "{s+=$5}" in sh_assign and "int(s/1024)" in sh_assign, (
        "validate.sh should sum file sizes and floor via awk int()"
    )

    ps_assign = _line_starting(_ps1(), "$archiveKb = [")
    assert "[math]::Floor" in ps_assign, (
        "validate.ps1 must floor like awk's int(); a bare [int] rounds half-to-even and "
        "reintroduces the KB divergence"
    )


def test_label_vocabulary_reads_the_same_anchored_active_row_set() -> None:
    """The label-drift check reads ACTIVE rows (Pending or In Progress) on both sides.

    sh previously used an alternation whose second branch carried no leading pipe-space,
    so it matched those words anywhere in a row -- including a Notes cell -- and it was
    also wider than ps1's Pending-only set. The fix keeps the wide row set (the backlog
    header defines active as Pending / In Progress, and an In-Progress row's labels are
    part of the vocabulary being watched) and anchors both alternatives.
    """
    sh_assign = _line_starting(_sh(), "distinct_labels=$(grep")
    assert "[ 	]*(Pending|In Progress)[ 	]*" in sh_assign, (
        "validate.sh label check must match a whole status cell with tolerant padding; a "
        "rigid single-space anchor keeps only the rows whose status is the widest value on "
        "a column-aligned backlog, so the count goes silently PARTIAL and still reports PASS"
    )
    assert r"| Pending\|In Progress" not in sh_assign, (
        "the unanchored alternation is back: its second branch has no leading pipe-space, "
        "so it matches prose cells"
    )

    ps_assign = _line_starting(_ps1(), "$activeRows =")
    assert "[ 	]*(Pending|In Progress)[ 	]*" in ps_assign, (
        "validate.ps1 must build the same tolerant whole-cell active row set"
    )
    # The padding class is a literal space and a literal TAB on both sides, deliberately.
    # POSIX ERE has no tab escape, so spelling it backslash-t inside grep -E would match a
    # backslash or the letter t instead; and .NET's shorthand whitespace class also matches
    # U+0085 / U+00A0 / U+3000, which POSIX [[:space:]] does not under LC_ALL=C -- an
    # NBSP-padded backlog would then be active for one twin and not the other. Pinned here
    # because a literal tab is invisible in review and trivially stripped by a formatter.
    for name, line in (("validate.sh", sh_assign), ("validate.ps1", ps_assign)):
        pattern = re.search(r"\(Pending\|In Progress\)", line)
        assert pattern, f"{name}: status alternation not found"
        # Scope to the selector itself: the sh line's later pipeline legitimately uses
        # [[:space:]] for trimming, which is unrelated to row selection.
        selector = line[max(0, pattern.start() - 12):pattern.end() + 12]
        assert f"[ {TAB}]*" in selector, (
            f"{name}: the padding class must stay ASCII space+tab -- POSIX and .NET "
            "whitespace shorthands disagree on Unicode blanks and would reintroduce a "
            "twin divergence"
        )
        assert "[[:space:]]" not in selector and chr(92) + "s" not in selector, (
            f"{name}: selector uses a Unicode-sensitive whitespace class"
        )
    assert "-cmatch" in ps_assign, (
        "must be -cmatch: PowerShell's -match is case-insensitive while grep -E is not, "
        "so a `| pending |` row would enter ps1's set and not sh's — a twin divergence "
        "introduced by the change that closes twin divergences"
    )


def test_label_check_survives_a_backlog_with_no_active_rows() -> None:
    """The label selector must not abort the whole validator when it matches nothing.

    `validate.sh` runs under `set -euo pipefail`, and this assignment's pipeline ends in
    filters (`grep -v`) that legitimately empty out. On a backlog whose rows are all
    Shipped -- an adopter who has just closed their last item -- the pipeline returns 1,
    the assignment fails, and errexit kills the run: no label line, no `Summary:`, every
    later check silently never executed, exit 1 with nothing explaining why.

    Measured pre-existing: the same abort reproduces on the base commit's unanchored
    pattern, so this is a latent bug rather than one the anchoring introduced -- but the
    anchoring touches this exact line, and `validate.ps1` does NOT abort in the same
    state (an empty `$activeRows` just yields 0), so leaving it would be a twin
    divergence in exit code, which is the worst kind.

    Its four siblings in the same block are already protected -- `total_pending` and
    `p0_pending` by `|| echo 0`, `kind_variety` and `kind_assigned` by count gates that
    only run when rows exist. This one runs unconditionally.
    """
    line = _line_starting(_sh(), "distinct_labels=$(grep")
    assert "|| true" in line or "|| echo 0" in line, (
        "the label-selector assignment is unguarded: under set -euo pipefail a backlog "
        "with no active rows aborts the entire validator mid-run"
    )


def test_label_check_row_set_is_separate_from_the_pending_only_siblings() -> None:
    """Widening the label check must NOT widen L-1/L-3/L-3b.

    In ps1 those four checks originally shared one `$pendingRows`. Reusing it for the
    wider active set would silently change three other checks and break parity in the
    opposite direction, so the label check gets its own row set.
    """
    ps1 = _ps1()
    assert "$distinctLabels = @($activeRows" in ps1, (
        "the label check must read $activeRows, not $pendingRows"
    )
    assert "$totalPending = $pendingRows.Count" in ps1, (
        "L-1 must still read the Pending-only row set"
    )
    pending_only = _line_starting(ps1, "$pendingRows =")
    assert "In Progress" not in pending_only, (
        "$pendingRows was widened; L-1/L-3/L-3b must stay Pending-only on both sides"
    )


def test_no_governed_specs_emits_a_skip_on_both_sides() -> None:
    """A tree with no governed specs must SKIP, identically, not fall silent.

    The old PASS was gated on a bare `*.md` glob that counted the `_`-prefixed meta files
    the scanning loop had just skipped, so a downstream that had run /spec-intake but
    written no spec was told its spec frontmatter was valid over zero specs. (Not
    `.gitkeep.md`: bash `*.md` never matches a dotfile without dotglob. An earlier draft
    of this note said otherwise and was wrong.) Simply deleting that PASS would have
    traded one defect for the one ratchet justification #7 names (backlog #149): a check
    that emits NOTHING while the summary still prints "integrity check passed".
    """
    assert _sh().count(NO_GOVERNED_SPECS) == 1, "validate.sh missing the governed-spec SKIP"
    assert _ps1().count(NO_GOVERNED_SPECS) == 1, (
        "validate.ps1 missing the governed-spec SKIP (parity)"
    )


def test_spec_frontmatter_pass_is_not_gated_on_a_bare_glob() -> None:
    """The PASS must be gated on the loop's filtered counter, never on a re-glob.

    The re-glob is what made the PASS vacuous: it counted every `*.md` in docs/specs/,
    including the placeholders the scanning loop had just skipped.
    """
    sh = _sh()
    assert 'for f in "$ROOT/docs/specs"/*.md; do [[ -f "$f" ]] && spec_file_count' not in sh, (
        "validate.sh re-globs docs/specs to gate the frontmatter PASS (the vacuous shape)"
    )
    assert "spec_file_count=$((spec_file_count + 1))" in sh, (
        "spec_file_count must be incremented inside the scanning loop, past both skips"
    )
