#!/usr/bin/env python3
"""Guarded read/write operations for AgentCortex context files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


MISSING_SHA = "MISSING"
DEFAULT_RECEIPT = Path(".agentcortex/context/.guard_receipt.json")
LOCK_ROOT = Path(".agentcortex/context/.guard_locks")
CONTEXT_ROOT = Path(".agentcortex/context")
LOCK_STALE_SECONDS = 900


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely snapshot or write AgentCortex context files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot = subparsers.add_parser("snapshot", help="Read a file and emit its sha256.")
    snapshot.add_argument("--path", required=True, help="Target file path")
    snapshot.add_argument("--root", default=".", help="Repository root")

    write = subparsers.add_parser("write", help="Write a file with optimistic locking.")
    write.add_argument("--path", required=True, help="Target file path")
    write.add_argument("--root", default=".", help="Repository root")
    write.add_argument("--expected-sha", required=True, help="Expected current sha256 or MISSING")
    write.add_argument("--lock-key", required=True, help="Stable lock key for the write scope")
    write.add_argument("--input", required=True, help="File that contains the desired new content")
    write.add_argument(
        "--receipt",
        default=str(DEFAULT_RECEIPT),
        help="Receipt path relative to --root (default: .agentcortex/context/.guard_receipt.json)",
    )
    return parser.parse_args()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolve_target(root: Path, target: str) -> Path:
    path = (root / target).resolve()
    context_root = (root / CONTEXT_ROOT).resolve()
    try:
        path.relative_to(context_root)
    except ValueError as exc:
        raise ValueError(f"target must stay under {CONTEXT_ROOT.as_posix()}: {target}") from exc
    return path


def read_text_and_sha(path: Path) -> tuple[str | None, str]:
    if not path.exists():
        return None, MISSING_SHA
    text = path.read_text(encoding="utf-8")
    return text, sha256_text(text)


def relative_posix(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def lock_path_for_target(root: Path, target: Path) -> Path:
    target_key = relative_posix(target, root)
    digest = hashlib.sha256(target_key.encode("utf-8")).hexdigest()[:16]
    stem = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in target.stem.lower())
    return (root / LOCK_ROOT / f"{stem}-{digest}.lock").resolve()


def lock_age_seconds(lock_path: Path) -> float:
    try:
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        timestamp = int(payload.get("timestamp", 0))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        timestamp = int(lock_path.stat().st_mtime)
    return max(0.0, time.time() - timestamp)


def stale_lock_threshold() -> int:
    raw = os.environ.get("ACX_GUARD_STALE_SECONDS", "").strip()
    if not raw:
        return LOCK_STALE_SECONDS
    try:
        value = int(raw)
    except ValueError:
        return LOCK_STALE_SECONDS
    return value if value > 0 else LOCK_STALE_SECONDS


def clear_stale_lock(lock_path: Path) -> bool:
    try:
        age_seconds = lock_age_seconds(lock_path)
    except FileNotFoundError:
        return True
    if age_seconds < stale_lock_threshold():
        return False
    try:
        lock_path.unlink()
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False


@contextmanager
def file_lock(lock_path: Path, *, metadata: dict[str, object] | None = None) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = None
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    for _attempt in range(2):
        try:
            handle = os.open(str(lock_path), flags)
            break
        except FileExistsError as exc:
            if clear_stale_lock(lock_path):
                continue
            raise RuntimeError(f"lock busy: {lock_path.name}") from exc
    if handle is None:
        raise RuntimeError(f"lock busy: {lock_path.name}")
    try:
        payload = {"pid": os.getpid(), "timestamp": int(time.time())}
        if metadata:
            payload.update(metadata)
        payload_json = json.dumps(payload, indent=2)
        os.write(handle, payload_json.encode("utf-8"))
        yield
    finally:
        if handle is not None:
            os.close(handle)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=path.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def write_receipt(root: Path, receipt_arg: str, *, target: Path, expected_sha: str, new_sha: str) -> Path:
    receipt = (root / receipt_arg).resolve()
    receipt.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "target": relative_posix(target, root),
        "timestamp": int(time.time()),
        "expected_sha": expected_sha,
        "new_sha": new_sha,
    }
    receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def cmd_snapshot(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    target = resolve_target(root, args.path)
    text, sha = read_text_and_sha(target)
    payload = {
        "path": relative_posix(target, root),
        "exists": text is not None,
        "sha256": sha,
        "size_bytes": len(text.encode("utf-8")) if text is not None else 0,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_write(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    target = resolve_target(root, args.path)
    input_path = (root / args.input).resolve()
    if not input_path.is_file():
        print(f"input file not found: {input_path}", file=sys.stderr)
        return 1
    try:
        content = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"could not read input file: {input_path} ({exc})", file=sys.stderr)
        return 1

    lock_path = lock_path_for_target(root, target)

    try:
        with file_lock(
            lock_path,
            metadata={
                "target": relative_posix(target, root),
                "scope": args.lock_key,
            },
        ):
            _, current_sha = read_text_and_sha(target)
            if current_sha != args.expected_sha:
                print(
                    json.dumps(
                        {
                            "status": "conflict",
                            "reason": "stale-sha",
                            "expected_sha": args.expected_sha,
                            "actual_sha": current_sha,
                            "path": relative_posix(target, root),
                        },
                        indent=2,
                        sort_keys=True,
                    ),
                    file=sys.stderr,
                )
                return 2

            atomic_write(target, content)
            new_sha = sha256_text(content)
            receipt = write_receipt(
                root,
                args.receipt,
                target=target,
                expected_sha=args.expected_sha,
                new_sha=new_sha,
            )
    except RuntimeError as exc:
        print(json.dumps({"status": "conflict", "reason": str(exc)}), file=sys.stderr)
        return 3
    except OSError as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "reason": "write-failed",
                    "detail": str(exc),
                    "path": relative_posix(target, root),
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 4
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "status": "ok",
                "path": relative_posix(target, root),
                "new_sha": new_sha,
                "receipt": str(receipt.relative_to(root)).replace("\\", "/"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def main() -> int:
    args = parse_args()
    if args.command == "snapshot":
        return cmd_snapshot(args)
    if args.command == "write":
        return cmd_write(args)
    print(f"unknown command: {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
