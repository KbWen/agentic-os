#!/usr/bin/env python3
"""Shared trigger-runtime helpers for Stage 1 compact-index governance."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_REGISTRY = ".agentcortex/metadata/trigger-registry.yaml"
DEFAULT_COMPACT_INDEX = ".agentcortex/metadata/trigger-compact-index.json"
SKILL_MANIFEST_NAME = "manifest.yaml"
DEFAULT_SKILL_PACKAGE_ROOT = ".agents/skills"
SKILL_REGISTRY_SNAPSHOT_VERSION = 1
SKILL_LOCKFILE_VERSION = 1
SKILL_POLICY_VERSION = 1

VALID_CLASSIFICATIONS = {"tiny-fix", "quick-win", "feature", "architecture-change", "hotfix"}
VALID_PHASES = {"bootstrap", "plan", "implement", "review", "test", "handoff", "ship"}
VALID_LIFECYCLE_STATES = {"active", "disabled", "deprecated", "retired", "quarantined"}
VALID_TRUST_TIERS = {"official", "partner", "community", "unverified"}
VALID_POLICY_RUNTIMES = {"claude", "codex", "antigravity"}
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z.-]+))?"
    r"(?:\+([0-9A-Za-z.-]+))?$"
)
SEMVER_CONSTRAINT_RE = re.compile(r"^(<=|>=|<|>|==|!=)?\s*(\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)$")

REQUIRED_SKILL_PACKAGE_FIELDS = {
    "id",
    "name",
    "version",
    "description",
    "engine_range",
    "entry_ref",
    "capabilities",
    "origin",
    "content_digest",
    "lifecycle",
}

OPTIONAL_SKILL_PACKAGE_FIELDS = {
    "api_range",
    "depends",
    "optional_companions",
    "provides",
    "trust_tier_hint",
    "signature",
    "homepage",
    "docs_ref",
    "replacement",
    "changelog_ref",
}

PHASE_WORKFLOW_MAP = {
    "bootstrap": ".agent/workflows/bootstrap.md",
    "plan": ".agent/workflows/plan.md",
    "implement": ".agent/workflows/implement.md",
    "review": ".agent/workflows/review.md",
    "test": ".agent/workflows/test.md",
    "handoff": ".agent/workflows/handoff.md",
    "ship": ".agent/workflows/ship.md",
}

PHASE_CONDITION_MATCHERS = {
    "enter-bootstrap": {"bootstrap"},
    "enter-phase": {"plan", "implement", "review", "test", "handoff", "ship"},
    "enter-plan": {"plan"},
    "enter-implement": {"implement"},
    "enter-review-or-test": {"review", "test"},
    "enter-handoff-or-ship": {"handoff", "ship"},
    "enter-review-or-handoff": {"review", "handoff"},
}

TRUST_TIER_CAPABILITY_ALLOWLIST = {
    "official": {"read_repo", "read_docs", "write_docs", "run_shell", "invoke_search", "invoke_connector"},
    "partner": {"read_repo", "read_docs", "write_docs", "invoke_search"},
    "community": {"read_repo", "read_docs"},
    "unverified": {"read_repo"},
}

TRUST_TIER_BUDGET_DEFAULTS = {
    "official": {"max_steps": 40, "max_tool_calls": 80, "timeout_seconds": 300},
    "partner": {"max_steps": 30, "max_tool_calls": 60, "timeout_seconds": 240},
    "community": {"max_steps": 20, "max_tool_calls": 40, "timeout_seconds": 180},
    "unverified": {"max_steps": 10, "max_tool_calls": 20, "timeout_seconds": 120},
}

RUNTIME_CAPABILITY_SUPPORT = {
    "claude": {"read_repo", "read_docs", "write_docs", "run_shell", "invoke_search", "invoke_connector"},
    "codex": {"read_repo", "read_docs", "write_docs", "run_shell", "invoke_search", "invoke_connector"},
    "antigravity": {"read_repo", "read_docs", "write_docs", "run_shell"},
}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", " ", value.casefold())).strip()


def split_csv(values: str | list[str] | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, list):
        return [value.strip() for value in values if value and value.strip()]
    if not values.strip():
        return []
    return [part.strip() for part in values.split(",") if part.strip()]


def load_json(path: Path) -> dict[str, Any]:
    from _yaml_loader import load_data

    return load_data(path)


def load_registry(root: Path, registry_rel: str = DEFAULT_REGISTRY) -> dict[str, Any]:
    return load_json((root / registry_rel).resolve())


def stable_content_hash(path: Path) -> str:
    # Normalize line endings to LF before hashing for cross-platform stability.
    content = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()[:8]


def stable_tree_hash(root: Path, *, exclude_names: set[str] | None = None) -> str:
    exclude_names = exclude_names or set()
    hasher = hashlib.sha256()
    # Sort by posix path string for cross-platform stability (Path sort is
    # case-insensitive on Windows but case-sensitive on Linux).
    all_files = [c for c in root.rglob("*") if c.is_file()]
    for path in sorted(all_files, key=lambda p: p.relative_to(root).as_posix()):
        if path.name in exclude_names:
            continue
        relative = path.relative_to(root).as_posix()
        content = path.read_bytes().replace(b"\r\n", b"\n")
        hasher.update(relative.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(content)
        hasher.update(b"\0")
    return hasher.hexdigest()


def package_content_hash(skill_dir: Path, manifest_name: str = SKILL_MANIFEST_NAME) -> str:
    """Hash all package files including manifest, but strip the content_digest
    field from the manifest to avoid circular self-reference."""
    hasher = hashlib.sha256()
    # Sort by posix path string for cross-platform stability (Path sort is
    # case-insensitive on Windows but case-sensitive on Linux).
    all_files = [c for c in skill_dir.rglob("*") if c.is_file()]
    for path in sorted(all_files, key=lambda p: p.relative_to(skill_dir).as_posix()):
        relative = path.relative_to(skill_dir).as_posix()
        content = path.read_bytes().replace(b"\r\n", b"\n")
        if path.name == manifest_name:
            lines = content.split(b"\n")
            content = b"\n".join(line for line in lines if not line.startswith(b"content_digest:"))
        hasher.update(relative.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(content)
        hasher.update(b"\0")
    return hasher.hexdigest()


def _parse_semver(version: str) -> tuple[int, int, int, list[str]]:
    match = SEMVER_RE.match(version)
    if not match:
        raise ValueError(f"invalid semantic version: {version}")
    major, minor, patch = (int(match.group(index)) for index in range(1, 4))
    prerelease = match.group(4) or ""
    prerelease_identifiers = prerelease.split(".") if prerelease else []
    return major, minor, patch, prerelease_identifiers


def _compare_prerelease_identifier(left: str, right: str) -> int:
    left_is_numeric = left.isdigit()
    right_is_numeric = right.isdigit()
    if left_is_numeric and right_is_numeric:
        left_value = int(left)
        right_value = int(right)
        if left_value < right_value:
            return -1
        if left_value > right_value:
            return 1
        return 0
    if left_is_numeric != right_is_numeric:
        return -1 if left_is_numeric else 1
    if left < right:
        return -1
    if left > right:
        return 1
    return 0


def _compare_semver(left: str, right: str) -> int:
    left_key = _parse_semver(left)
    right_key = _parse_semver(right)
    if left_key[:3] < right_key[:3]:
        return -1
    if left_key[:3] > right_key[:3]:
        return 1
    left_prerelease = left_key[3]
    right_prerelease = right_key[3]
    if left_prerelease == right_prerelease:
        return 0
    if not left_prerelease:
        return 1
    if not right_prerelease:
        return -1
    for left_identifier, right_identifier in zip(left_prerelease, right_prerelease):
        comparison = _compare_prerelease_identifier(left_identifier, right_identifier)
        if comparison != 0:
            return comparison
    if len(left_prerelease) < len(right_prerelease):
        return -1
    if len(left_prerelease) > len(right_prerelease):
        return 1
    return 0


def version_satisfies_range(version: str, version_range: str | list[str]) -> bool:
    constraints = [version_range] if isinstance(version_range, str) else version_range
    for constraint_set in constraints:
        parts = [part.strip() for part in str(constraint_set).split() if part.strip()]
        if not parts:
            continue
        matches_all = True
        for part in parts:
            match = SEMVER_CONSTRAINT_RE.match(part)
            if not match:
                matches_all = False
                break
            operator = match.group(1) or "=="
            expected = match.group(2)
            comparison = _compare_semver(version, expected)
            if operator == "==" and comparison != 0:
                matches_all = False
                break
            if operator == "!=" and comparison == 0:
                matches_all = False
                break
            if operator == ">" and comparison <= 0:
                matches_all = False
                break
            if operator == ">=" and comparison < 0:
                matches_all = False
                break
            if operator == "<" and comparison >= 0:
                matches_all = False
                break
            if operator == "<=" and comparison > 0:
                matches_all = False
                break
        if matches_all:
            return True
    return False


def load_skill_package_manifest(skill_dir: Path, manifest_name: str = SKILL_MANIFEST_NAME) -> dict[str, Any] | None:
    manifest_path = skill_dir / manifest_name
    if not manifest_path.is_file():
        return None
    data = load_json(manifest_path)
    if not isinstance(data, dict):
        raise ValueError(f"skill package manifest must be an object: {manifest_path}")
    return data


def _stable_json_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _dedupe_sorted_strings(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


def build_skill_registry_snapshot(
    root: Path,
    *,
    skill_package_root: str = DEFAULT_SKILL_PACKAGE_ROOT,
    manifest_name: str = SKILL_MANIFEST_NAME,
) -> dict[str, Any]:
    skill_root = (root / skill_package_root).resolve()
    packages: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    if skill_root.is_dir():
        manifest_paths = sorted(
            skill_root.glob(f"*/{manifest_name}"),
            key=lambda path: path.relative_to(root).as_posix(),
        )
        for manifest_path in manifest_paths:
            skill_dir = manifest_path.parent
            manifest = load_skill_package_manifest(skill_dir, manifest_name=manifest_name)
            if manifest is None:
                continue
            errors = validate_skill_package_manifest(skill_dir, manifest, manifest_name=manifest_name)
            if errors:
                raise ValueError("; ".join(errors))

            package_id = str(manifest["id"])
            if package_id in seen_ids:
                raise ValueError(f"duplicate skill package id in snapshot: {package_id}")
            seen_ids.add(package_id)

            packages.append(
                {
                    "id": package_id,
                    "version": manifest["version"],
                    "content_digest": manifest["content_digest"],
                    "entry_ref": manifest["entry_ref"],
                    "manifest_ref": manifest_path.relative_to(root).as_posix(),
                    "lifecycle_status": manifest["lifecycle"]["status"],
                    "capabilities": manifest["capabilities"],
                    "trust_tier_hint": manifest.get("trust_tier_hint", "unverified"),
                    "depends": manifest.get("depends", []),
                }
            )

    packages.sort(key=lambda package: package["id"])
    snapshot = {
        "version": SKILL_REGISTRY_SNAPSHOT_VERSION,
        "generated_from": skill_package_root.replace("\\", "/"),
        "packages": packages,
    }
    snapshot["snapshot_digest"] = _stable_json_digest(snapshot)
    return snapshot


def resolve_skill_lockfile(snapshot: dict[str, Any], requested_ids: list[str]) -> dict[str, Any]:
    if not requested_ids:
        raise ValueError("requested skill ids must not be empty")
    canonical_requested = sorted({requested_id for requested_id in requested_ids if requested_id})
    if not canonical_requested:
        raise ValueError("requested skill ids must not be empty")

    packages = snapshot.get("packages", [])
    if not isinstance(packages, list):
        raise ValueError("snapshot packages must be a list")

    package_map: dict[str, dict[str, Any]] = {}
    for package in packages:
        package_id = package.get("id")
        if not isinstance(package_id, str) or not package_id.strip():
            raise ValueError("snapshot package id must be a non-empty string")
        if package_id in package_map:
            raise ValueError(f"duplicate skill package id in snapshot: {package_id}")
        package_map[package_id] = package

    resolved_ids: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(package_id: str) -> None:
        if package_id in visited:
            return
        if package_id in visiting:
            raise ValueError(f"cyclic skill dependency detected: {package_id}")

        package = package_map.get(package_id)
        if package is None:
            raise ValueError(f"requested or dependent skill not found in snapshot: {package_id}")

        visiting.add(package_id)
        dependencies = package.get("depends", [])
        if not isinstance(dependencies, list):
            raise ValueError(f"{package_id}: depends must be a list in snapshot")

        for dependency in dependencies:
            if not isinstance(dependency, dict):
                raise ValueError(f"{package_id}: dependency entry must be an object")
            if not dependency.get("required", False):
                continue
            dependency_id = dependency.get("id")
            if not isinstance(dependency_id, str) or not dependency_id.strip():
                raise ValueError(f"{package_id}: dependency id must be a non-empty string")
            target = package_map.get(dependency_id)
            if target is None:
                raise ValueError(f"{package_id}: missing required dependency {dependency_id}")
            version_range = dependency.get("version_range")
            if not _string_or_string_list(version_range):
                raise ValueError(f"{package_id}: dependency {dependency_id} has invalid version_range")
            if not version_satisfies_range(str(target["version"]), version_range):
                raise ValueError(
                    f"{package_id}: dependency {dependency_id} version {target['version']} does not satisfy {version_range}"
                )
            visit(dependency_id)

        visiting.remove(package_id)
        visited.add(package_id)
        resolved_ids.append(package_id)

    for requested_id in canonical_requested:
        visit(requested_id)

    resolved = []
    for package_id in sorted(resolved_ids):
        package = package_map[package_id]
        depends_on = [
            dependency["id"]
            for dependency in package.get("depends", [])
            if isinstance(dependency, dict) and dependency.get("required", False)
        ]
        resolved.append(
            {
                "id": package["id"],
                "version": package["version"],
                "content_digest": package["content_digest"],
                "entry_ref": package["entry_ref"],
                "manifest_ref": package["manifest_ref"],
                "depends_on": sorted(depends_on),
            }
        )

    return {
        "version": SKILL_LOCKFILE_VERSION,
        "source_snapshot": {
            "generated_from": snapshot.get("generated_from"),
            "snapshot_digest": snapshot.get("snapshot_digest"),
            "package_count": len(packages),
        },
        "requested": canonical_requested,
        "resolved": resolved,
    }


def _base_effective_policy(trust_tier: str) -> dict[str, Any]:
    return {
        "files": {"read_scopes": [], "write_scopes": []},
        "network": {"mode": "disabled", "allowed_hosts": []},
        "shell": {"allowed": False, "profiles": []},
        "connectors": {"allowed_ids": [], "mcp_servers": []},
        "budget": dict(TRUST_TIER_BUDGET_DEFAULTS[trust_tier]),
    }


def _apply_capability_to_policy(policy: dict[str, Any], capability: str) -> None:
    if capability == "read_repo":
        policy["files"]["read_scopes"] = _dedupe_sorted_strings(policy["files"]["read_scopes"] + ["repo"])
        return
    if capability == "read_docs":
        policy["files"]["read_scopes"] = _dedupe_sorted_strings(policy["files"]["read_scopes"] + ["docs"])
        return
    if capability == "write_docs":
        policy["files"]["write_scopes"] = _dedupe_sorted_strings(policy["files"]["write_scopes"] + ["docs"])
        return
    if capability == "run_shell":
        policy["shell"]["allowed"] = True
        policy["shell"]["profiles"] = _dedupe_sorted_strings(policy["shell"]["profiles"] + ["sandboxed"])
        return
    if capability == "invoke_search":
        policy["network"]["mode"] = "allowlist"
        policy["network"]["allowed_hosts"] = _dedupe_sorted_strings(policy["network"]["allowed_hosts"] + ["search"])
        return
    if capability == "invoke_connector":
        policy["connectors"]["allowed_ids"] = _dedupe_sorted_strings(policy["connectors"]["allowed_ids"] + ["*"])
        policy["connectors"]["mcp_servers"] = _dedupe_sorted_strings(policy["connectors"]["mcp_servers"] + ["*"])


def resolve_skill_execution_policy(
    snapshot: dict[str, Any],
    requested_ids: list[str],
    runtime: str,
    target_skill_id: str,
    *,
    repository_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if runtime not in VALID_POLICY_RUNTIMES:
        raise ValueError(f"unsupported runtime for execution policy: {runtime}")

    lockfile = resolve_skill_lockfile(snapshot, requested_ids)
    packages = snapshot.get("packages", [])
    package_map = {
        str(package.get("id")): package
        for package in packages
        if isinstance(package, dict) and isinstance(package.get("id"), str)
    }
    package = package_map.get(target_skill_id)
    if package is None:
        raise ValueError(f"target skill not found in snapshot: {target_skill_id}")

    trust_tier = str(package.get("trust_tier_hint", "unverified"))
    if trust_tier not in VALID_TRUST_TIERS:
        raise ValueError(f"{target_skill_id}: invalid trust tier {trust_tier}")

    requested_capabilities = package.get("capabilities", [])
    if not _string_list(requested_capabilities):
        raise ValueError(f"{target_skill_id}: capabilities must be a list of strings")

    deny_capabilities = repository_policy.get("deny_capabilities", []) if repository_policy else []
    if deny_capabilities and not _string_list(deny_capabilities):
        raise ValueError("repository_policy.deny_capabilities must be a list of strings")

    supported_capabilities = RUNTIME_CAPABILITY_SUPPORT[runtime]
    for capability in requested_capabilities:
        if capability not in supported_capabilities:
            raise ValueError(f"{target_skill_id}: runtime {runtime} cannot safely map capability {capability}")

    effective_capabilities = [
        capability
        for capability in requested_capabilities
        if capability in TRUST_TIER_CAPABILITY_ALLOWLIST[trust_tier] and capability not in set(deny_capabilities)
    ]
    policy = _base_effective_policy(trust_tier)
    for capability in effective_capabilities:
        _apply_capability_to_policy(policy, capability)

    resolved_entry = next((entry for entry in lockfile["resolved"] if entry["id"] == target_skill_id), None)
    if resolved_entry is None:
        raise ValueError(f"target skill not found in resolved lockfile: {target_skill_id}")

    return {
        "version": SKILL_POLICY_VERSION,
        "skill": {
            "id": resolved_entry["id"],
            "version": resolved_entry["version"],
            "content_digest": resolved_entry["content_digest"],
        },
        "source_lockfile": {
            "snapshot_digest": lockfile["source_snapshot"]["snapshot_digest"],
            "lockfile_version": lockfile["version"],
        },
        "trust_tier": trust_tier,
        "effective_policy": policy,
        "backend": {
            "runtime": runtime,
            "adapter_version": 1,
            "fail_closed_on_unmapped": True,
        },
    }


def assert_policy_allows_action(policy_artifact: dict[str, Any], category: str, action: str) -> None:
    effective_policy = policy_artifact.get("effective_policy", {})
    if category == "shell" and action == "execute":
        if effective_policy.get("shell", {}).get("allowed", False):
            return
        raise PermissionError("shell action not allowed by resolved policy")
    if category == "network" and action == "access":
        if effective_policy.get("network", {}).get("mode") != "disabled":
            return
        raise PermissionError("network action not allowed by resolved policy")
    if category == "connectors" and action == "invoke":
        connectors = effective_policy.get("connectors", {})
        if connectors.get("allowed_ids") or connectors.get("mcp_servers"):
            return
        raise PermissionError("connector action not allowed by resolved policy")
    raise PermissionError(f"{category} action not allowed by resolved policy")


def _string_or_string_list(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def _validate_dependency_entries(entries: Any, errors: list[str], skill_name: str) -> None:
    if not isinstance(entries, list):
        errors.append(f"{skill_name}: depends must be a list")
        return
    required_fields = {"id", "version_range", "required", "reason"}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"{skill_name}: depends[{index}] must be an object")
            continue
        missing = required_fields - set(entry)
        if missing:
            errors.append(f"{skill_name}: depends[{index}] missing fields {sorted(missing)}")
            continue
        if not isinstance(entry["id"], str) or not entry["id"].strip():
            errors.append(f"{skill_name}: depends[{index}].id must be a non-empty string")
        if not _string_or_string_list(entry["version_range"]):
            errors.append(f"{skill_name}: depends[{index}].version_range must be a string or list of strings")
        if not isinstance(entry["required"], bool):
            errors.append(f"{skill_name}: depends[{index}].required must be a boolean")
        if not isinstance(entry["reason"], str) or not entry["reason"].strip():
            errors.append(f"{skill_name}: depends[{index}].reason must be a non-empty string")


def validate_skill_package_manifest(
    skill_dir: Path,
    manifest: dict[str, Any],
    *,
    manifest_name: str = SKILL_MANIFEST_NAME,
) -> list[str]:
    skill_name = skill_dir.name
    errors: list[str] = []
    missing = REQUIRED_SKILL_PACKAGE_FIELDS - set(manifest)
    if missing:
        errors.append(f"{skill_name}: manifest missing required fields {sorted(missing)}")
        return errors

    unknown = set(manifest) - REQUIRED_SKILL_PACKAGE_FIELDS - OPTIONAL_SKILL_PACKAGE_FIELDS
    if unknown:
        errors.append(f"{skill_name}: manifest contains unknown fields {sorted(unknown)}")

    if manifest.get("id") != skill_name:
        errors.append(f"{skill_name}: manifest id must match skill directory name")
    if not isinstance(manifest.get("name"), str) or not manifest["name"].strip():
        errors.append(f"{skill_name}: name must be a non-empty string")
    if not isinstance(manifest.get("description"), str) or not manifest["description"].strip():
        errors.append(f"{skill_name}: description must be a non-empty string")
    if not isinstance(manifest.get("version"), str) or not SEMVER_RE.match(manifest["version"]):
        errors.append(f"{skill_name}: version must be valid semantic versioning")
    if not _string_or_string_list(manifest.get("engine_range")):
        errors.append(f"{skill_name}: engine_range must be a string or list of strings")

    entry_ref = manifest.get("entry_ref")
    if not isinstance(entry_ref, str) or not entry_ref.strip():
        errors.append(f"{skill_name}: entry_ref must be a non-empty string")
    else:
        entry_path = (skill_dir / entry_ref).resolve()
        if not entry_path.is_file():
            errors.append(f"{skill_name}: entry_ref does not resolve to a file")

    capabilities = manifest.get("capabilities")
    if not _string_list(capabilities) or not capabilities:
        errors.append(f"{skill_name}: capabilities must be a non-empty list of strings")

    origin = manifest.get("origin")
    if not isinstance(origin, dict):
        errors.append(f"{skill_name}: origin must be an object")
    else:
        for field in ("publisher", "channel"):
            value = origin.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{skill_name}: origin.{field} must be a non-empty string")

    lifecycle = manifest.get("lifecycle")
    if not isinstance(lifecycle, dict):
        errors.append(f"{skill_name}: lifecycle must be an object")
    else:
        status = lifecycle.get("status")
        if status not in VALID_LIFECYCLE_STATES:
            errors.append(f"{skill_name}: lifecycle.status must be one of {sorted(VALID_LIFECYCLE_STATES)}")

    content_digest = manifest.get("content_digest")
    if not isinstance(content_digest, str) or not content_digest.startswith("sha256:"):
        errors.append(f"{skill_name}: content_digest must use the sha256:<hex> format")
    else:
        expected_digest = f"sha256:{package_content_hash(skill_dir, manifest_name)}"
        if content_digest != expected_digest:
            errors.append(f"{skill_name}: content_digest does not match current package contents")

    if "api_range" in manifest and not _string_or_string_list(manifest["api_range"]):
        errors.append(f"{skill_name}: api_range must be a string or list of strings")
    for list_field in ("optional_companions", "provides"):
        if list_field in manifest and not _string_list(manifest[list_field]):
            errors.append(f"{skill_name}: {list_field} must be a list of strings")
    for string_field in ("trust_tier_hint", "homepage", "docs_ref", "replacement", "changelog_ref"):
        if string_field in manifest:
            value = manifest[string_field]
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{skill_name}: {string_field} must be a non-empty string")
    trust_tier_hint = manifest.get("trust_tier_hint")
    if trust_tier_hint is not None and trust_tier_hint not in VALID_TRUST_TIERS:
        errors.append(f"{skill_name}: trust_tier_hint must be one of {sorted(VALID_TRUST_TIERS)}")
    if "signature" in manifest and not isinstance(manifest["signature"], dict):
        errors.append(f"{skill_name}: signature must be an object when present")
    if "depends" in manifest:
        _validate_dependency_entries(manifest["depends"], errors, skill_name)

    return errors


def validate_skill_manifest_authority(
    *,
    entry: dict[str, Any],
    summary: dict[str, Any],
    mirror: dict[str, Any],
    manifest: dict[str, Any],
    detail_path: Path,
) -> list[str]:
    errors: list[str] = []
    skill_id = entry["id"]
    mirror_meta = mirror.get("agentcortex", {})

    if summary.get("name") != manifest.get("id"):
        errors.append(f"{skill_id}: summary name must derive from manifest id")
    if summary.get("description") != manifest.get("description"):
        errors.append(f"{skill_id}: summary description must derive from manifest description")
    if mirror.get("display_name") != manifest.get("name"):
        errors.append(f"{skill_id}: mirror display_name must derive from manifest name")
    if mirror.get("short_description") != manifest.get("description"):
        errors.append(f"{skill_id}: mirror short_description must derive from manifest description")

    entry_ref = manifest.get("entry_ref")
    if isinstance(entry_ref, str):
        if Path(entry_ref).name != detail_path.name:
            errors.append(f"{skill_id}: manifest entry_ref must point at the registered detail file")
        if mirror_meta.get("detail_ref") and Path(str(mirror_meta["detail_ref"])).name != Path(entry_ref).name:
            errors.append(f"{skill_id}: mirror detail_ref must align with manifest entry_ref")

    return errors


def compact_detect_by(entry: dict[str, Any]) -> dict[str, Any]:
    detect_by = entry.get("detect_by", {})
    payload: dict[str, Any] = {}
    for key in ("classification", "intent_patterns", "scope_signals", "failure_signals", "phase_conditions"):
        values = detect_by.get(key)
        if values:
            payload[key] = values
    return payload


def compact_entry(entry: dict[str, Any], content_hash: str | None = None) -> dict[str, Any]:
    payload = {
        "id": entry["id"],
        "kind": entry["kind"],
        "platforms": entry["platforms"],
        "phase_scope": entry["phase_scope"],
        "detect_by": compact_detect_by(entry),
        "load_policy": entry["load_policy"],
    }
    if content_hash:
        payload["content_hash"] = content_hash
    return payload


def _build_summary(registry: dict[str, Any]) -> dict[str, Any]:
    """Build a flat skill-id -> load_policy/cost_risk/kind lookup for fast scanning."""
    summary: dict[str, Any] = {
        "_note": "READ THIS FIRST — scan this flat lookup before reading full entries below. Only read individual entries for skills you need to evaluate.",
    }
    for entry in registry.get("entries", []):
        entry_id = entry.get("id", "")
        summary[entry_id] = {
            "load_policy": entry.get("load_policy", "on-match"),
            "cost_risk": entry.get("cost_risk", "medium"),
            "kind": entry.get("kind", "skill"),
        }
    return summary


def build_compact_index(root: Path, registry_rel: str = DEFAULT_REGISTRY) -> dict[str, Any]:
    registry = load_registry(root, registry_rel)
    entries: list[dict[str, Any]] = []
    for entry in registry.get("entries", []):
        content_hash = None
        detail_ref = entry.get("detail_ref")
        if detail_ref:
            detail_path = (root / detail_ref).resolve()
            if detail_path.is_file():
                content_hash = stable_content_hash(detail_path)
        entries.append(compact_entry(entry, content_hash=content_hash))
    return {
        "version": 1,
        "generated_from": registry_rel.replace("\\", "/"),
        "registry_version": registry.get("version"),
        "_summary": _build_summary(registry),
        "entries": entries,
    }


def load_runtime_index(
    root: Path,
    compact_index_rel: str = DEFAULT_COMPACT_INDEX,
    registry_rel: str = DEFAULT_REGISTRY,
) -> tuple[dict[str, Any], str]:
    compact_path = (root / compact_index_rel).resolve()
    if compact_path.is_file():
        return load_json(compact_path), "compact-index"
    return build_compact_index(root, registry_rel=registry_rel), "registry-fallback"


def extract_markdown_sections(text: str, level: int) -> dict[str, str]:
    normalized = text.replace("\r\n", "\n")
    matches = list(re.finditer(rf"^(#{{{level}}})\s+(.*?)\s*$", normalized, re.MULTILINE))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.start()
        end = len(normalized)
        for next_match in matches[index + 1 :]:
            if len(next_match.group(1)) <= level:
                end = next_match.start()
                break
        sections[match.group(2).strip()] = normalized[start:end]
    return sections


def extract_skill_notes_text(worklog_text: str) -> str:
    return extract_markdown_sections(worklog_text, 2).get("Skill Notes", "")


def extract_skill_hash(skill_block: str) -> str | None:
    for raw_line in skill_block.splitlines():
        line = raw_line.strip()
        if line.startswith("- Content Hash:"):
            return line.split(":", 1)[1].strip() or None
        if line.startswith("- cached_hash:"):
            return line.split(":", 1)[1].strip() or None
    return None


def legacy_skill_phase_note_is_valid(skill_notes_text: str, skill_id: str, phase: str) -> bool:
    skill_blocks = extract_markdown_sections(skill_notes_text, 3)
    skill_block = skill_blocks.get(skill_id)
    if not skill_block:
        return False
    phase_blocks = extract_markdown_sections(skill_block, 4)
    phase_block = phase_blocks.get(phase)
    if not phase_block:
        return False
    lines = [line.strip() for line in phase_block.splitlines() if line.strip()]
    checklist_count = sum(line.startswith("- Checklist:") for line in lines)
    constraint_count = sum(line.startswith("- Constraint:") for line in lines)
    body = "\n".join(
        line.replace("- Checklist:", "", 1).replace("- Constraint:", "", 1).strip()
        for line in lines
        if line.startswith("- Checklist:") or line.startswith("- Constraint:")
    )
    return checklist_count >= 2 and constraint_count >= 1 and len("".join(body.split())) >= 50


def cache_decision(skill_notes_text: str, skill_id: str, phase: str, expected_hash: str | None) -> dict[str, str]:
    if not skill_notes_text.strip():
        return {"action": "read-skill", "reason": "missing-skill-notes"}

    skill_block = extract_markdown_sections(skill_notes_text, 3).get(skill_id)
    if not skill_block:
        return {"action": "read-skill", "reason": "missing-skill-block"}

    phase_valid = legacy_skill_phase_note_is_valid(skill_notes_text, skill_id, phase)
    cached_hash = extract_skill_hash(skill_block)

    if expected_hash and cached_hash:
        if cached_hash == expected_hash and phase_valid:
            return {"action": "use-cache", "reason": "hash-match"}
        if cached_hash != expected_hash:
            return {"action": "read-skill", "reason": "hash-mismatch"}

    if phase_valid:
        return {"action": "use-cache", "reason": "legacy-heuristic"}
    return {"action": "read-skill", "reason": "legacy-cache-miss"}


def phase_condition_matches(phase: str, condition: str) -> bool:
    phases = PHASE_CONDITION_MATCHERS.get(condition)
    return bool(phases and phase in phases)


def values_match(reference_values: list[str], actual_values: list[str]) -> bool:
    normalized_actual = [normalize_text(value) for value in actual_values if normalize_text(value)]
    normalized_reference = [normalize_text(value) for value in reference_values if normalize_text(value)]
    for actual in normalized_actual:
        actual_tokens = set(actual.split())
        for reference in normalized_reference:
            reference_tokens = set(reference.split())
            if actual == reference:
                return True
            if actual_tokens and reference_tokens and (actual_tokens.issubset(reference_tokens) or reference_tokens.issubset(actual_tokens)):
                return True
    return False


def classification_matches(entry: dict[str, Any], classification: str) -> bool:
    classes = entry.get("detect_by", {}).get("classification", [])
    return not classes or classification in classes


def platform_matches(entry: dict[str, Any], platform: str) -> bool:
    platforms = entry.get("platforms", [])
    return not platforms or platform in platforms


def skill_is_candidate(
    entry: dict[str, Any],
    *,
    classification: str,
    phase: str,
    platform: str,
    manual_skills: list[str],
    scope_signals: list[str],
    failure_signals: list[str],
) -> tuple[bool, dict[str, bool]]:
    # Classification and platform checks apply to BOTH auto and manual
    # activation.  AGENTS.md §5.4: "manual activation MUST still respect
    # the skill's Skip when column from the bootstrap rule table."  The
    # bootstrap rule table expresses skip rules via the classification
    # list in detect_by — if the current classification is not listed,
    # the skill is skipped even when manually requested.
    if not classification_matches(entry, classification):
        return False, {}
    if not platform_matches(entry, platform):
        return False, {}

    detect_by = entry.get("detect_by", {})
    matches = {
        "phase_scope": phase in entry.get("phase_scope", []),
        "phase_condition": any(phase_condition_matches(phase, condition) for condition in detect_by.get("phase_conditions", [])),
        "manual": values_match([entry["id"], *detect_by.get("intent_patterns", [])], manual_skills),
        "scope": values_match(detect_by.get("scope_signals", []), scope_signals),
        "failure": values_match(detect_by.get("failure_signals", []), failure_signals),
    }
    phase_ready = matches["phase_scope"] or matches["phase_condition"]
    is_candidate = matches["manual"] or phase_ready
    return is_candidate, matches


def skill_is_activated(
    entry: dict[str, Any],
    *,
    classification: str,
    phase: str,
    matches: dict[str, bool],
) -> bool:
    if entry["load_policy"] in {"always", "phase-entry"}:
        return (
            matches.get("phase_scope", False)
            or matches.get("phase_condition", False)
            or matches.get("manual", False)
            or matches.get("scope", False)
            or matches.get("failure", False)
        )
    if entry["load_policy"] == "on-failure":
        if entry["id"] == "systematic-debugging" and classification == "hotfix" and phase in {"implement", "review", "test", "ship"}:
            return True
        return matches.get("manual", False) or (
            (matches.get("phase_scope", False) or matches.get("phase_condition", False))
            and (matches.get("scope", False) or matches.get("failure", False))
        )
    return (
        matches.get("manual", False)
        or (
            (matches.get("phase_scope", False) or matches.get("phase_condition", False))
            and (matches.get("phase_condition", False) or matches.get("scope", False) or matches.get("failure", False))
        )
    )


def resolve_runtime_contract(
    root: Path,
    *,
    classification: str,
    phase: str,
    platform: str,
    manual_skills: list[str] | None = None,
    scope_signals: list[str] | None = None,
    failure_signals: list[str] | None = None,
    worklog_path: str | None = None,
    compact_index_rel: str = DEFAULT_COMPACT_INDEX,
    registry_rel: str = DEFAULT_REGISTRY,
) -> dict[str, Any]:
    manual_skills = manual_skills or []
    scope_signals = scope_signals or []
    failure_signals = failure_signals or []

    blockers: list[str] = []
    if classification not in VALID_CLASSIFICATIONS:
        blockers.append(f"invalid classification: {classification}")
    if phase not in VALID_PHASES:
        blockers.append(f"invalid phase: {phase}")

    resolved_workflow = PHASE_WORKFLOW_MAP.get(phase)
    if resolved_workflow and not (root / resolved_workflow).is_file():
        blockers.append(f"missing workflow file: {resolved_workflow}")

    index, index_source = load_runtime_index(root, compact_index_rel=compact_index_rel, registry_rel=registry_rel)
    worklog_text = ""
    if worklog_path:
        candidate = (root / worklog_path).resolve()
        if candidate.is_file():
            worklog_text = candidate.read_text(encoding="utf-8")
    skill_notes_text = extract_skill_notes_text(worklog_text)

    candidate_skills: list[dict[str, Any]] = []
    activated_skills: list[str] = []

    if not blockers:
        for entry in index.get("entries", []):
            if entry.get("kind") != "skill":
                continue
            is_candidate, match_flags = skill_is_candidate(
                entry,
                classification=classification,
                phase=phase,
                platform=platform,
                manual_skills=manual_skills,
                scope_signals=scope_signals,
                failure_signals=failure_signals,
            )
            if not is_candidate:
                continue

            activated = skill_is_activated(entry, classification=classification, phase=phase, matches=match_flags)
            cache = (
                cache_decision(skill_notes_text, entry["id"], phase, entry.get("content_hash"))
                if activated
                else {"action": "deferred", "reason": "not-activated"}
            )
            candidate_skills.append(
                {
                    "id": entry["id"],
                    "load_policy": entry["load_policy"],
                    "cache_action": cache["action"],
                    "cache_reason": cache["reason"],
                    "content_hash": entry.get("content_hash"),
                    "active": activated,
                }
            )
            if activated:
                activated_skills.append(entry["id"])

    receipt = {
        "platform": platform,
        "phase": phase,
        "resolved_workflow": resolved_workflow,
        "activated_skills": activated_skills,
        "cache": {entry["id"]: entry["cache_action"] for entry in candidate_skills if entry["active"]},
        "index_source": index_source,
    }

    return {
        "version": 1,
        "classification": classification,
        "phase": phase,
        "platform": platform,
        "resolved_workflow": resolved_workflow,
        "candidate_skills": candidate_skills,
        "activated_skills": activated_skills,
        "cache_source": "work-log-skill-notes" if skill_notes_text else "none",
        "index_source": index_source,
        "blockers": blockers,
        "receipt": receipt,
    }


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        parts = [part.strip() for part in re.split(r",(?![^\[]*\])", inner)]
        return [parse_scalar(part) for part in parts]
    if value.isdigit():
        return int(value)
    return value


def parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        container = stack[-1][1]
        key, sep, value = line.partition(":")
        if not sep:
            continue
        key = key.strip()
        value = value.strip()
        if not value:
            new_dict: dict[str, Any] = {}
            container[key] = new_dict
            stack.append((indent, new_dict))
            continue
        container[key] = parse_scalar(value)
    return root


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return parse_simple_yaml(parts[1])
