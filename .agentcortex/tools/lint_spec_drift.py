#!/usr/bin/env python3
"""Advisory spec-vs-diff linter for Agentic OS review."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


PATH_RE = re.compile(r"(?<!://)([A-Za-z0-9._-]+(?:[\\/][A-Za-z0-9._-]+)+\.[A-Za-z0-9._-]+)")
SPEC_REF_RE = re.compile(r"docs[\\/]specs[\\/][A-Za-z0-9._/-]+\.md")


@dataclass(frozen=True)
class DriftResult:
    uncovered_changed: list[str]
    untouched_ac_paths: list[str]

    @property
    def warning_count(self) -> int:
        return len(self.uncovered_changed) + len(self.untouched_ac_paths)


def normalize_path(value: str) -> str:
    path = value.strip().strip("`'\"")
    path = path.replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path.strip("/")


def acceptance_criteria_section(markdown: str) -> str:
    lines = markdown.splitlines()
    collected: list[str] = []
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip().lower()
            if in_section:
                break
            in_section = heading == "acceptance criteria"
            continue
        if in_section:
            collected.append(line)
    return "\n".join(collected)


def extract_ac_paths(markdown: str) -> set[str]:
    section = acceptance_criteria_section(markdown)
    paths: set[str] = set()
    for match in PATH_RE.finditer(section):
        paths.add(normalize_path(match.group(1)))
    return paths


def path_covers(ac_path: str, changed_path: str) -> bool:
    ac_norm = normalize_path(ac_path)
    changed_norm = normalize_path(changed_path)
    if ac_norm.endswith("/"):
        return changed_norm.startswith(ac_norm)
    return changed_norm == ac_norm


def evaluate_drift(changed_files: list[str], ac_paths: set[str]) -> DriftResult:
    changed = sorted({normalize_path(path) for path in changed_files if path.strip()})
    ac = sorted({normalize_path(path) for path in ac_paths if path.strip()})

    uncovered_changed = [
        path
        for path in changed
        if not any(path_covers(ac_path, path) for ac_path in ac)
    ]
    untouched_ac_paths = [
        path
        for path in ac
        if not any(path_covers(path, changed_path) for changed_path in changed)
    ]
    return DriftResult(uncovered_changed=uncovered_changed, untouched_ac_paths=untouched_ac_paths)


def validate_revision(value: str | None) -> str | None:
    if value and value.startswith("-"):
        raise RuntimeError(f"unsafe git revision: {value}")
    return value


def spec_from_worklog(worklog_text: str) -> str | None:
    for raw_line in worklog_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 2 and cells[0].lower() == "spec":
            match = SPEC_REF_RE.search(cells[1])
            if match:
                return normalize_path(match.group(0))
    match = SPEC_REF_RE.search(worklog_text)
    return normalize_path(match.group(0)) if match else None


def changed_files(root: Path, base: str | None = None, head: str | None = None) -> list[str]:
    base = validate_revision(base)
    head = validate_revision(head)
    if base and head:
        args = ["git", "diff", "--name-only", base, head]
    elif base:
        args = ["git", "diff", "--name-only", base]
    else:
        args = ["git", "diff", "--name-only", "HEAD"]
    result = subprocess.run(args, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git diff failed")
    files = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    if not base and not head:
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if untracked.returncode != 0:
            raise RuntimeError(untracked.stderr.strip() or "git ls-files failed")
        files.update(line.strip() for line in untracked.stdout.splitlines() if line.strip())
    return sorted(files)


def resolve_spec_path(root: Path, spec: str | None, worklog: str | None) -> Path | None:
    if spec:
        return root / normalize_path(spec)
    if not worklog:
        return None
    worklog_path = root / normalize_path(worklog)
    if not worklog_path.is_file():
        raise FileNotFoundError(f"worklog not found: {worklog}")
    resolved = spec_from_worklog(worklog_path.read_text(encoding="utf-8"))
    return (root / resolved) if resolved else None


def print_result(result: DriftResult) -> None:
    print(f"Spec drift advisory: {result.warning_count} warning(s)")
    if result.warning_count == 0:
        print("OK: changed files match AC path references")
        return
    for path in result.uncovered_changed:
        print(f"UNCOVERED_CHANGED: {path}")
    for path in result.untouched_ac_paths:
        print(f"UNTOUCHED_AC_PATH: {path}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    if argv is not None and argv and argv[0].endswith(".py"):
        argv = argv[1:]
    parser = argparse.ArgumentParser(description="Advisory spec-vs-diff linter.")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--spec", help="Spec path, e.g. docs/specs/example.md")
    parser.add_argument("--worklog", help="Work Log path used to discover the spec")
    parser.add_argument("--base", help="Base git revision for diff")
    parser.add_argument("--head", help="Head git revision for diff")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    try:
        spec_path = resolve_spec_path(root, args.spec, args.worklog)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if spec_path is None:
        print("spec not found: pass --spec or --worklog with a Spec reference", file=sys.stderr)
        return 2
    if not spec_path.is_file():
        print(f"spec not found: {spec_path}", file=sys.stderr)
        return 2

    try:
        changed = changed_files(root, args.base, args.head)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    ac_paths = extract_ac_paths(spec_path.read_text(encoding="utf-8"))
    print_result(evaluate_drift(changed, ac_paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
