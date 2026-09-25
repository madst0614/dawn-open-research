import hashlib
import json
from pathlib import Path

import pytest
import yaml

from open_research import views
from open_research.cli import main
from open_research.ids import new_id
from open_research.models import (
    Evidence,
    Exploration,
    InfrastructureProvider,
    Relation,
    ResourceProfile,
    Run,
    Source,
)
from open_research.resolver import resolve
from open_research.store import load_catalog, validate_catalog
from open_research.views import build_export, build_view
from conftest import read_yaml, write_yaml


def executable_exploration(catalog):
    return next(item for item in catalog.of_type(Exploration) if item.entrypoint)


def canonical_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".dor" not in path.parts
    }


def add_evidence_provenance(research_tree: Path):
    catalog = load_catalog(research_tree)
    exploration = executable_exploration(catalog)
    profile = catalog.get(exploration.profile_ids[0], ResourceProfile)
    environment_id = profile.environment_ids[0]
    selected = {}
    for capability in exploration.requires.capabilities:
        candidates = sorted(
            [provider for provider in catalog.of_type(InfrastructureProvider)
             if capability in provider.capabilities
             and environment_id in provider.environment_ids
             and profile.id in provider.profile_ids],
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
        created_at="2026-09-25T00:00:00Z",
        exploration_id=exploration.id,
        probe_id=exploration.entrypoint_probe_id,
        research_revision="b" * 40,
        research_dirty=False,
        implementations=[{
            "provider_id": provider.id,
            "interface_version": provider.interface_version,
            "repository_id": provider.repository_id,
            "revision": catalog.get(provider.repository_id).revision,
            "dirty": False,
        } for provider in sorted(providers.values(), key=lambda item: item.id)],
        environment_id=environment_id,
        environment_lock_digest="sha256:" + "a" * 64,
        profile_id=profile.id,
        hardware_class=profile.hardware_class,
        input_artifacts=[{
            "artifact_id": artifact_id,
            "digest": "sha256:" + "c" * 64,
            "location": str(local_artifact),
        } for artifact_id in exploration.requires.artifacts],
        config_digest="sha256:" + hashlib.sha256(config_bytes).hexdigest(),
        config_path="config.json",
        command=["fixture-evaluator", f"artifact:{exploration.requires.artifacts[0]}"],
        executor="github:test",
        started_at="2026-09-25T00:00:00Z",
        status="created",
    )
    write_yaml(run_dir / "manifest.yaml", run.model_dump(mode="json"))

    source = sorted(catalog.of_type(Source), key=lambda item: item.id)[0]
    evidence_id = new_id(catalog.program.namespace, "E")
    evidence = Evidence(
        id=evidence_id,
        created_by="github:test",
        created_at="2026-09-25T00:01:00Z",
        title="Fixture observation",
        observation="A fixture observation tied to exact provenance.",
        scope="Projection tests only.",
        limitations="Synthetic fixture, not a research finding.",
        run_ids=[run.id],
        source_ids=[source.id],
        authors=["github:test"],
    )
    evidence_dir = research_tree / "graph" / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    write_yaml(evidence_dir / f"{evidence.id}.yaml", evidence.model_dump(mode="json"))

    relation_id = new_id(catalog.program.namespace, "R")
    relation = Relation(
        id=relation_id,
        created_by="github:test",
        created_at="2026-09-25T00:02:00Z",
        source_id=evidence.id,
        target_id=exploration.targets[0],
        relation_class="semantic",
        relation_type="answers",
        status="proposed",
        asserted_by="github:test",
        asserted_at="2026-09-25T00:02:00Z",
        rationale="Expose explicit Evidence provenance in the fixture closure.",
    )
    write_yaml(research_tree / "graph" / "relations" / f"{relation.id}.yaml",
               relation.model_dump(mode="json"))
    catalog = load_catalog(research_tree)
    assert validate_catalog(catalog) == []
    return catalog, exploration, evidence, source, run, local_artifact


