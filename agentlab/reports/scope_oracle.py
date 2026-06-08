from __future__ import annotations

from collections.abc import Mapping


def compact_scope_oracle_metadata(metadata: Mapping[str, object]) -> str:
    parts: list[str] = []
    consent_style = _nonempty_text(metadata.get("consent_style"))
    if consent_style is not None:
        parts.append(f"consent_style={consent_style}")

    allowed_paths = _path_list(metadata.get("allowed_paths"))
    if allowed_paths is not None:
        parts.append(f"allowed_paths={_format_path_list(allowed_paths)}")

    forbidden_paths = _path_list(metadata.get("forbidden_paths"))
    if forbidden_paths:
        parts.append(f"forbidden_paths={_format_path_list(forbidden_paths)}")

    return "; ".join(parts)


def _nonempty_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    if not text:
        return None
    return text


def _path_list(value: object) -> list[str] | None:
    if not isinstance(value, list):
        return None
    return [str(path) for path in value]


def _format_path_list(paths: list[str]) -> str:
    if not paths:
        return "(empty)"
    return ", ".join(paths)
