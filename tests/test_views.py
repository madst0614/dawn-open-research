import hashlib
import json
from pathlib import Path

import pytest

from open_research import views
from open_research.cli import main
from open_research.ids import new_id
from open_research.models import (
    Claim,
    InfrastructureProvider,
    Relation,
    ResourceProfile,
    Result,
    Run,
    Source,
    Study,
)
from open_research.resolver import resolve
from open_research.store import load_catalog, validate_catalog
from open_research.views import build_export, build_view
from conftest import read_yaml, write_yaml


def executable_study(catalog):
    return next(item for item in catalog.of_type(Study) if item.entrypoint)


def canonical_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".dor" not in path.parts
    }


def add_result_provenance(research_tree: Path):
    catalog = load_catalog(research_tree)
    study = executable_study(catalog)
    profile = catalog.get(study.profile_ids[0], ResourceProfile)
    environment_id = profile.environment_ids[0]
    selected = {}
    for capability in study.requires.capabilities:
        candidates = sorted(
            [
                provider
                for provider in catalog.of_type(InfrastructureProvider)
                if capability in provider.capabilities
                and environment_id in provider.environment_ids
                and profile.id in provider.profile_ids
            ],
            key=lambda provider: provider.id,
        )
        selected[capability] = candidates[0]
    providers = {provider.id: provider for provider in selected.values()}

    run_id = new_id(catalog.program.namespace, "RUN")
    run_dir = research_tree / "runs" / run_id
    run_dir.mkdir(parents=True)
    config_bytes = b"{}\n"
    (run_dir / "config.json").write_bytes(config_bytes)
    local_artifact = (research_tree / "private-fixture-artifact").resolve()
    run = Run(
        id=run_id,
        created_by="github:test",
        created_at="2026-09-26T00:00:00Z",
        study_id=study.id,
        method_id=study.entrypoint_method_id,
        research_revision="b" * 40,
        research_dirty=False,
        implementations=[
            {
                "provider_id": provider.id,
                "interface_version": provider.interface_version,
                "repository_id": provider.repository_id,
                "revision": catalog.get(provider.repository_id).revision,
                "dirty": False,
            }
            for provider in sorted(providers.values(), key=lambda item: item.id)
        ],
        environment_id=environment_id,
        environment_lock_digest="sha256:" + "a" * 64,
        profile_id=profile.id,
        hardware_class=profile.hardware_class,
        input_artifacts=[
            {
                "artifact_id": artifact_id,
                "digest": "sha256:" + "c" * 64,
                "location": str(local_artifact),
            }
            for artifact_id in study.requires.artifacts
        ],
        config_digest="sha256:" + hashlib.sha256(config_bytes).hexdigest(),
        config_path="config.json",
        command=["fixture-evaluator", f"artifact:{study.requires.artifacts[0]}"],
        executor="github:test",
        started_at="2026-09-26T00:00:00Z",
        status="created",
    )
    write_yaml(run_dir / "manifest.yaml", run.model_dump(mode="json"))

    source = Source(
        id=new_id(catalog.program.namespace, "SRC"),
        created_by="github:test",
        created_at="2026-09-26T00:00:30Z",
        title="Isolated fixture reference",
        source_type="other",
        uri="https://example.invalid/isolated-fixture-reference",
        source_statement="Fixture reference used only for Result provenance.",
    )
    source_dir = research_tree / "graph" / "sources"
    write_yaml(source_dir / f"{source.id}.yaml", source.model_dump(mode="json"))

    result = Result(
        id=new_id(catalog.program.namespace, "RES"),
        created_by="github:test",
        created_at="2026-09-26T00:01:00Z",
        title="Fixture outcome",
        statement="A fixture outcome tied to exact provenance.",
        scope="Projection tests only.",
        limitations=str(local_artifact),
        run_ids=[run.id],
        source_ids=[source.id],
        authors=["github:test"],
    )
    result_dir = research_tree / "graph" / "results"
    write_yaml(result_dir / f"{result.id}.yaml", result.model_dump(mode="json"))

    claim = sorted(catalog.of_type(Claim), key=lambda item: item.id)[0]
    relation = Relation(
        id=new_id(catalog.program.namespace, "REL"),
        created_by="github:test",
        created_at="2026-09-26T00:02:00Z",
        source_id=result.id,
        target_id=claim.id,
        relation_class="semantic",
        relation_type="supports",
        status="proposed",
        asserted_by="github:test",
        asserted_at="2026-09-26T00:02:00Z",
        rationale="Expose the Result and its exact provenance in the fixture closure.",
    )
    write_yaml(
        research_tree / "graph" / "relations" / f"{relation.id}.yaml",
        relation.model_dump(mode="json"),
    )
    catalog = load_catalog(research_tree)
    assert validate_catalog(catalog) == []
    return catalog, study, result, source, run, local_artifact


