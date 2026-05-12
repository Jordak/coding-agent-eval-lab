from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Dict

from agentlab.agent_harness_config import normalize_agent_harness_config
from agentlab.model_identity import model_identity_from_events
from agentlab.patches import count_patch_lines
from agentlab.resource_usage import (
    ResourceUsage,
    parse_resource_usage_events,
    resource_usage_to_dict,
)


def apply_result_backfills(data: Dict[str, Any], run_dir: Path | None) -> None:
    """Apply read-time compatibility fixes for historical result artifacts."""
    _backfill_edit_size(data, run_dir)
    _backfill_resource_usage(data, run_dir)
    _backfill_model_identity(data, run_dir)
    _backfill_agent_harness_config(data)


def _backfill_edit_size(data: Dict[str, Any], run_dir: Path | None) -> None:
    outcome = data.get("outcome")
    if isinstance(outcome, Mapping):
        if "files_changed" not in data and isinstance(
            outcome.get("files_changed"),
            list,
        ):
            data["files_changed"] = list(outcome.get("files_changed") or [])
        if "lines_added" not in data and outcome.get("lines_added") is not None:
            data["lines_added"] = outcome.get("lines_added")
        if "lines_deleted" not in data and outcome.get("lines_deleted") is not None:
            data["lines_deleted"] = outcome.get("lines_deleted")
        if (
            "n_files_changed" not in data
            and outcome.get("n_files_changed") is not None
        ):
            data["n_files_changed"] = outcome.get("n_files_changed")

    needs_patch = (
        "files_changed" not in data
        or "lines_added" not in data
        or "lines_deleted" not in data
    )
    if needs_patch:
        patch_text = _patch_text(data, run_dir)
        if patch_text is not None:
            if "files_changed" not in data:
                data["files_changed"] = _patch_files_changed(patch_text)
            stats = count_patch_lines(patch_text)
            data.setdefault("lines_added", stats.lines_added)
            data.setdefault("lines_deleted", stats.lines_deleted)

    data.setdefault("files_changed", [])
    data.setdefault("lines_added", 0)
    data.setdefault("lines_deleted", 0)
    data.setdefault(
        "n_files_changed",
        _files_changed_count(data, _files_changed(data)),
    )


def _backfill_resource_usage(data: Dict[str, Any], run_dir: Path | None) -> None:
    resource_usage = data.get("resource_usage")
    if not isinstance(resource_usage, Mapping):
        resource_usage = {}

    if not resource_usage:
        event_usage = _resource_usage_from_events(run_dir)
        if event_usage is not None:
            resource_usage = resource_usage_to_dict(event_usage)

    for key in [
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "cost_usd",
    ]:
        data.setdefault(key, resource_usage.get(key))

    usage = ResourceUsage(
        input_tokens=_optional_int(data.get("input_tokens")),
        cached_input_tokens=_optional_int(data.get("cached_input_tokens")),
        output_tokens=_optional_int(data.get("output_tokens")),
        reasoning_output_tokens=_optional_int(data.get("reasoning_output_tokens")),
        cost_usd=_optional_float(data.get("cost_usd")),
    )
    data["resource_usage"] = resource_usage_to_dict(usage)


def _backfill_model_identity(data: Dict[str, Any], run_dir: Path | None) -> None:
    events_text = _model_events_text(run_dir)
    if events_text is None:
        return

    config = _optional_dict(data.get("agent_harness_config")) or {}
    requested_model = _requested_model_name(data, config)
    identity = model_identity_from_events(
        events_text,
        requested_model_name=requested_model,
    )
    if not identity.model_name:
        return

    data["model_name"] = identity.model_name
    config["model_name"] = identity.model_name
    config["model_source"] = identity.model_source
    config["requested_model_name"] = identity.requested_model_name
    data["agent_harness_config"] = config


def _backfill_agent_harness_config(data: Dict[str, Any]) -> None:
    data["agent_harness_config"] = normalize_agent_harness_config(
        _optional_dict(data.get("agent_harness_config")),
        agent_name=_optional_str(data.get("agent_name")),
        model_name=_optional_str(data.get("model_name")),
        cost_usd=_optional_float(data.get("cost_usd")),
    )


def _requested_model_name(
    data: Mapping[str, Any],
    config: Mapping[str, Any],
) -> str | None:
    requested = _optional_str(config.get("requested_model_name"))
    if requested is not None:
        return requested
    if config.get("model_source") == "explicit":
        return _optional_str(config.get("model_name"))
    return _optional_str(data.get("requested_model_name"))


def _model_events_text(run_dir: Path | None) -> str | None:
    if run_dir is None:
        return None
    for filename in ["claude-events.jsonl", "codex-events.jsonl"]:
        path = run_dir / filename
        if not path.exists():
            continue
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return None
    return None


def _resource_usage_from_events(run_dir: Path | None) -> ResourceUsage | None:
    if run_dir is None:
        return None
    events_path = run_dir / "codex-events.jsonl"
    if not events_path.exists():
        return None
    try:
        usage = parse_resource_usage_events(events_path.read_text(encoding="utf-8"))
    except OSError:
        return None
    if usage.total_tokens is None and usage.cost_usd is None:
        return None
    return usage


def _patch_text(data: Mapping[str, Any], run_dir: Path | None) -> str | None:
    diff_path = _result_diff_path(data, run_dir)
    if diff_path is None or not diff_path.exists():
        return None
    try:
        return diff_path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _result_diff_path(
    data: Mapping[str, Any],
    run_dir: Path | None,
) -> Path | None:
    raw_path = data.get("diff_path")
    if not raw_path:
        raw_path = "diff.patch"
    diff_path = Path(str(raw_path))
    if diff_path.is_absolute():
        return diff_path
    if run_dir is None:
        return None
    return run_dir / diff_path


def _patch_files_changed(patch_text: str) -> list[str]:
    files: list[str] = []
    seen: set[str] = set()
    for line in patch_text.splitlines():
        path = None
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                path = _strip_git_prefix(parts[3])
        elif line.startswith("+++ ") and not line.startswith("+++ /dev/null"):
            path = _strip_git_prefix(line[4:].strip())

        if path and path not in seen:
            files.append(path)
            seen.add(path)
    return files


def _strip_git_prefix(path: str) -> str:
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path


def _files_changed(data: Mapping[str, Any]) -> list[str]:
    files = data.get("files_changed")
    if isinstance(files, list):
        return [str(path) for path in files]
    return []


def _files_changed_count(
    data: Mapping[str, Any],
    files_changed: list[str],
) -> int:
    raw_count = _optional_int(data.get("n_files_changed"))
    if raw_count is not None:
        return raw_count
    return len(files_changed)


def _optional_dict(value: object) -> Dict[str, Any] | None:
    if isinstance(value, Mapping):
        return dict(value)
    return None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _optional_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None
