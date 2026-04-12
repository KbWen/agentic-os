#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

TEXT_SUFFIXES = {
    '.md', '.sh', '.ps1', '.cmd', '.bat', '.yml', '.yaml', '.txt',
    '.rules', '.toml', '.json', '.py', '.cff'
}
TEXT_FILENAMES = {'.gitignore', '.gitattributes', '.editorconfig'}
UTF8_BOM = b'\xef\xbb\xbf'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Check tracked and untracked text files for encoding regressions.')
    parser.add_argument('--root', type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1])
    parser.add_argument('--baseline', type=pathlib.Path, default=None)
    return parser.parse_args()


def candidate_files(root: pathlib.Path) -> list[pathlib.Path]:
    commands = (
        ['git', 'ls-files', '-z'],
        ['git', 'ls-files', '-z', '--others', '--exclude-standard'],
    )
    seen: set[str] = set()
    paths: list[pathlib.Path] = []
    for command in commands:
        output = subprocess.check_output(command, cwd=root)
        for item in output.split(b'\0'):
            if not item:
                continue
            rel = item.decode('utf-8')
            if rel in seen:
                continue
            seen.add(rel)
            paths.append(root / rel)
    return paths


def is_text_candidate(path: pathlib.Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name.lower() in TEXT_FILENAMES


def load_baseline(path: pathlib.Path | None, root: pathlib.Path) -> set[str]:
    baseline_path = path or root / 'tools' / 'text_integrity_baseline.txt'
    if not baseline_path.is_file():
        return set()
    entries = set()
    for raw in baseline_path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        entries.add(line.replace('\\', '/'))
    return entries


def has_mixed_eol_bytes(data: bytes) -> bool:
    has_crlf = b'\r\n' in data
    normalized = data.replace(b'\r\n', b'')
    has_bare_lf = b'\n' in normalized
    has_bare_cr = b'\r' in normalized
    return (has_crlf and (has_bare_lf or has_bare_cr)) or (has_bare_lf and has_bare_cr)


def inspect_file(path: pathlib.Path, root: pathlib.Path) -> list[str]:
    issues: list[str] = []
    data = path.read_bytes()
    if data.startswith(UTF8_BOM):
        issues.append('utf8-bom')
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        issues.append('invalid-utf8')
        return issues
    if has_mixed_eol_bytes(data):
        issues.append('mixed-eol')
    if '\x00' in text:
        issues.append('null-byte')
    return issues


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    baseline = load_baseline(args.baseline, root)
    baseline_hits: list[tuple[str, list[str]]] = []
    regressions: list[tuple[str, list[str]]] = []

    for path in candidate_files(root):
        if not path.is_file() or not is_text_candidate(path):
            continue
        rel = path.relative_to(root).as_posix()
        issues = inspect_file(path, root)
        if not issues:
            continue
        bucket = baseline_hits if rel in baseline else regressions
        bucket.append((rel, issues))

    if regressions:
        print('Text integrity regression(s) detected:', file=sys.stderr)
        for rel, issues in regressions:
            print(f'  - {rel}: {", ".join(issues)}', file=sys.stderr)
        if baseline_hits:
            print(f'Baseline exceptions still present: {len(baseline_hits)}', file=sys.stderr)
        return 1

    print(f'Text integrity check passed ({len(baseline_hits)} baseline exception(s) tracked).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())