def test_compact_exploration_view_is_small_and_useful(research_tree, capsys):
    catalog = load_catalog(research_tree)
    exploration = executable_exploration(catalog)
    result = build_view(catalog, exploration.id)
    assert result["mode"] == "compact"
    assert result["focus"]["id"] == exploration.id
    assert result["focus"]["title"] == exploration.title
    assert result["state"]["readiness"] == "blocked"
    assert result["goal"] == exploration.goal
    assert result["targets"] and result["probes"] and result["profiles"]
    assert result["latest_run"] is None
    assert "schema_version" not in result["focus"]
    assert "created_by" not in result["focus"]
    assert "expected_outputs" not in result

    assert main(["--root", str(research_tree), "view", exploration.id, "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == result

    question = catalog.get(exploration.targets[0])
    question_view = build_view(catalog, question.id)
    assert question_view["focus"]["id"] == question.id
    assert question_view["relations"]
    assert exploration.id in {item["id"] for item in question_view["related_explorations"]}


def test_research_view_uses_bounded_explicit_graph_closure(research_tree):
    catalog = load_catalog(research_tree)
    exploration = executable_exploration(catalog)
    result = build_view(catalog, exploration.id, "research")
    assert result["focus"]["graph_context"] == exploration.graph_context
    assert result["focus"]["targets"] == exploration.targets
    assert result["focus"]["probe_ids"] == exploration.probe_ids

    seeds = set(exploration.graph_context + exploration.targets + exploration.probe_ids)
    expected_relations = {
        relation.id for relation in catalog.of_type(Relation)
        if relation.source_id in seeds or relation.target_id in seeds
    }
    actual_relations = {item["id"] for item in result["research"]["relations"]}
    assert actual_relations == expected_relations

    included_ids = {
        item["id"] for name, _ in views.GRAPH_GROUPS for item in result["research"][name]
    }
    expected_endpoints = {
        endpoint for relation in catalog.of_type(Relation) if relation.id in expected_relations
        for endpoint in (relation.source_id, relation.target_id)
    }
    assert seeds | expected_endpoints <= included_ids
    unrelated = next(object_id for object_id in sorted(catalog.objects)
                     if object_id.startswith("DAWN-C-") and object_id not in included_ids)
    assert unrelated not in included_ids


def test_evidence_run_and_source_provenance_are_exact(research_tree):
    catalog, exploration, evidence, source, run, _ = add_evidence_provenance(research_tree)
    result = build_view(catalog, exploration.id, "research")
    evidence_rows = {item["id"]: item for item in result["research"]["evidence"]}
    source_rows = {item["id"]: item for item in result["research"]["sources"]}
    run_rows = {item["id"]: item for item in result["runs"]}
    assert evidence_rows[evidence.id] == catalog.get(evidence.id).model_dump(mode="json")
    assert source_rows[source.id] == catalog.get(source.id).model_dump(mode="json")
    assert run_rows[run.id] == catalog.get(run.id).model_dump(mode="json")


def test_execution_view_is_resolver_output_and_profile_filter(research_tree):
    catalog = load_catalog(research_tree)
    exploration = executable_exploration(catalog)
    profile = catalog.get(exploration.profile_ids[0], ResourceProfile)
    expected = resolve(catalog, exploration.id, profile.id)
    result = build_view(catalog, exploration.id, "execution")
    assert result["resolutions"] == [expected]
    assert result["resolutions"][0]["blockers"] == expected["blockers"]
    assert result["ready"] == expected["ready"]
    assert result["publicly_reproducible"] == expected["publicly_reproducible"]

    alternate = profile.model_copy(update={
        "id": new_id(catalog.program.namespace, "PROFILE"),
        "name": profile.name + "-alternate",
    })
    catalog.objects[alternate.id] = alternate
    exploration.profile_ids.append(alternate.id)
    all_profiles = build_view(catalog, exploration.id, "execution")
    filtered = build_view(catalog, exploration.id, "execution", profile.name)
    assert [item["profile_id"] for item in all_profiles["resolutions"]] == sorted(exploration.profile_ids)
    assert filtered["resolutions"] == [resolve(catalog, exploration.id, profile.name)]

    unspecified = next(item for item in catalog.of_type(Exploration) if not item.entrypoint)
    unspecified_view = build_view(catalog, unspecified.id, "execution")
    assert unspecified_view["applicable"] is True
    assert unspecified_view["ready"] is False
    assert any("no entrypoint" in blocker for plan in unspecified_view["resolutions"]
               for blocker in plan["blockers"])
    assert any("no executable Probe" in blocker for plan in unspecified_view["resolutions"]
               for blocker in plan["blockers"])


def test_export_is_deterministic_private_safe_and_read_only(research_tree, monkeypatch, capsys):
    catalog, exploration, _, _, _, local_artifact = add_evidence_provenance(research_tree)
    private = research_tree / ".dor" / "maps" / "private.intake.yaml"
    private.parent.mkdir(parents=True)
    private.write_text("secret: SUPER_PRIVATE_PACKET_MARKER\n", encoding="utf-8")
    revision = "d" * 40
    monkeypatch.setattr(views, "git_identity", lambda root: (revision, True))
    before_files = canonical_files(research_tree)
    before_count = len(catalog.objects)

    first = build_export(catalog, exploration.id)
    second = build_export(catalog, exploration.id)
    assert first == second
    assert first["source"]["research_revision"] == revision
    assert first["source"]["research_dirty"] is True
    rendered = json.dumps(first, sort_keys=True)
    assert "SUPER_PRIVATE_PACKET_MARKER" not in rendered
    assert ".dor" not in rendered
    assert str(local_artifact) not in rendered
    assert all("location" not in item for run in first["runs"] for item in run["input_artifacts"])

    build_view(catalog, exploration.id)
    build_view(catalog, exploration.id, "research")
    build_view(catalog, exploration.id, "execution")
    assert len(catalog.objects) == before_count
    assert canonical_files(research_tree) == before_files

    assert main(["--root", str(research_tree), "export", exploration.id, "--json"]) == 0
    cli_export = json.loads(capsys.readouterr().out)
    assert cli_export == first
    assert main(["--root", str(research_tree), "export", exploration.id]) == 0
    assert yaml.safe_load(capsys.readouterr().out) == first


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
