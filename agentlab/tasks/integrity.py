from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List

from agentlab.tasks.reference import ReferenceVerification, verify_reference
from agentlab.tasks.cards import render_task_card
from agentlab.tasks import (
    TaskBundle,
    TaskLoadError,
    discover_task_files,
    load_task_bundle,
)


class TaskBundleIntegrityError(RuntimeError):
    """Raised when a loaded task bundle is not ready for a bundle-level workflow."""


@dataclass(frozen=True)
class TaskBundleIntegrityFailure:
    path: Path
    message: str


@dataclass(frozen=True)
class TaskBundleSourceValidationResult:
    matched_files: int
    bundles: List[TaskBundle]
    failures: List[TaskBundleIntegrityFailure] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures


@dataclass(frozen=True)
class TaskCardIntegrityCheck:
    bundle: TaskBundle
    path: Path
    expected_content: str
    drifted: bool


@dataclass(frozen=True)
class ReferenceReadinessCheck:
    bundle: TaskBundle
    ready: bool
    message: str


@dataclass(frozen=True)
class SmokeTestReadinessCheck:
    bundle: TaskBundle
    reference: ReferenceReadinessCheck

    @property
    def ready(self) -> bool:
        return self.reference.ready


@dataclass(frozen=True)
class TaskBundleIntegrityResult:
    source: TaskBundleSourceValidationResult
    task_card_changes: List[Path] = field(default_factory=list)
    reference_failures: List[TaskBundleIntegrityFailure] = field(default_factory=list)

    @property
    def matched_files(self) -> int:
        return self.source.matched_files

    @property
    def bundles(self) -> List[TaskBundle]:
        return self.source.bundles

    @property
    def failures(self) -> List[TaskBundleIntegrityFailure]:
        return self.source.failures + self.reference_failures

    @property
    def ok(self) -> bool:
        return not self.failures and not self.task_card_changes


@dataclass(frozen=True)
class TaskCardPublicationResult:
    matched_bundles: int
    changed_paths: List[Path]
    failures: List[TaskBundleIntegrityFailure] = field(default_factory=list)


def validate_task_bundle_sources(
    paths: Iterable[str],
) -> TaskBundleSourceValidationResult:
    files = discover_task_files(paths)
    bundles: List[TaskBundle] = []
    failures: List[TaskBundleIntegrityFailure] = []

    for path in files:
        try:
            bundles.append(load_task_bundle(path))
        except TaskLoadError as exc:
            failures.append(TaskBundleIntegrityFailure(path=Path(path), message=str(exc)))

    return TaskBundleSourceValidationResult(
        matched_files=len(files),
        bundles=bundles,
        failures=failures,
    )


def check_task_bundle_integrity(
    paths: Iterable[str],
    *,
    check_task_cards: bool = False,
    require_reference_artifacts: bool = False,
) -> TaskBundleIntegrityResult:
    source = validate_task_bundle_sources(paths)
    task_card_changes: List[Path] = []
    reference_failures: List[TaskBundleIntegrityFailure] = []

    for bundle in source.bundles:
        if check_task_cards:
            card = check_task_card(bundle)
            if card.drifted:
                task_card_changes.append(card.path)

        if require_reference_artifacts:
            readiness = check_reference_artifact_ready(bundle)
            if not readiness.ready:
                reference_failures.append(
                    TaskBundleIntegrityFailure(
                        path=bundle.task_file,
                        message=readiness.message,
                    )
                )

    return TaskBundleIntegrityResult(
        source=source,
        task_card_changes=task_card_changes,
        reference_failures=reference_failures,
    )


def check_task_card(bundle: TaskBundle) -> TaskCardIntegrityCheck:
    expected = render_task_card(bundle)
    current = (
        bundle.task_card_path.read_text(encoding="utf-8")
        if bundle.task_card_path.exists()
        else None
    )
    return TaskCardIntegrityCheck(
        bundle=bundle,
        path=bundle.task_card_path,
        expected_content=expected,
        drifted=current != expected,
    )


def publish_task_cards(
    paths: Iterable[str],
    *,
    check: bool = False,
) -> TaskCardPublicationResult:
    source = validate_task_bundle_sources(paths)
    if source.failures:
        return TaskCardPublicationResult(
            matched_bundles=len(source.bundles),
            changed_paths=[],
            failures=source.failures,
        )

    changed: List[Path] = []

    for bundle in source.bundles:
        card = check_task_card(bundle)
        if not card.drifted:
            continue
        if not check:
            card.path.write_text(card.expected_content, encoding="utf-8")
        changed.append(card.path)

    return TaskCardPublicationResult(
        matched_bundles=len(source.bundles),
        changed_paths=changed,
        failures=source.failures,
    )


def check_reference_artifact_ready(bundle: TaskBundle) -> ReferenceReadinessCheck:
    artifact = bundle.task.reference_artifact
    if artifact is None:
        return ReferenceReadinessCheck(
            bundle=bundle,
            ready=False,
            message=f"task has no reference_artifact: {bundle.task.id}",
        )

    if artifact.type == "patch":
        if not artifact.path:
            return ReferenceReadinessCheck(
                bundle=bundle,
                ready=False,
                message="patch reference artifact is missing path",
            )
        if not (bundle.bundle_dir / artifact.path).is_file():
            return ReferenceReadinessCheck(
                bundle=bundle,
                ready=False,
                message=f"reference_artifact.path does not exist: {artifact.path}",
            )
        return ReferenceReadinessCheck(
            bundle=bundle,
            ready=True,
            message="reference_artifact ready",
        )

    if artifact.type == "commit":
        if not artifact.commit:
            return ReferenceReadinessCheck(
                bundle=bundle,
                ready=False,
                message="commit reference artifact is missing commit",
            )
        return ReferenceReadinessCheck(
            bundle=bundle,
            ready=True,
            message="reference_artifact ready",
        )

    return ReferenceReadinessCheck(
        bundle=bundle,
        ready=False,
        message=f"unsupported reference artifact type: {artifact.type}",
    )


def check_smoke_test_readiness(bundle: TaskBundle) -> SmokeTestReadinessCheck:
    return SmokeTestReadinessCheck(
        bundle=bundle,
        reference=check_reference_artifact_ready(bundle),
    )


def require_reference_artifact(bundle: TaskBundle) -> None:
    readiness = check_reference_artifact_ready(bundle)
    if not readiness.ready:
        raise TaskBundleIntegrityError(readiness.message)


def load_smoke_test_ready_bundle(path: str | Path) -> TaskBundle:
    bundle = load_task_bundle(path)
    readiness = check_smoke_test_readiness(bundle)
    if not readiness.ready:
        raise TaskBundleIntegrityError(readiness.reference.message)
    return bundle


def verify_reference_for_bundle(
    bundle: TaskBundle,
    workspace_root: Path,
    *,
    write_artifacts: bool = False,
) -> ReferenceVerification:
    require_reference_artifact(bundle)
    return verify_reference(
        bundle.task,
        workspace_root,
        write_artifacts=write_artifacts,
    )