def test_compact_study_view_answers_research_questions(research_tree, capsys):
    catalog = load_catalog(research_tree)
    study = executable_study(catalog)
    result = build_view(catalog, study.id)
    assert result["mode"] == "compact"
    assert result["focus"]["id"] == study.id
    assert result["focus"]["title"] == study.title
    assert result["state"]["readiness"] == "blocked"
    assert result["what_are_we_studying"] == study.goal
    assert result["questions"] and result["methods"] and result["profiles"]
    assert result["claims"] == [] and result["results"] == []
    assert result["latest_run"] is None
    assert result["next"]["completion_criteria"] == study.completion_criteria
    assert "schema_version" not in result["focus"]
    assert "created_by" not in result["focus"]

    assert main(["--root", str(research_tree), "view", study.id, "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == result

    question = catalog.get(study.question_ids[0])
    question_view = build_view(catalog, question.id)
    assert question_view["focus"]["id"] == question.id
    assert question_view["connections"]
    assert study.id in {item["id"] for item in question_view["related_studies"]}


def test_research_view_uses_bounded_explicit_graph_closure(research_tree):
    catalog = load_catalog(research_tree)
    study = executable_study(catalog)
    result = build_view(catalog, study.id, "research")
    assert result["focus"]["question_ids"] == study.question_ids
    assert result["focus"]["claim_ids"] == study.claim_ids
    assert result["focus"]["method_ids"] == study.method_ids
    assert set(result["research"]) == {
        "questions",
        "claims",
        "methods",
        "results",
        "references",
        "connections",
        "other_objects",
    }

    seeds = set(study.question_ids + study.claim_ids + study.method_ids)
    expected_connections = {
        relation.id
        for relation in catalog.of_type(Relation)
        if relation.source_id in seeds or relation.target_id in seeds
    }
    actual_connections = {item["id"] for item in result["research"]["connections"]}
    assert actual_connections == expected_connections

    included_ids = {
        item["id"] for name, _ in views.GRAPH_GROUPS for item in result["research"][name]
    }
    expected_endpoints = {
        endpoint
        for relation in catalog.of_type(Relation)
        if relation.id in expected_connections
        for endpoint in (relation.source_id, relation.target_id)
    }
    assert seeds | expected_endpoints <= included_ids
    unrelated = next(
        object_id
        for object_id in sorted(catalog.objects)
        if object_id.startswith("DAWN-C-") and object_id not in included_ids
    )
    assert unrelated not in included_ids


def test_result_run_and_reference_provenance_are_exact(research_tree):
    catalog, study, result, source, run, local_artifact = add_result_provenance(research_tree)
    projected = build_view(catalog, study.id, "research")
    result_rows = {item["id"]: item for item in projected["research"]["results"]}
    source_rows = {item["id"]: item for item in projected["research"]["references"]}
    run_rows = {item["id"]: item for item in projected["runs"]}
    assert not any(
        source.id in {relation.source_id, relation.target_id}
        for relation in catalog.of_type(Relation)
    )
    assert result_rows[result.id] == catalog.get(result.id).model_dump(mode="json")
    assert result_rows[result.id]["limitations"] == str(local_artifact)
    assert source_rows[source.id] == catalog.get(source.id).model_dump(mode="json")
    assert run_rows[run.id] == catalog.get(run.id).model_dump(mode="json")


def test_execution_view_is_resolver_output_and_profile_filter(research_tree):
    catalog = load_catalog(research_tree)
    study = executable_study(catalog)
    profile = catalog.get(study.profile_ids[0], ResourceProfile)
    expected = resolve(catalog, study.id, profile.id)
    result = build_view(catalog, study.id, "execution")
    assert result["resolutions"] == [expected]
    assert result["resolutions"][0]["blockers"] == expected["blockers"]
    assert result["ready"] == expected["ready"]
    assert result["publicly_reproducible"] == expected["publicly_reproducible"]

    alternate = profile.model_copy(
        update={"id": new_id(catalog.program.namespace, "PROFILE"), "name": profile.name + "-alternate"}
    )
    catalog.objects[alternate.id] = alternate
    study.profile_ids.append(alternate.id)
    all_profiles = build_view(catalog, study.id, "execution")
    filtered = build_view(catalog, study.id, "execution", profile.name)
    assert [item["profile_id"] for item in all_profiles["resolutions"]] == sorted(study.profile_ids)
    assert filtered["resolutions"] == [resolve(catalog, study.id, profile.name)]

    unspecified = next(item for item in catalog.of_type(Study) if not item.entrypoint)
    unspecified_view = build_view(catalog, unspecified.id, "execution")
    assert unspecified_view["applicable"] is True
    assert unspecified_view["ready"] is False
    assert any(
        "no entrypoint" in blocker
        for plan in unspecified_view["resolutions"]
        for blocker in plan["blockers"]
    )
    assert any(
        "no executable Method" in blocker
        for plan in unspecified_view["resolutions"]
        for blocker in plan["blockers"]
    )


def test_export_is_deterministic_private_safe_and_read_only(research_tree, monkeypatch, capsys):
    catalog, study, result, _, _, local_artifact = add_result_provenance(research_tree)
    private = research_tree / ".dor" / "maps" / "private.intake.yaml"
    private.parent.mkdir(parents=True)
    private.write_text("secret: SUPER_PRIVATE_PACKET_MARKER\n", encoding="utf-8")
    revision = "d" * 40
    monkeypatch.setattr(views, "git_identity", lambda root: (revision, True))
    before_files = canonical_files(research_tree)
    before_count = len(catalog.objects)

    first = build_export(catalog, study.id)
    second = build_export(catalog, study.id)
    assert first == second
    assert first["source"]["research_revision"] == revision
    assert first["source"]["research_dirty"] is True
    assert set(first["research"]) == {
        "questions",
        "claims",
        "methods",
        "results",
        "references",
        "connections",
        "other_objects",
    }
    rendered = json.dumps(first, sort_keys=True)
    assert "SUPER_PRIVATE_PACKET_MARKER" not in rendered
    assert ".dor" not in rendered
    assert str(local_artifact) not in rendered
    exported_results = {item["id"]: item for item in first["research"]["results"]}
    assert exported_results[result.id]["limitations"] == "[local path omitted]"
    assert all("location" not in item for run in first["runs"] for item in run["input_artifacts"])

    build_view(catalog, study.id)
    build_view(catalog, study.id, "research")
    build_view(catalog, study.id, "execution")
    assert len(catalog.objects) == before_count
    assert canonical_files(research_tree) == before_files

    assert main(["--root", str(research_tree), "export", study.id, "--json"]) == 0
    cli_export = json.loads(capsys.readouterr().out)
    assert cli_export == first
    assert main(["--root", str(research_tree), "export", study.id]) == 0


def test_invalid_catalog_and_unknown_focus_fail_closed(research_tree, capsys):
    catalog = load_catalog(research_tree)
    missing_id = new_id(catalog.program.namespace, "Q")
    with pytest.raises(ValueError, match="missing object"):
        build_view(catalog, missing_id)
    with pytest.raises(ValueError, match="missing object"):
        build_export(catalog, missing_id)

    relation_path = sorted((research_tree / "graph" / "relations").glob("*.yaml"))[0]
    relation = read_yaml(relation_path)
    relation["target_id"] = missing_id
    write_yaml(relation_path, relation)
    invalid = load_catalog(research_tree)
    with pytest.raises(ValueError, match="invalid canonical catalog"):
        build_view(invalid, relation["source_id"])
    with pytest.raises(ValueError, match="invalid canonical catalog"):
        build_export(invalid, relation["source_id"])

    assert main(["--root", str(research_tree), "view", relation["source_id"]]) == 1
    assert "missing object" in capsys.readouterr().err
    assert main(["--root", str(research_tree), "export", relation["source_id"]]) == 1
    assert "missing object" in capsys.readouterr().err
