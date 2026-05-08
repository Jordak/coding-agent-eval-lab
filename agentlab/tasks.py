from __future__ import annotations

import glob
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

from agentlab.taxonomy import FAILURE_LABELS

EVAL_TYPES = ["capability", "regression"]
TASK_BUNDLE_FILENAMES = ("task.yaml", "task.yml")


class TaskLoadError(ValueError):
    """Raised when a task file cannot be loaded or validated."""


@dataclass(frozen=True)
class SuccessCriteria:
    tests_must_pass: bool = True
    max_files_changed: Optional[int] = None


@dataclass(frozen=True)
class ReferenceArtifact:
    type: str
    path: Optional[str] = None
    commit: Optional[str] = None


@dataclass(frozen=True)
class EvalTask:
    id: str
    title: str
    repo: str
    commit: str
    language: str
    prompt: str
    suite: str = "default"
    eval_type: str = "capability"
    reference_solution: Optional[str] = None
    reference_artifact: Optional[ReferenceArtifact] = None
    setup: List[str] = field(default_factory=list)
    baseline: List[str] = field(default_factory=list)
    test: List[str] = field(default_factory=list)
    environment_path: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
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

        eval_type = str(mapping.get("eval_type", "capability"))
        if eval_type not in EVAL_TYPES:
            raise TaskLoadError(
                "eval_type must be one of: " + ", ".join(EVAL_TYPES)
            )

        return cls(
            id=str(mapping["id"]),
            title=str(mapping["title"]),
            repo=str(mapping["repo"]),
            commit=str(mapping["commit"]),
            language=str(mapping["language"]),
            prompt=str(mapping["prompt"]).strip(),
            suite=str(mapping.get("suite", "default")),
            eval_type=eval_type,
            reference_solution=_optional_string(
                mapping.get("reference_solution"),
                "reference_solution",
            ),
            reference_artifact=_reference_artifact(
                mapping.get("reference_artifact"),
                source_path,
            ),
            setup=_string_list(mapping.get("setup", []), "setup"),
            baseline=_string_list(mapping.get("baseline", []), "baseline"),
            test=_string_list(mapping.get("test", []), "test"),
            environment_path=_environment_path(
                mapping.get("environment_path", []),
                "environment_path",
            ),
            environment=_string_mapping(
                mapping.get("environment", {}),
                "environment",
            ),
            success=success,
            tags=_string_list(mapping.get("tags", []), "tags"),
            failure_modes=failure_modes,
            source_path=source_path,
        )


@dataclass(frozen=True)
class TaskBundle:
    task: EvalTask
    task_file: Path
    bundle_dir: Path
    suite_dir: Path
    task_card_path: Path


def discover_task_files(patterns: Iterable[str]) -> List[Path]:
    files: List[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        matches = sorted(Path(match) for match in glob.glob(pattern))
        candidates = matches if matches else [Path(pattern)]
        for candidate in candidates:
            for task_file in _task_files_for_candidate(candidate):
                resolved = task_file.resolve()
                if resolved not in seen:
                    files.append(task_file)
                    seen.add(resolved)

    return files


def discover_task_bundles(patterns: Iterable[str]) -> List[TaskBundle]:
    return [load_task_bundle(path) for path in discover_task_files(patterns)]


def load_task(path: str | Path) -> EvalTask:
    task_path = resolve_task_file(path)
    try:
        raw_text = task_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TaskLoadError(str(exc)) from exc

    mapping = load_task_mapping(raw_text)
    return EvalTask.from_mapping(mapping, source_path=task_path)


def load_task_bundle(path: str | Path) -> TaskBundle:
    task_path = resolve_task_file(path)
    task = load_task(task_path)
    bundle_dir = task_path.parent
    return TaskBundle(
        task=task,
        task_file=task_path,
        bundle_dir=bundle_dir,
        suite_dir=bundle_dir.parent,
        task_card_path=bundle_dir / "task-card.md",
    )


def resolve_task_file(path: str | Path) -> Path:
    task_path = Path(path)
    if task_path.is_dir():
        for filename in TASK_BUNDLE_FILENAMES:
            candidate = task_path / filename
            if candidate.is_file():
                return candidate
        raise TaskLoadError(f"task bundle is missing task.yaml: {task_path}")
    return task_path


def _task_files_for_candidate(candidate: Path) -> List[Path]:
    if candidate.is_file():
        return [candidate]
    if not candidate.is_dir():
        return []

    for filename in TASK_BUNDLE_FILENAMES:
        task_file = candidate / filename
        if task_file.is_file():
            return [task_file]

    task_files: List[Path] = []
    for filename in TASK_BUNDLE_FILENAMES:
        task_files.extend(sorted(candidate.glob(f"**/{filename}")))
    return task_files


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


def _environment_path(value: Any, field_name: str) -> List[str]:
    entries = _string_list(value, field_name)
    for entry in entries:
        _validate_relative_path(entry, field_name)
    return entries


def _string_mapping(value: Any, field_name: str) -> Dict[str, str]:
    if value is None:
        return {}
    mapping = _mapping(value, field_name)
    parsed: Dict[str, str] = {}
    for key, raw_value in mapping.items():
        if not isinstance(key, str) or not key:
            raise TaskLoadError(f"{field_name} keys must be non-empty strings")
        if raw_value is None or not isinstance(raw_value, (str, int, float)):
            raise TaskLoadError(f"{field_name}.{key} must be a scalar value")
        parsed[key] = str(raw_value)
    return parsed


def _optional_int(value: Any, field_name: str) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise TaskLoadError(f"{field_name} must be an integer") from exc


def _optional_string(value: Any, field_name: str) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    raise TaskLoadError(f"{field_name} must be a scalar string")


def _reference_artifact(
    value: Any,
    source_path: Optional[Path],
) -> Optional[ReferenceArtifact]:
    if value is None:
        return None
    mapping = _mapping(value, "reference_artifact")
    artifact_type = _required_string(
        mapping.get("type"),
        "reference_artifact.type",
    )
    if artifact_type == "patch":
        artifact_path = _required_string(
            mapping.get("path"),
            "reference_artifact.path",
        )
        _validate_relative_path(artifact_path, "reference_artifact.path")
        if source_path is not None and not (source_path.parent / artifact_path).is_file():
            raise TaskLoadError(
                f"reference_artifact.path does not exist: {artifact_path}"
            )
        return ReferenceArtifact(type=artifact_type, path=artifact_path)
    if artifact_type == "commit":
        return ReferenceArtifact(
            type=artifact_type,
            commit=_required_string(
                mapping.get("commit"),
                "reference_artifact.commit",
            ),
        )
    raise TaskLoadError("reference_artifact.type must be one of: patch, commit")


def _required_string(value: Any, field_name: str) -> str:
    parsed = _optional_string(value, field_name)
    if parsed is None or parsed == "":
        raise TaskLoadError(f"{field_name} is required")
    return parsed


def _validate_relative_path(value: str, field_name: str) -> None:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise TaskLoadError(f"{field_name} must be a relative path inside the bundle")
