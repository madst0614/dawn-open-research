"""Deterministic, read-only projections of validated canonical research."""

from pathlib import PurePosixPath, PureWindowsPath
from urllib.parse import urlsplit

from .models import (
    Artifact,
    Claim,
    Method,
    Question,
    Relation,
    RepositoryRef,
    ResourceProfile,
    Result,
    Run,
    Source,
    Study,
)
from .resolver import readiness, resolve
from .revision import git_identity
from .store import validate_catalog


VIEW_VERSION = 1
GRAPH_GROUPS = (
    ("questions", Question),
    ("claims", Claim),
    ("methods", Method),
    ("results", Result),
    ("references", Source),
)


def _ensure_valid(catalog) -> None:
    errors = validate_catalog(catalog)
    if errors:
        raise ValueError("cannot generate a view from an invalid canonical catalog: " + "; ".join(errors))


def _record(obj) -> dict:
    return obj.model_dump(mode="json")


def _title(obj) -> str:
    return getattr(obj, "title", None) or getattr(obj, "name", None) or obj.id


def _human_kind(obj) -> str:
    if isinstance(obj, Source):
        return "Reference"
    if isinstance(obj, Relation):
        return "Connection"
    return type(obj).__name__


def _summary(obj) -> dict:
    value = {"id": obj.id, "kind": _human_kind(obj), "title": _title(obj)}
    if isinstance(obj, Study):
        value.update({"lifecycle": obj.lifecycle, "goal": obj.goal})
    elif isinstance(obj, Claim):
        value.update(
            {
                "status": obj.status,
                "claim_type": obj.claim_type,
                "statement": obj.statement,
                "scope": obj.scope,
            }
        )
    elif isinstance(obj, Question):
        value.update({"status": obj.status, "statement": obj.question})
    elif isinstance(obj, Method):
        value.update({"status": obj.status, "statement": obj.description})
    elif isinstance(obj, Result):
        value.update({"statement": obj.statement, "scope": obj.scope})
    elif isinstance(obj, Source):
        value.update({"source_type": obj.source_type, "statement": obj.source_statement})
    elif isinstance(obj, Relation):
        value.update(
            {
                "relation_class": obj.relation_class,
                "relation_type": obj.relation_type,
                "status": obj.status,
                "source_id": obj.source_id,
                "target_id": obj.target_id,
            }
        )
    elif isinstance(obj, Run):
        value.update(
            {
                "status": obj.status,
                "study_id": obj.study_id,
                "method_id": obj.method_id,
                "started_at": obj.started_at.isoformat(),
            }
        )
    else:
        for field in ("status", "availability"):
            if hasattr(obj, field):
                value[field] = getattr(obj, field)
    return value


def _study_refs(study: Study) -> set[str]:
    return set(
        study.question_ids
        + study.claim_ids
        + study.method_ids
        + study.requires.artifacts
        + study.profile_ids
    )


def _direct_studies(catalog, object_id: str) -> list[Study]:
    return sorted(
        [item for item in catalog.of_type(Study) if object_id in _study_refs(item)],
        key=lambda item: item.id,
    )


def _direct_runs(catalog, focus) -> list[Run]:
    run_ids = set()
    if isinstance(focus, Run):
        run_ids.add(focus.id)
    if isinstance(focus, Result):
        run_ids.update(focus.run_ids)
    for run in catalog.of_type(Run):
        if isinstance(focus, Study) and run.study_id == focus.id:
            run_ids.add(run.id)
        elif isinstance(focus, Method) and run.method_id == focus.id:
            run_ids.add(run.id)
        elif isinstance(focus, ResourceProfile) and run.profile_id == focus.id:
            run_ids.add(run.id)
        elif isinstance(focus, Artifact) and (
            focus.id in run.produced_artifact_ids
            or any(item.artifact_id == focus.id for item in run.input_artifacts)
        ):
            run_ids.add(run.id)
    return [catalog.get(run_id, Run) for run_id in sorted(run_ids)]


