#!/usr/bin/env python3
"""Record a test run against the code it tested, and check that record later.

Spec: docs/specs/test-evidence-freshness.md.

  record_test_run.py run --worklog <path> [--root <repo>] -- <command> [args...]
      Runs the command (no shell), fingerprints the code before and after, and appends
      one line under the Work Log's `## Test Gate Results`:
        - Test run: `<command>` | exit: <n> | tree: <40-hex|unstable> | at: <ISO-UTC>
      Exits with the command's exit code.

  record_test_run.py check [--root <repo>]
      Reads the current branch's active Work Log(s). Exit 1 (FAIL) when the latest
      recorded run failed and a later test/ship PASS receipt exists, or when the code
      changed after the latest run and a ship receipt exists. Other findings are printed
      as WARN text with exit 0. A log with no `Test run:` line is not checked.

The fingerprint is `git write-tree` of a temporary index (seeded from the real one, so
the real index is never written) holding every tracked and untracked, non-ignored file
except `.agentcortex/context/` — runtime state such as Work Logs and the SSoT. Recording
the result, or shipping, therefore does not change it. A hand-typed line with a correct
fingerprint passes: this detects stale and failed evidence, not forged evidence.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXCLUDE = ".agentcortex/context"
SECTION = "## Test Gate Results"
RUN_RE = re.compile(
    r"^- Test run: `(?P<cmd>[^`]*)` \| exit: (?P<exit>-?\d+) \| tree: (?P<tree>[0-9a-f]{40}|unstable|none)"
    r" \| at: (?P<at>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s*$"
)
RECEIPT_RE = re.compile(
    r"^\s*-\s*Gate:\s*(?P<phase>[a-z-]+)\s*\|\s*Verdict:\s*(?P<verdict>[a-z ]+?)\s*\|.*?"
    r"Timestamp:\s*(?P<ts>\S+)",
    re.I,
)


def parse_ts(raw: str) -> _dt.datetime | None:
    """ISO date, date-time, minute precision, Z or offset -> aware UTC; None if unparseable.
    A date or a time with no zone is read as UTC (the template asks for `date -u`)."""
    raw = raw.strip().rstrip(",;")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        # A date alone is read as the end of that day: it cannot prove it came first.
        # (Checked first: fromisoformat accepts a bare date as midnight on 3.11+.)
        raw += "T23:59:59+00:00"
    if raw.endswith("Z") or raw.endswith("z"):
        raw = raw[:-1] + "+00:00"
    try:
        value = _dt.datetime.fromisoformat(raw)
    except ValueError:
        try:
            # A date alone is read as the end of that day: it cannot prove it came first.
            value = _dt.datetime.combine(_dt.date.fromisoformat(raw), _dt.time(23, 59, 59))
        except ValueError:
            return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=_dt.timezone.utc)
    return value.astimezone(_dt.timezone.utc)


def _git(root: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)


def fingerprint(root: Path) -> str | None:
    """Tree id of the working tree minus runtime state, or None when git cannot say."""
    if shutil.which("git") is None:
        return None
    idx = _git(root, "rev-parse", "--git-path", "index")
    if idx.returncode != 0:
        return None
    real = Path(idx.stdout.strip())
    if not real.is_absolute():
        real = root / real
    tmpdir = tempfile.mkdtemp(prefix="acx-fp-")
    try:
        tmp = Path(tmpdir) / "index"
        if real.exists():
            # copy2 keeps the index mtime: git re-reads entries modified within the same
            # second as the index ("racy" entries). copyfile would give the copy a fresh
            # mtime and git would trust stale stat data for same-size edits.
            shutil.copy2(real, tmp)
        env = {**os.environ, "GIT_INDEX_FILE": str(tmp)}
        for args in (("update-index", "-q", "--refresh"), ("add", "-A", "--", "."),
                     ("rm", "-r", "-q", "--cached", "--ignore-unmatch", "--", EXCLUDE)):
            if _git(root, *args, env=env).returncode != 0 and args[0] != "update-index":
                return None
        out = _git(root, "write-tree", env=env)
        return out.stdout.strip() if out.returncode == 0 else None
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_run(worklog: Path, line: str) -> None:
    text = worklog.read_text(encoding="utf-8")
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == SECTION)
    except StopIteration:
        lines += ["", SECTION, line]
        worklog.write_text(nl.join(lines), encoding="utf-8", newline="")
        return
    end = start + 1
    while end < len(lines) and not (lines[end].startswith("## ") or lines[end].strip() == "---"):
        end += 1
    body = [i for i in range(start + 1, end) if lines[i].strip()]
    if len(body) == 1 and lines[body[0]].strip() == "none":
        lines[body[0]] = line
    else:
        at = (body[-1] + 1) if body else start + 1
        lines.insert(at, line)
    worklog.write_text(nl.join(lines), encoding="utf-8", newline="")


def cmd_run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    worklog = Path(args.worklog)
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("record_test_run: no command given (usage: run --worklog <path> -- <command...>)", file=sys.stderr)
        return 2
    if not worklog.is_file():
        print(f"record_test_run: Work Log not found: {worklog}", file=sys.stderr)
        return 2
    typed = list(command)  # recorded as typed; the resolved path is only used to launch
    exe = shutil.which(command[0], path=os.environ.get("PATH"))
    if exe:
        command = [exe, *command[1:]]
    before = fingerprint(root)
    try:
        proc = subprocess.run(command, cwd=str(root))
        code = proc.returncode
    except OSError as exc:
        print(f"record_test_run: could not start {command[0]!r}: {exc}", file=sys.stderr)
        code = 127
    after = fingerprint(root)
    if before is None or after is None:
        tree = "none"  # git could not fingerprint this tree: reported, never a ship FAIL
    else:
        tree = before if before == after else "unstable"
    # One line, no backticks: a newline or control character in an argument would split the
    # record and `check` would no longer see it.
    shown = " ".join(" ".join(typed).splitlines())  # every separator splitlines() honours
    shown = re.sub(r"[\x00-\x1f\x7f]+", " ", shown).replace("`", "'")
    append_run(worklog, f"- Test run: `{shown}` | exit: {code} | tree: {tree} | at: {_now()}")
    note = {"unstable": " (code changed during the run)",
            "none": " (git could not fingerprint this tree)"}.get(tree, "")
    print(f"record_test_run: exit {code}, tree {tree}{note} -> {worklog}")
    return code


def worklog_key(branch: str) -> str:
    key = re.sub(r"[^a-zA-Z0-9._-]", "-", branch)
    key = re.sub(r"-{2,}", "-", key).strip("-.").lower()
    return key[:100]


def _header_branch(path: Path) -> str | None:
    m = re.search(r"^- Branch:\s*`?([^`\n]+?)`?\s*$", path.read_text(encoding="utf-8", errors="replace"), re.M)
    return m.group(1) if m else None


def _receipts(text: str) -> list[tuple[str, str, _dt.datetime | None]]:
    out = []
    for line in text.splitlines():
        m = RECEIPT_RE.match(line)
        if m:
            out.append((m.group("phase").lower(), m.group("verdict").strip().upper(), parse_ts(m.group("ts"))))
    return out


def check_log(path: Path, current: str | None) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    runs = [m for m in (RUN_RE.match(l) for l in text.splitlines()) if m]
    if not runs:
        return [], []
    last = runs[-1]
    receipts = _receipts(text)
    fails, warns = [], []
    name = path.name
    run_at = parse_ts(last.group("at"))
    shipped = any(r[0] == "ship" for r in receipts)
    if last.group("exit") != "0":
        # A receipt with no parseable time is treated as later: it cannot prove it came first.
        later = [r for r in receipts if r[0] in ("test", "ship") and r[1] == "PASS"
                 and (r[2] is None or run_at is None or r[2] >= run_at)]
        if later:
            fails.append(f"{name}: latest recorded test run exited {last.group('exit')} "
                         f"but a later {later[0][0]} PASS receipt exists")
        else:
            warns.append(f"{name}: latest recorded test run exited {last.group('exit')}")
    if last.group("tree") == "none":
        warns.append(f"{name}: the latest recorded run could not be fingerprinted (git failed on this tree); freshness not checked")
    elif last.group("tree") == "unstable":
        msg = f"{name}: latest recorded test run is 'unstable' (code changed during the run)"
        (fails if shipped else warns).append(msg + ("; re-run the tests before ship" if shipped else ""))
    elif current is None:
        warns.append(f"{name}: could not fingerprint the working tree (not a git work tree, or git unavailable)")
    elif last.group("tree") != current:
        msg = f"{name}: code changed after the latest recorded test run ({last.group('at')}); re-run the tests"
        (fails if shipped else warns).append(msg + (" before ship" if shipped else ""))
    return fails, warns


def cmd_check(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    work = root / ".agentcortex" / "context" / "work"
    if shutil.which("git") is None or _git(root, "rev-parse", "--git-dir").returncode != 0:
        print("WARN: test evidence freshness -- not a git work tree; nothing checked")
        return 0
    br = _git(root, "symbolic-ref", "-q", "--short", "HEAD")
    if br.returncode != 0:
        print("WARN: test evidence freshness -- detached HEAD; the branch's Work Log cannot be resolved, not checked")
        return 0
    branch = br.stdout.strip()
    key = worklog_key(branch)
    logs = []
    if work.is_dir():
        for p in sorted(work.glob("*.md")):
            if p.name == f"{key}.md":
                logs.append(p)
            elif p.name.endswith(f"-{key}.md") and _header_branch(p) == branch:
                logs.append(p)  # multi-person variant <owner>-<key>.md of this branch
    recorded = [p for p in logs
                if any(RUN_RE.match(l) for l in p.read_text(encoding="utf-8", errors="replace").splitlines())]
    if not recorded:
        print("test evidence freshness: no recorded test run on the current branch (opt-in; nothing checked)")
        return 0
    current = fingerprint(root)
    all_fails, all_warns = [], []
    for p in recorded:
        f, w = check_log(p, current)
        all_fails += f
        all_warns += w
    for w in all_warns:
        print(f"WARN: {w}")
    for f in all_fails:
        print(f"FAIL: {f}")
    if not all_fails and not all_warns:
        print(f"test evidence freshness: {len(recorded)} log(s) current")
    return 1 if all_fails else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a test command and record it")
    r.add_argument("--worklog", required=True)
    r.add_argument("--root", default=".")
    r.add_argument("command", nargs=argparse.REMAINDER)
    c = sub.add_parser("check", help="check the current branch's recorded runs")
    c.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    return cmd_run(args) if args.cmd == "run" else cmd_check(args)


if __name__ == "__main__":
    sys.exit(main())
