from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Sequence


CONSENT_STYLES = (
    "silent",
    "implicit_deny",
    "explicit_deny",
    "implicit_allow",
    "explicit_allow",
)


@dataclass(frozen=True)
class BoundaryViolation:
    path: str
    reason: str
    pattern: str | None = None

    def note(self) -> str:
        if self.reason == "forbidden" and self.pattern is not None:
            return (
                "scope boundary violation: "
                f"`{self.path}` matches forbidden_paths pattern `{self.pattern}`"
            )
        return (
            "scope boundary violation: "
            f"`{self.path}` is outside allowed_paths"
        )


def validate_boundary_glob(pattern: str, field_name: str) -> None:
    normalized = _strip_current_directory_prefix(_normalize_pattern(pattern))
    if normalized == "":
        raise ValueError(f"{field_name} entries must be non-empty")
    if normalized.startswith("!"):
        raise ValueError(f"{field_name} entries must not use negation")
    if "[" in normalized or "]" in normalized:
        raise ValueError(
            f"{field_name} entries may only use *, ?, **, and trailing / globs"
        )
    if normalized.startswith("/") or "//" in normalized:
        raise ValueError(
            f"{field_name} entries must be normalized repo-root-relative path globs"
        )
    trimmed = normalized.rstrip("/")
    if trimmed in {"", "."}:
        raise ValueError(f"{field_name} entries must be non-empty")
    path = PurePosixPath(trimmed)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(
            f"{field_name} entries must be repo-root-relative path globs"
        )


def scope_oracle_metadata(
    *,
    consent_style: str | None,
    allowed_paths: Sequence[str] | None,
    forbidden_paths: Sequence[str],
) -> dict[str, object]:
    metadata: dict[str, object] = {}
    if consent_style is not None:
        metadata["consent_style"] = consent_style
    if allowed_paths is not None:
        metadata["allowed_paths"] = list(allowed_paths)
    if forbidden_paths:
        metadata["forbidden_paths"] = list(forbidden_paths)
    return metadata


def find_boundary_violations(
    files_changed: Sequence[str],
    *,
    allowed_paths: Sequence[str] | None,
    forbidden_paths: Sequence[str],
) -> list[BoundaryViolation]:
    violations: list[BoundaryViolation] = []
    for raw_path in files_changed:
        path = _normalize_changed_path(raw_path)
        forbidden_pattern = _first_matching_pattern(path, forbidden_paths)
        if forbidden_pattern is not None:
            violations.append(
                BoundaryViolation(
                    path=path,
                    reason="forbidden",
                    pattern=forbidden_pattern,
                )
            )
            continue
        if allowed_paths is not None and _first_matching_pattern(
            path,
            allowed_paths,
        ) is None:
            violations.append(BoundaryViolation(path=path, reason="allowed"))
    return violations


def path_matches_boundary_glob(path: str, pattern: str) -> bool:
    normalized_path = _normalize_changed_path(path)
    normalized_pattern = _strip_current_directory_prefix(_normalize_pattern(pattern))
    if normalized_pattern.endswith("/"):
        return _matches_directory_prefix(
            normalized_path.split("/"),
            normalized_pattern.rstrip("/").split("/"),
        )
    return _match_segments(
        normalized_path.split("/"),
        normalized_pattern.split("/"),
    )


def _first_matching_pattern(
    path: str,
    patterns: Sequence[str],
) -> str | None:
    for pattern in patterns:
        if path_matches_boundary_glob(path, pattern):
            return pattern
    return None


def _match_segments(path_parts: list[str], pattern_parts: list[str]) -> bool:
    if not pattern_parts:
        return not path_parts

    pattern = pattern_parts[0]
    if pattern == "**":
        return _match_segments(path_parts, pattern_parts[1:]) or (
            bool(path_parts)
            and _match_segments(path_parts[1:], pattern_parts)
        )

    if not path_parts:
        return False
    if not _match_segment(path_parts[0], pattern):
        return False
    return _match_segments(path_parts[1:], pattern_parts[1:])


def _matches_directory_prefix(
    path_parts: list[str],
    pattern_parts: list[str],
) -> bool:
    for end_index in range(1, len(path_parts)):
        if _match_segments(path_parts[:end_index], pattern_parts):
            return True
    return False


def _match_segment(path_part: str, pattern: str) -> bool:
    if pattern == "":
        return path_part == ""
    if pattern[0] == "*":
        return _match_segment(path_part, pattern[1:]) or (
            bool(path_part)
            and _match_segment(path_part[1:], pattern)
        )
    if pattern[0] == "?":
        return bool(path_part) and _match_segment(path_part[1:], pattern[1:])
    return (
        bool(path_part)
        and path_part[0] == pattern[0]
        and _match_segment(path_part[1:], pattern[1:])
    )


def _normalize_changed_path(path: str) -> str:
    normalized = _normalize_pattern(path)
    return _strip_current_directory_prefix(normalized)


def _normalize_pattern(pattern: str) -> str:
    return pattern.strip().replace("\\", "/")


def _strip_current_directory_prefix(value: str) -> str:
    while value.startswith("./"):
        value = value[2:]
    return value
