#!/usr/bin/env python3
"""Verify reviewable Agentic OS work logs and emit CI-friendly findings."""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REVIEWABLE_WORKLOG_DIR = ".agentcortex/context/review/"
ACTIVE_WORKLOG_DIR = ".agentcortex/context/work/"
DEPENDENCY_MANIFESTS = {
    "package.json",
    "requirements.txt",
    "go.mod",
    "Cargo.toml",
    "pubspec.yaml",
}
ALLOWLIST_PREFIXES = {
    ("pytest",),
    ("python", "-m", "pytest"),
    ("python3", "-m", "pytest"),
    ("npm", "test"),
    ("pnpm", "test"),
    ("yarn", "test"),
    ("go", "test"),
    ("cargo", "test"),
    ("flutter", "test"),
}
UNSAFE_CHARS = set("&;|><`$\n\r\0")
VALID_CLASSIFICATIONS = {"tiny-fix", "quick-win", "feature", "architecture-change", "hotfix"}
WINDOWS_ABSOLUTE_PATH = re.compile(r"^[A-Za-z]:[\\/]")
PHASE_RULES = {
    "tiny-fix": [],
    "quick-win": ["bootstrap", "plan", "implement", "ship"],
    "feature": ["bootstrap", "spec", "plan", "implement", "review", "test", "handoff", "ship"],
    "architecture-change": ["bootstrap", "adr", "spec", "plan", "implement", "review", "test", "handoff", "ship"],
    "hotfix": ["bootstrap", "research", "plan", "implement", "review", "test", "ship"],
}
STRUCTURED_LESSON = re.compile(
    r"^\s*-\s*\[Category:\s*(?P<category>[^\]]+)\]\[Severity:\s*(?P<severity>HIGH|MEDIUM|LOW)\]"
    r"\[Trigger:\s*(?P<trigger>[^\]]+)\]\s*(?P<body>.+?)\s*$"
)
HEADER_FIELD = re.compile(r"^\s*-\s+\*\*(?P<key>[^*]+)\*\*:\s*(?P<value>.+?)\s*$")


@dataclass
class EvidenceEntry:
    command: str
    result: str
    summary: str


@dataclass
class WorkLog:
    path: Path
    classification: str
    headers: dict[str, str]
    sections: dict[str, str]
    evidence: list[EvidenceEntry]
    phases: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify reviewable Work Log evidence and soft-gate coverage.")
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--base-sha", help="Base git revision for diff")
    parser.add_argument("--head-sha", help="Head git revision for diff")
    parser.add_argument("--current-state", default=".agentcortex/context/current_state.md", help="SSoT path")
    parser.add_argument(
        "--skill-matrix",
        default=".agent/rules/skill_conflict_matrix.md",
        help="Skill conflict matrix path",
    )
    parser.add_argument(
        "--path",
        dest="paths",
        action="append",
        default=[],
        help="Explicit work log path to verify (can be repeated)",
    )
    return parser.parse_args()


def normalize_token(value: str) -> str:
    lowered = value.lower()
    replaced = re.sub(r"[^a-z0-9]+", "-", lowered)
    return replaced.strip("-")


def normalize_text(value: str) -> str:
    return normalize_token(value).replace("-", " ")


def is_empty_section(value: str | None) -> bool:
    if value is None:
        return True
    normalized_lines: list[str] = []
    for raw_line in value.splitlines():
        cleaned = re.sub(r"^\s*[-*+]\s+", "", raw_line).strip().lower()
        if cleaned:
            normalized_lines.append(cleaned)
    if not normalized_lines:
        return True
    return all(line == "none" for line in normalized_lines)