def _related_studies(catalog, focus) -> list[Study]:
    study_ids = {item.id for item in _direct_studies(catalog, focus.id)}
    study_ids.update(run.study_id for run in _direct_runs(catalog, focus))
    return [catalog.get(item, Study) for item in sorted(study_ids)]


def _study_results(catalog, study: Study) -> list[Result]:
    run_ids = {run.id for run in catalog.of_type(Run) if run.study_id == study.id}
    result_ids = {
        result.id for result in catalog.of_type(Result) if run_ids.intersection(result.run_ids)
    }
    research_ids = set(study.question_ids + study.claim_ids + study.method_ids)
    for relation in catalog.of_type(Relation):
        if relation.source_id in research_ids and isinstance(catalog.objects.get(relation.target_id), Result):
            result_ids.add(relation.target_id)
        if relation.target_id in research_ids and isinstance(catalog.objects.get(relation.source_id), Result):
            result_ids.add(relation.source_id)
    return [catalog.get(result_id, Result) for result_id in sorted(result_ids)]


def _relation_summary(catalog, relation: Relation, focus_id: str) -> dict:
    if relation.source_id == focus_id:
        direction, other_id = "outbound", relation.target_id
    else:
        direction, other_id = "inbound", relation.source_id
    return {
        "id": relation.id,
        "direction": direction,
        "relation_class": relation.relation_class,
        "relation_type": relation.relation_type,
        "status": relation.status,
        "other": _summary(catalog.get(other_id)),
    }


def _compact_unchecked(catalog, object_id: str) -> dict:
    focus = catalog.get(object_id)
    output = {"dor_view_version": VIEW_VERSION, "mode": "compact", "focus": _summary(focus)}
    if isinstance(focus, Study):
        state, blockers = readiness(catalog, focus)
        runs = _direct_runs(catalog, focus)
        latest = max(runs, key=lambda run: (run.started_at, run.id)) if runs else None
        output.update(
            {
                "state": {"lifecycle": focus.lifecycle, "readiness": state},
                "what_are_we_studying": focus.goal,
                "questions": [_summary(catalog.get(item, Question)) for item in sorted(focus.question_ids)],
                "claims": [_summary(catalog.get(item, Claim)) for item in sorted(focus.claim_ids)],
                "methods": [_summary(catalog.get(item, Method)) for item in sorted(focus.method_ids)],
                "results": [_summary(item) for item in _study_results(catalog, focus)],
                "latest_run": _summary(latest) if latest else None,
                "blockers": list(blockers),
                "next": {
                    "expected_outputs": list(focus.expected_outputs),
                    "completion_criteria": focus.completion_criteria,
                },
                "profiles": [
                    _summary(catalog.get(item, ResourceProfile)) for item in sorted(focus.profile_ids)
                ],
            }
        )
        return output

    connections = sorted(
        [
            item
            for item in catalog.of_type(Relation)
            if item.source_id == focus.id or item.target_id == focus.id
        ],
        key=lambda item: item.id,
    )
    output.update(
        {
            "connections": [_relation_summary(catalog, item, focus.id) for item in connections],
            "related_studies": [_summary(item) for item in _related_studies(catalog, focus)],
            "related_runs": [_summary(item) for item in _direct_runs(catalog, focus)],
        }
    )
    if isinstance(focus, Relation):
        output["endpoints"] = [
            _summary(catalog.get(focus.source_id)),
            _summary(catalog.get(focus.target_id)),
        ]
    return output


