from __future__ import annotations

import contextlib
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from agentlab.runtime.model_identity import ModelIdentity, parse_model_name_from_events
from agentlab.runtime.run_surface import normalize_run_surface


LOCAL_CODEX_STATE_SOURCE = "local_codex_state"


@dataclass(frozen=True)
class CodexRuntimeMetadata:
    thread_id: str
    model_name: str | None = None
    reasoning_effort: str | None = None
    model_provider: str | None = None
    codex_thread_source: str | None = None
    cli_version: str | None = None


@dataclass(frozen=True)
class CodexRuntimeRecoveryEntry:
    result_path: Path
    status: str
    message: str
    thread_id: str | None = None
    model_name: str | None = None
    changed: bool = False
    error: bool = False


@dataclass(frozen=True)
class CodexRuntimeRecoverySummary:
    entries: list[CodexRuntimeRecoveryEntry]

    @property
    def changed_entries(self) -> list[CodexRuntimeRecoveryEntry]:
        return [entry for entry in self.entries if entry.changed]

    @property
    def error_entries(self) -> list[CodexRuntimeRecoveryEntry]:
        return [entry for entry in self.entries if entry.error]


def default_codex_state_db_path() -> Path:
    return Path.home() / ".codex" / "state_5.sqlite"


def parse_codex_thread_id_from_events(events_jsonl: str) -> str | None:
    for event in _iter_json_messages(events_jsonl):
        if event.get("type") != "thread.started":
            continue
        thread_id = _string_value(event, "thread_id")
        if thread_id:
            return thread_id
        thread_id = _string_value(event, "threadId")
        if thread_id:
            return thread_id
    return None


def lookup_codex_thread_metadata(
    codex_state_db: Path | str | None,
    thread_id: str | None,
) -> CodexRuntimeMetadata | None:
    if codex_state_db is None or not thread_id:
        return None

    state_db = Path(codex_state_db).expanduser()
    if not state_db.is_file():
        return None

    try:
        uri = state_db.resolve().as_uri() + "?mode=ro"
        with contextlib.closing(sqlite3.connect(uri, uri=True)) as connection:
            connection.row_factory = sqlite3.Row
            row = connection.execute(
                """
                select
                  id,
                  model,
                  reasoning_effort,
                  model_provider,
                  source,
                  cli_version
                from threads
                where id = ?
                """,
                (thread_id,),
            ).fetchone()
    except (OSError, sqlite3.Error, ValueError):
        return None

    if row is None:
        return None

    return CodexRuntimeMetadata(
        thread_id=str(row["id"]),
        model_name=_optional_str(row["model"]),
        reasoning_effort=_optional_str(row["reasoning_effort"]),
        model_provider=_optional_str(row["model_provider"]),
        codex_thread_source=_optional_str(row["source"]),
        cli_version=_optional_str(row["cli_version"]),
    )


def codex_model_identity_from_events_and_state(
    events_jsonl: str,
    *,
    requested_model_name: str | None = None,
    codex_state_db: Path | str | None = None,
) -> ModelIdentity:
    thread_id = parse_codex_thread_id_from_events(events_jsonl)
    event_model = parse_model_name_from_events(events_jsonl)
    metadata = lookup_codex_thread_metadata(codex_state_db, thread_id)
    if event_model:
        return ModelIdentity(
            model_name=event_model,
            model_source="events",
            requested_model_name=requested_model_name,
            reasoning_effort=metadata.reasoning_effort if metadata else None,
            model_provider=metadata.model_provider if metadata else None,
            codex_thread_id=thread_id,
            codex_thread_source=metadata.codex_thread_source if metadata else None,
            cli_version=metadata.cli_version if metadata else None,
        )

    if metadata is not None and metadata.model_name:
        return _identity_from_metadata(
            metadata,
            requested_model_name=requested_model_name,
        )

    if requested_model_name:
        return ModelIdentity(
            model_name=requested_model_name,
            model_source="explicit",
            requested_model_name=requested_model_name,
            codex_thread_id=thread_id,
        )

    return ModelIdentity(
        requested_model_name=requested_model_name,
        codex_thread_id=thread_id,
    )


def recover_codex_runtime_metadata(
    result_files: Iterable[Path],
    *,
    codex_state_db: Path | str,
    apply: bool = False,
) -> CodexRuntimeRecoverySummary:
    entries = [
        recover_codex_runtime_metadata_for_result(
            result_file,
            codex_state_db=codex_state_db,
            apply=apply,
        )
        for result_file in result_files
    ]
    return CodexRuntimeRecoverySummary(entries=entries)