def parse_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def parse_headers(text: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in text.splitlines():
        match = HEADER_FIELD.match(line)
        if match:
            headers[match.group("key").strip()] = match.group("value").strip()
        elif line.startswith("## "):
            break
    return headers


def parse_phase_sequence(section: str) -> list[str]:
    phases: list[str] = []
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        phases.append(line[2:].strip().lower())
    return phases


def parse_evidence(section: str) -> list[EvidenceEntry]:
    entries: list[EvidenceEntry] = []
    current: dict[str, str] = {}
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.lower().startswith("command:"):
            if current:
                entries.append(
                    EvidenceEntry(
                        command=current.get("command", ""),
                        result=current.get("result", ""),
                        summary=current.get("summary", ""),
                    )
                )
            current = {"command": line.split(":", 1)[1].strip()}
        elif line.lower().startswith("result:"):
            current["result"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("summary:"):
            current["summary"] = line.split(":", 1)[1].strip()
    if current:
        entries.append(
            EvidenceEntry(
                command=current.get("command", ""),
                result=current.get("result", ""),
                summary=current.get("summary", ""),
            )
        )
    return entries


def parse_work_log(path: Path) -> WorkLog:
    text = path.read_text(encoding="utf-8")
    headers = parse_headers(text)
    sections = parse_sections(text)
    classification = headers.get("Classification", "").strip().lower()
    return WorkLog(
        path=path,
        classification=classification,
        headers=headers,
        sections=sections,
        evidence=parse_evidence(sections.get("Evidence", "")),
        phases=parse_phase_sequence(sections.get("Phase Sequence", "")),
    )


def changed_files(root: Path, base_sha: str, head_sha: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", base_sha, head_sha],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git diff failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def discover_work_logs(root: Path, args: argparse.Namespace) -> tuple[list[Path], list[str]]:
    changed: list[str] = []
    if args.paths:
        paths = [(root / relative).resolve() for relative in args.paths]
        return paths, changed
    if args.base_sha and args.head_sha:
        changed = changed_files(root, args.base_sha, args.head_sha)
        logs = []
        for relative in changed:
            normalized = relative.replace("\\", "/")
            if (
                normalized.startswith(REVIEWABLE_WORKLOG_DIR)
                or normalized.startswith(ACTIVE_WORKLOG_DIR)
            ) and normalized.endswith(".md"):
                logs.append((root / normalized).resolve())
        return logs, changed
    return [], changed


def review_mirror_opted_in(root: Path) -> bool:
    review_dir = (root / REVIEWABLE_WORKLOG_DIR).resolve()
    if not review_dir.is_dir():
        return False
    if (review_dir / ".gitkeep").is_file():
        return True
    return any(review_dir.glob("*.md"))


def load_high_lessons(path: Path) -> list[tuple[str, str]]:
    if not path.is_file():
        return []
    lessons: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = STRUCTURED_LESSON.match(line)
        if not match:
            continue
        if match.group("severity") != "HIGH":
            continue
        lessons.append((normalize_token(match.group("trigger")), match.group("body").strip()))
    return lessons


def load_skill_conflicts(path: Path) -> dict[frozenset[str], str]:
    if not path.is_file():
        return {}
    matrix: dict[frozenset[str], str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0].lower().startswith("skill a") or set(cells[0]) == {"-"}:
            continue
        relation = normalize_token(cells[2])
        if relation not in {"partial-conflict", "conflict"}:
            continue
        matrix[frozenset({normalize_token(cells[0]), normalize_token(cells[1])})] = relation
    return matrix


def parse_recommended_skills(value: str) -> list[str]:
    if not value or value.strip().lower() == "none":
        return []
    skills: list[str] = []
    for part in value.split(","):
        fragment = part.strip()
        if not fragment:
            continue
        name = fragment.split("(", 1)[0].strip()
        skills.append(normalize_token(name))
    return skills


def phase_order_status(classification: str, phases: list[str]) -> tuple[bool, bool]:
    required = PHASE_RULES.get(classification, [])
    if not required:
        return True, True
    if not phases:
        return False, False
    if "ship" in phases and phases[-1] != "ship":
        return False, False
    seen: set[str] = set()
    for phase in phases:
        if phase not in required:
            return False, False
        phase_index = required.index(phase)
        if any(required[index] not in seen for index in range(phase_index)):
            return False, False
        seen.add(phase)
    return True, all(phase in seen for phase in required)


def classify_result_marker(result: str) -> bool | None:
    lowered = result.strip().lower()
    if any(token in lowered for token in {"pass", "passed", "success", "ok"}):
        return True
    if any(token in lowered for token in {"fail", "failed", "error"}):
        return False
    return None


def command_is_safe(command: str) -> bool:
    return not any(char in command for char in UNSAFE_CHARS)


def command_is_allowlisted(argv: list[str]) -> bool:
    for prefix in ALLOWLIST_PREFIXES:
        if tuple(argv[: len(prefix)]) == prefix:
            return True
    return False


def arg_targets_outside_repo(arg: str) -> bool:
    normalized = arg.replace("\\", "/")
    if WINDOWS_ABSOLUTE_PATH.match(arg) or normalized.startswith("/"):
        return True
    return normalized == ".." or normalized.startswith("../") or "/../" in normalized or normalized.endswith("/..")


def argv_args_are_safe(argv: list[str]) -> bool:
    """Reject suspicious arguments after an allowlisted command prefix."""
    for arg in argv[1:]:
        if any(char in arg for char in UNSAFE_CHARS):
            return False
        candidate = arg.split("=", 1)[1] if arg.startswith("-") and "=" in arg else arg
        if candidate and arg_targets_outside_repo(candidate):
            return False
    return True


def rerun_evidence(root: Path, entry: EvidenceEntry) -> tuple[str, bool]:
    """Rerun an allowlisted evidence command and compare the reported result.

    Safety note: commands execute in the repository root with full filesystem
    access. In CI this runs on an ephemeral runner. In local `--path` mode, use
    it only with Work Logs from authors you trust.
    """
    command = entry.command.strip()
    if not command:
        return "UNVERIFIED: missing command stanza.", False
    if not command_is_safe(command):
        return f"UNVERIFIED: unsafe command syntax in `{command}`.", False
    try:
        argv = shlex.split(command, posix=True)
    except ValueError as exc:
        return f"UNVERIFIED: could not parse command `{command}` ({exc}).", False
    if not argv or not command_is_allowlisted(argv):
        return f"UNVERIFIED: command `{command}` is not in the deterministic allowlist.", False
    if not argv_args_are_safe(argv):
        return f"UNVERIFIED: command `{command}` contains suspicious arguments.", False
    expected = classify_result_marker(entry.result)
    if expected is None:
        return f"UNVERIFIED: result marker for `{command}` is narrative-only.", False
    try:
        result = subprocess.run(argv, cwd=root, capture_output=True, text=True, check=False)
    except OSError as exc:
        return f"UNVERIFIED: could not execute `{command}` ({exc}).", False
    actual = result.returncode == 0
    if actual != expected:
        return (
            f"Evidence mismatch for `{command}`: work log says `{entry.result}` but rerun exited {result.returncode}.",
            True,
        )
    return f"Verified `{command}` ({entry.result}).", False


def gha_annotate(level: str, message: str, path: Path | None = None) -> None:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    if path is None:
        print(f"::{level}::{message}")
    else:
        print(f"::{level} file={path.as_posix()}::{message}")


def emit_skip_warning(changed: list[str], *, opted_in: bool) -> None:
    if not changed:
        print("No changed reviewable Work Logs found.")
        return
    if not opted_in:
        print("No changed reviewable Work Logs found; PR-visible evidence checks are not enabled for this repo.")
        return
    message = (
        "No changed reviewable Work Logs found. Evidence verification was skipped; "
        f"commit a mirror under `{REVIEWABLE_WORKLOG_DIR}` if this repo opts into PR-visible evidence checks."
    )
    print(f"WARNING: {message}")
    gha_annotate("warning", message)


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    state_path = (root / args.current_state).resolve()
    matrix_path = (root / args.skill_matrix).resolve()

    try:
        work_logs, changed = discover_work_logs(root, args)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    opted_in = review_mirror_opted_in(root)

    if not work_logs:
        emit_skip_warning(changed, opted_in=opted_in)
        return 0

    high_lessons = load_high_lessons(state_path)
    conflicts = load_skill_conflicts(matrix_path)
    changed_manifest = any(Path(path).name in DEPENDENCY_MANIFESTS for path in changed)

    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    for log_path in work_logs:
        if not log_path.is_file():
            errors.append(f"{log_path}: missing active Work Log file.")
            continue
        work_log = parse_work_log(log_path)
        relative_path = log_path.relative_to(root)

        if work_log.classification not in VALID_CLASSIFICATIONS:
            errors.append(f"{relative_path}: invalid or missing Classification.")
        required_sections = [
            "Task Description",
            "Phase Sequence",
            "Evidence",
            "External References",
            "Known Risk",
            "Conflict Resolution",
            "Skill Notes",
        ]
        for section in required_sections:
            if section not in work_log.sections:
                errors.append(f"{relative_path}: missing required section `## {section}`.")
        if is_empty_section(work_log.sections.get("Task Description")):
            errors.append(f"{relative_path}: `## Task Description` must not be empty.")
        phase_valid, phase_complete = phase_order_status(work_log.classification, work_log.phases)
        if not phase_valid:
            errors.append(
                f"{relative_path}: invalid phase sequence for `{work_log.classification}` "
                f"({', '.join(work_log.phases) or 'none'})."
            )
        elif not phase_complete and str(relative_path).replace("\\", "/").startswith(REVIEWABLE_WORKLOG_DIR):
            notes.append(
                f"{relative_path}: in-progress phase sequence accepted; ship gate not yet validated."
            )
        if is_empty_section(work_log.sections.get("Evidence")):
            errors.append(f"{relative_path}: `## Evidence` must not be empty.")

        if changed_manifest and work_log.classification != "tiny-fix" and is_empty_section(
            work_log.sections.get("External References")
        ):
            warnings.append(
                f"{relative_path}: dependency manifest changed but `## External References` is empty."
            )

        task_text = normalize_text(work_log.sections.get("Task Description", ""))
        if high_lessons and not is_empty_section(work_log.sections.get("Task Description")):
            for trigger, lesson in high_lessons:
                trigger_text = trigger.replace("-", " ")
                if trigger_text and trigger_text in task_text and is_empty_section(work_log.sections.get("Known Risk")):
                    warnings.append(
                        f"{relative_path}: HIGH Global Lesson trigger `{trigger}` matched task description but "
                        f"`## Known Risk` is empty."
                    )
                    break

        recommended_skills = parse_recommended_skills(work_log.headers.get("Recommended Skills", ""))
        if len(recommended_skills) >= 2 and is_empty_section(work_log.sections.get("Conflict Resolution")):
            for index, skill_a in enumerate(recommended_skills):
                for skill_b in recommended_skills[index + 1 :]:
                    relation = conflicts.get(frozenset({skill_a, skill_b}))
                    if relation:
                        warnings.append(
                            f"{relative_path}: recommended skills `{skill_a}` + `{skill_b}` are marked "
                            f"`{relation}` but `## Conflict Resolution` is empty."
                        )
                        break
                else:
                    continue
                break

        if work_log.evidence:
            for entry in work_log.evidence:
                message, is_error = rerun_evidence(root, entry)
                if is_error:
                    errors.append(f"{relative_path}: {message}")
                else:
                    notes.append(f"{relative_path}: {message}")
        else:
            warnings.append(f"{relative_path}: no executable Evidence stanzas found; marked UNVERIFIED.")

    for note in notes:
        print(note)
    for warning in warnings:
        print(f"WARNING: {warning}")
        gha_annotate("warning", warning)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
        gha_annotate("error", error)

    print(
        f"Verified {len(work_logs)} work log(s): {len(errors)} error(s), {len(warnings)} warning(s), {len(notes)} note(s)."
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