def _research_unchecked(catalog, object_id: str, export_safe: bool = False) -> dict:
    focus = catalog.get(object_id)
    selected_ids: set[str] = set()
    connection_ids: set[str] = set()
    study_ids: set[str] = set()
    run_ids: set[str] = set()

    if isinstance(focus, Study):
        study_ids.add(focus.id)
        selected_ids.update(focus.question_ids + focus.claim_ids + focus.method_ids)
        selected_ids.update(item.id for item in _study_results(catalog, focus))
        run_ids.update(run.id for run in catalog.of_type(Run) if run.study_id == focus.id)
    elif isinstance(focus, Relation):
        connection_ids.add(focus.id)
        selected_ids.update((focus.source_id, focus.target_id))
    else:
        selected_ids.add(focus.id)
        study_ids.update(item.id for item in _direct_studies(catalog, focus.id))
        run_ids.update(item.id for item in _direct_runs(catalog, focus))

    connection_seeds = set(selected_ids)
    for relation in sorted(catalog.of_type(Relation), key=lambda item: item.id):
        if (
            relation.id in connection_ids
            or relation.source_id in connection_seeds
            or relation.target_id in connection_seeds
        ):
            connection_ids.add(relation.id)
            selected_ids.update((relation.source_id, relation.target_id))

    provenance_source_ids = set()
    for selected_id in sorted(selected_ids):
        selected = catalog.get(selected_id)
        if isinstance(selected, Result):
            run_ids.update(selected.run_ids)
            provenance_source_ids.update(selected.source_ids)
    selected_ids.update(provenance_source_ids)

    for run_id in sorted(run_ids):
        run = catalog.get(run_id, Run)
        selected_ids.add(run.method_id)
        study_ids.add(run.study_id)

    groups = {name: [] for name, _ in GRAPH_GROUPS}
    other_objects = []
    for selected_id in sorted(selected_ids):
        selected = catalog.get(selected_id)
        matched = False
        for name, model in GRAPH_GROUPS:
            if isinstance(selected, model):
                groups[name].append(_export_record(selected) if export_safe else _record(selected))
                matched = True
                break
        if matched:
            continue
        if isinstance(selected, Study):
            study_ids.add(selected.id)
        elif isinstance(selected, Run):
            run_ids.add(selected.id)
        elif isinstance(selected, Relation):
            connection_ids.add(selected.id)
        else:
            other_objects.append(_export_record(selected) if export_safe else _record(selected))

    connections = [catalog.get(item, Relation) for item in sorted(connection_ids)]
    studies = [catalog.get(item, Study) for item in sorted(study_ids)]
    runs = [catalog.get(item, Run) for item in sorted(run_ids)]
    groups["connections"] = [
        _export_record(item) if export_safe else _record(item) for item in connections
    ]
    groups["other_objects"] = other_objects
    return {
        "dor_view_version": VIEW_VERSION,
        "mode": "research",
        "focus": _export_record(focus) if export_safe else _record(focus),
        "research": groups,
        "studies": [_export_record(item) if export_safe else _record(item) for item in studies],
        "runs": [_export_record(item) if export_safe else _record(item) for item in runs],
        "unresolved": {
            "limitations": [
                {"study_id": item.id, "items": list(item.known_limitations)}
                for item in studies
                if item.known_limitations
            ],
            "blockers": [
                {"study_id": item.id, "items": list(item.blockers)}
                for item in studies
                if item.blockers
            ],
        },
    }


