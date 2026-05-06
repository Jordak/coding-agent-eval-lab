from __future__ import annotations

import glob
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from agentlab.taxonomy import FAILURE_LABELS


class TaskLoadError(ValueError):
    """Raised when a task file cannot be loaded or validated."""


@dataclass(frozen=True)
class SuccessCriteria:
    tests_must_pass: bool = True
    max_files_changed: Optional[int] = None


@dataclass(frozen=True)
class EvalTask:
    id: str
    title: str
    repo: str
    commit: str
    language: str
    prompt: str
    setup: List[str] = field(default_factory=list)
    baseline: List[str] = field(default_factory=list)
    test: List[str] = field(default_factory=list)
    success: SuccessCriteria = field(default_factory=SuccessCriteria)
    tags: List[str] = field(default_factory=list)
    failure_modes: List[str] = field(default_factory=list)
    source_path: Optional[Path] = None

    @classmethod
    def from_mapping(
        cls,
        mapping: Mapping[str, Any],
        source_path: Optional[Path] = None,
    ) -> "EvalTask":
        required = ["id", "title", "repo", "commit", "language", "prompt"]
        missing = [key for key in required if not _present(mapping.get(key))]
        if missing:
            raise TaskLoadError(f"missing required field(s): {', '.join(missing)}")

        success_mapping = _mapping(mapping.get("success", {}), "success")
        success = SuccessCriteria(
            tests_must_pass=bool(success_mapping.get("tests_must_pass", True)),
            max_files_changed=_optional_int(
                success_mapping.get("max_files_changed"),
                "success.max_files_changed",
            ),
        )

        failure_modes = _string_list(mapping.get("failure_modes", []), "failure_modes")
        invalid_failure_modes = [
            label for label in failure_modes if label not in FAILURE_LABELS
        ]
        if invalid_failure_modes:
            raise TaskLoadError(
                "failure_modes contains unknown label(s): "
                + ", ".join(invalid_failure_modes)
            )

        return cls(
            id=str(mapping["id"]),
            title=str(mapping["title"]),
            repo=str(mapping["repo"]),
            commit=str(mapping["commit"]),
            language=str(mapping["language"]),
            prompt=str(mapping["prompt"]).strip(),
            setup=_string_list(mapping.get("setup", []), "setup"),
            baseline=_string_list(mapping.get("baseline", []), "baseline"),
            test=_string_list(mapping.get("test", []), "test"),
            success=success,
            tags=_string_list(mapping.get("tags", []), "tags"),
            failure_modes=failure_modes,
            source_path=source_path,
        )


def discover_task_files(patterns: Iterable[str]) -> List[Path]:
    files: List[Path] = []
    for pattern in patterns:
        matches = sorted(Path(match) for match in glob.glob(pattern))
        if matches:
            files.extend(matches)
        else:
            files.append(Path(pattern))

    return [path for path in files if path.is_file()]


def load_task(path: str | Path) -> EvalTask:
    task_path = Path(path)
    try:
        raw_text = task_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TaskLoadError(str(exc)) from exc

    mapping = load_task_mapping(raw_text)
    return EvalTask.from_mapping(mapping, source_path=task_path)


def load_task_mapping(raw_text: str) -> Mapping[str, Any]:
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        parsed = _load_yaml(raw_text)

    if not isinstance(parsed, Mapping):
        raise TaskLoadError("task file must contain a mapping/object")

    return parsed


def _load_yaml(raw_text: str) -> Mapping[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError:
        return _load_yaml_subset(raw_text)

    parsed = yaml.safe_load(raw_text)
    if parsed is None:
        return {}
    return parsed


def _load_yaml_subset(raw_text: str) -> Dict[str, Any]:
    lines = raw_text.splitlines()
    result: Dict[str, Any] = {}
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue

        indent = _indent_of(line)
        if indent != 0:
            raise TaskLoadError(f"unexpected indentation on line {index + 1}")

        key, rest = _split_key_value(stripped, index + 1)
        if rest in {">", "|"}:
            value, index = _parse_block_scalar(lines, index + 1, rest)
        elif rest == "":
            value, index = _parse_indented_value(lines, index + 1)
        else:
            value = _parse_scalar(rest)
            index += 1

        result[key] = value

    return result


def _parse_indented_value(lines: List[str], index: int) -> tuple[Any, int]:
    while index < len(lines) and not lines[index].strip():
        index += 1

    if index >= len(lines):
        return None, index

    line = lines[index]
    indent = _indent_of(line)
    if indent == 0:
        return None, index

    stripped = line.strip()
    if stripped.startswith("- "):
        values: List[Any] = []
        while index < len(lines):
            current = lines[index]
            current_stripped = current.strip()
            if not current_stripped:
                index += 1
                continue
            if _indent_of(current) < indent or _indent_of(current) == 0:
                break
            if _indent_of(current) != indent or not current_stripped.startswith("- "):
                raise TaskLoadError(f"unsupported list syntax on line {index + 1}")
            values.append(_parse_scalar(current_stripped[2:].strip()))
            index += 1
        return values, index

    values_dict: Dict[str, Any] = {}
    while index < len(lines):
        current = lines[index]
        current_stripped = current.strip()
        if not current_stripped:
            index += 1
            continue
        if _indent_of(current) < indent or _indent_of(current) == 0:
            break
        if _indent_of(current) != indent:
            raise TaskLoadError(f"unsupported nested mapping syntax on line {index + 1}")
        key, rest = _split_key_value(current_stripped, index + 1)
        values_dict[key] = _parse_scalar(rest)
        index += 1

    return values_dict, index


def _parse_block_scalar(
    lines: List[str],
    index: int,
    style: str,
) -> tuple[str, int]:
    block_lines: List[str] = []
    block_indent: Optional[int] = None

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            block_lines.append("")
            index += 1
            continue

        indent = _indent_of(line)
        if indent == 0:
            break
        if block_indent is None:
            block_indent = indent
        if indent < block_indent:
            break
        block_lines.append(line[block_indent:])
        index += 1

    if style == ">":
        return " ".join(part.strip() for part in block_lines if part.strip()), index
    return "\n".join(block_lines), index


def _split_key_value(line: str, line_number: int) -> tuple[str, str]:
    if ":" not in line:
        raise TaskLoadError(f"expected key/value pair on line {line_number}")
    key, value = line.split(":", 1)
    key = key.strip()
    if not key:
        raise TaskLoadError(f"empty key on line {line_number}")
    return key, value.strip()


def _parse_scalar(value: str) -> Any:
    if value == "":
        return ""

    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none", "~"}:
        return None

    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]

    try:
        return int(value)
    except ValueError:
        return value


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _present(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TaskLoadError(f"{field_name} must be a mapping/object")
    return value


def _string_list(value: Any, field_name: str) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise TaskLoadError(f"{field_name} must be a list")
    if not all(isinstance(item, (str, int, float)) for item in value):
        raise TaskLoadError(f"{field_name} must contain only scalar values")
    return [str(item) for item in value]


def _optional_int(value: Any, field_name: str) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise TaskLoadError(f"{field_name} must be an integer") from exc