def recover_codex_runtime_metadata_for_result(
    result_path: Path,
    *,
    codex_state_db: Path | str,
    apply: bool = False,
) -> CodexRuntimeRecoveryEntry:
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return CodexRuntimeRecoveryEntry(
            result_path=result_path,
            status="error",
            message=f"result.json is not valid JSON: {exc}",
            error=True,
        )
    except OSError as exc:
        return CodexRuntimeRecoveryEntry(
            result_path=result_path,
            status="error",
            message=f"could not read result.json: {exc}",
            error=True,
        )

    if not isinstance(result, dict):
        return CodexRuntimeRecoveryEntry(
            result_path=result_path,
            status="error",
            message="result.json must contain a JSON object",
            error=True,
        )

    run_dir = _result_run_dir(result, result_path)
    events_path = run_dir / "codex-events.jsonl"
    try:
        events_text = events_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return CodexRuntimeRecoveryEntry(
            result_path=result_path,
            status="skipped",
            message="codex-events.jsonl not found",
        )
    except OSError as exc:
        return CodexRuntimeRecoveryEntry(
            result_path=result_path,
            status="error",
            message=f"could not read codex-events.jsonl: {exc}",
            error=True,
        )

    current_config = _optional_dict(result.get("agent_harness_config")) or {}
    requested_model = _requested_model_name(result, current_config)
    identity = codex_model_identity_from_events_and_state(
        events_text,
        requested_model_name=requested_model,
        codex_state_db=codex_state_db,
    )

    if not identity.codex_thread_id:
        return CodexRuntimeRecoveryEntry(
            result_path=result_path,
            status="skipped",
            message="thread.started event did not include thread_id",
        )

    updated = _with_recovered_identity(result, identity)
    changed = updated != result
    if not changed:
        return CodexRuntimeRecoveryEntry(
            result_path=result_path,
            status="unchanged",
            message="runtime metadata already present",
            thread_id=identity.codex_thread_id,
            model_name=identity.model_name,
        )

    if apply:
        result_path.write_text(
            json.dumps(updated, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        status = "updated"
        message = "recovered runtime metadata written"
    else:
        status = "would_update"
        message = "runtime metadata would be written"

    return CodexRuntimeRecoveryEntry(
        result_path=result_path,
        status=status,
        message=message,
        thread_id=identity.codex_thread_id,
        model_name=identity.model_name,
        changed=True,
    )


def _identity_from_metadata(
    metadata: CodexRuntimeMetadata,
    *,
    requested_model_name: str | None,
) -> ModelIdentity:
    return ModelIdentity(
        model_name=metadata.model_name,
        model_source=LOCAL_CODEX_STATE_SOURCE,
        requested_model_name=requested_model_name,
        reasoning_effort=metadata.reasoning_effort,
        model_provider=metadata.model_provider,
        codex_thread_id=metadata.thread_id,
        codex_thread_source=metadata.codex_thread_source,
        cli_version=metadata.cli_version,
    )


def _with_recovered_identity(
    result: Mapping[str, Any],
    identity: ModelIdentity,
) -> dict[str, Any]:
    updated = dict(result)
    config = _optional_dict(updated.get("agent_harness_config")) or {}

    if identity.model_name:
        updated["model_name"] = identity.model_name
        config["model_name"] = identity.model_name
        config["model_source"] = identity.model_source
        config["requested_model_name"] = identity.requested_model_name

    if identity.codex_thread_id:
        config["codex_thread_id"] = identity.codex_thread_id
    if identity.reasoning_effort:
        config["reasoning_effort"] = identity.reasoning_effort
    if identity.model_provider:
        config["model_provider"] = identity.model_provider
    if identity.codex_thread_source:
        config["codex_thread_source"] = identity.codex_thread_source
    if identity.cli_version and not config.get("cli_version"):
        config["cli_version"] = identity.cli_version

    updated["agent_harness_config"] = config
    updated["run_surface"] = normalize_run_surface(
        _optional_dict(updated.get("run_surface")),
        agent_harness_config=config,
        agent_name=_optional_str(updated.get("agent_name")),
        status=_optional_str(updated.get("status")),
        success=updated.get("success")
        if isinstance(updated.get("success"), bool)
        else None,
        error=updated.get("error"),
    )
    return updated


def _result_run_dir(result: Mapping[str, Any], result_path: Path) -> Path:
    raw_run_dir = result.get("run_dir")
    if raw_run_dir:
        return Path(str(raw_run_dir))
    return result_path.parent


def _requested_model_name(
    result: Mapping[str, Any],
    config: Mapping[str, Any],
) -> str | None:
    requested = _optional_str(config.get("requested_model_name"))
    if requested is not None:
        return requested
    if config.get("model_source") == "explicit":
        return _optional_str(config.get("model_name"))
    return _optional_str(result.get("requested_model_name"))


def _iter_json_messages(events_jsonl: str) -> Iterable[dict[str, Any]]:
    for line in events_jsonl.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            yield event


def _optional_dict(value: object) -> dict[str, Any] | None:
    if isinstance(value, Mapping):
        return dict(value)
    return None


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _string_value(values: dict[str, Any], key: str) -> str | None:
    value = values.get(key)
    if isinstance(value, str) and value:
        return value
    return None