def _execution_unchecked(catalog, object_id: str, profile: str | None = None) -> dict:
    focus = catalog.get(object_id)
    output = {"dor_view_version": VIEW_VERSION, "mode": "execution", "focus": _summary(focus)}
    if not isinstance(focus, Study):
        if profile:
            raise ValueError("--profile requires a Study focus")
        output.update({"applicable": False, "reason": "execution view is available only for Studies"})
        return output

    profile_keys = [profile] if profile else sorted(focus.profile_ids)
    plans = [resolve(catalog, focus.id, key) for key in profile_keys]
    missing = []
    if not profile_keys:
        missing.append("Study has no configured profile")
        if not focus.entrypoint:
            missing.append("Study has no entrypoint")
        if not focus.entrypoint_method_id:
            missing.append("Study has no executable Method")
    blockers = sorted(
        set(focus.blockers + missing + [item for plan in plans for item in plan["blockers"]])
    )
    output.update(
        {
            "applicable": True,
            "study": {"id": focus.id, "title": focus.title, "lifecycle": focus.lifecycle},
            "required_capabilities": sorted(set(focus.requires.capabilities)),
            "required_artifacts": list(focus.requires.artifacts),
            "entrypoint": focus.entrypoint,
            "executable_method": _summary(catalog.get(focus.entrypoint_method_id, Method))
            if focus.entrypoint_method_id
            else None,
            "configured_profiles": [
                _summary(catalog.get(item, ResourceProfile)) for item in sorted(focus.profile_ids)
            ],
            "resolutions": plans,
            "declared_blockers": list(focus.blockers),
            "blockers": blockers,
            "ready": any(plan["ready"] for plan in plans),
            "publicly_reproducible": any(plan["publicly_reproducible"] for plan in plans),
        }
    )
    return output


def _redact_paths(value):
    if isinstance(value, dict):
        return {key: _redact_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_paths(item) for item in value]
    if not isinstance(value, str):
        return value
    if value.lower().startswith("file:"):
        return "[private locator omitted]"
    if "://" in value:
        try:
            parsed = urlsplit(value)
        except ValueError:
            return "[private locator omitted]"
        if parsed.username or parsed.password:
            return "[private locator omitted]"
    if PureWindowsPath(value).is_absolute() or PurePosixPath(value).is_absolute():
        return "[local path omitted]"
    return value


def _export_record(obj) -> dict:
    data = _record(obj)
    if isinstance(obj, Run):
        data["input_artifacts"] = [
            {"artifact_id": item.artifact_id, "digest": item.digest} for item in obj.input_artifacts
        ]
    elif isinstance(obj, Artifact) and obj.availability != "public":
        data.pop("uri", None)
    elif isinstance(obj, RepositoryRef) and obj.status != "public":
        data.pop("url", None)
    return _redact_paths(data)


def build_view(catalog, object_id: str, mode: str = "compact", profile: str | None = None) -> dict:
    """Build a purpose-specific projection from canonical state only."""

    _ensure_valid(catalog)
    if mode == "compact":
        if profile:
            raise ValueError("--profile is valid only with --mode execution")
        return _compact_unchecked(catalog, object_id)
    if mode == "research":
        if profile:
            raise ValueError("--profile is valid only with --mode execution")
        return _research_unchecked(catalog, object_id)
    if mode == "execution":
        return _execution_unchecked(catalog, object_id, profile)
    raise ValueError(f"unknown view mode: {mode}")


def build_export(catalog, object_id: str) -> dict:
    """Build a self-contained, export-safe snapshot from canonical state."""

    _ensure_valid(catalog)
    focus = catalog.get(object_id)
    revision, dirty = git_identity(catalog.root)
    compact = _redact_paths(_compact_unchecked(catalog, object_id))
    research = _research_unchecked(catalog, object_id, export_safe=True)
    execution = _redact_paths(_execution_unchecked(catalog, object_id))
    summary = {
        key: value
        for key, value in compact.items()
        if key not in {"dor_view_version", "mode", "focus"}
    }
    execution_payload = {
        key: value
        for key, value in execution.items()
        if key not in {"dor_view_version", "mode", "focus"}
    }
    return {
        "dor_view_version": VIEW_VERSION,
        "source": {
            "program_id": catalog.program.id,
            "repository": _redact_paths(catalog.program.repository),
            "research_revision": revision,
            "research_dirty": dirty,
        },
        "focus": _redact_paths(_summary(focus)),
        "summary": summary,
        "research": research["research"],
        "studies": research["studies"],
        "runs": research["runs"],
        "execution": execution_payload,
        "unresolved": research["unresolved"],
    }
