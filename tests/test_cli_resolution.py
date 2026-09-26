import json

from open_research.cli import main
from open_research.ids import new_id
from open_research.models import InfrastructureProvider, Study
from open_research.resolver import readiness, resolve
from open_research.store import load_catalog, validate_catalog
from conftest import read_yaml, write_yaml


def first_study(catalog):
    return next(obj for obj in catalog.of_type(Study) if obj.entrypoint)


def test_status_show_studies_and_resolve(research_tree, capsys):
    catalog = load_catalog(research_tree)
    study = first_study(catalog)
    profile = catalog.get(study.profile_ids[0])

    assert main(["--root", str(research_tree), "status", "--json"]) == 0
    status = json.loads(capsys.readouterr().out)
    assert len(status["studies"]) == 8
    assert status["recent_runs"] == []
    assert status["claims_by_status"] == {"proposed": 4}
    blocked = next(row for row in status["studies"] if row["id"] == study.id)
    assert blocked["readiness"] == "blocked"
    assert any("artifact" in item for item in blocked["blockers"])

    assert main(["--root", str(research_tree), "show", study.question_ids[0], "--json"]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["object"]["id"] == study.question_ids[0]
    assert shown["inbound_connections"]

    assert main(["--root", str(research_tree), "studies", "Frozen stock", "--json"]) == 0
    matches = json.loads(capsys.readouterr().out)
    assert len(matches) == 1 and matches[0]["id"] == study.id

    assert main(
        ["--root", str(research_tree), "resolve", study.id, "--profile", profile.name, "--json"]
    ) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["study_id"] == study.id
    assert not plan["ready"]
    assert plan["providers"]
    assert all(
        provider["revision"] == catalog.get(provider["repository_id"]).revision
        for provider in plan["providers"]
    )
    assert any("lockfile and digest" in item for item in plan["blockers"])


def test_unsupported_capability_resolution(research_tree):
    catalog = load_catalog(research_tree)
    study = first_study(catalog)
    path = catalog.paths[study.id]
    value = read_yaml(path)
    value["requires"]["capabilities"].append("nonexistent.kernel@1")
    write_yaml(path, value)
    catalog = load_catalog(research_tree)
    plan = resolve(catalog, study.id, study.profile_ids[0])
    assert "missing compatible capability: nonexistent.kernel@1" in plan["blockers"]


def test_profile_environment_incompatibility(research_tree):
    catalog = load_catalog(research_tree)
    study = first_study(catalog)
    provider = next(
        obj
        for obj in catalog.objects.values()
        if getattr(obj, "capabilities", None) and "model.dawn_srw@1" in obj.capabilities
    )
    value = read_yaml(catalog.paths[provider.id])
    value["profile_ids"] = []
    write_yaml(catalog.paths[provider.id], value)
    catalog = load_catalog(research_tree)
    plan = resolve(catalog, study.id, study.profile_ids[0])
    assert not plan["ready"]
    assert "missing compatible capability: model.dawn_srw@1" in plan["blockers"]


def test_draft_and_blocked_readiness_are_derived(research_tree):
    catalog = load_catalog(research_tree)
    states = {item.title: readiness(catalog, item)[0] for item in catalog.of_type(Study)}
    assert states["Random versus structured organization"] == "draft"
    assert states["Physical sparse execution"] == "blocked"


def test_best_provider_plan_is_chosen_across_environments(research_tree):
    catalog = load_catalog(research_tree)
    study = first_study(catalog)
    profile = catalog.get(study.profile_ids[0])
    original_environment = catalog.get(profile.environment_ids[0])
    better_environment = original_environment.model_copy(
        update={"id": new_id("DAWN", "ENV"), "status": "available"}
    )
    catalog.objects[better_environment.id] = better_environment
    profile.environment_ids.append(better_environment.id)
    better_ids = set()
    for provider in list(catalog.of_type(InfrastructureProvider)):
        better = provider.model_copy(
            update={
                "id": new_id("DAWN", "INFRA"),
                "status": "available",
                "environment_ids": [better_environment.id],
            }
        )
        catalog.objects[better.id] = better
        better_ids.add(better.id)
    plan = resolve(catalog, study.id, profile.id)
    assert plan["environment_id"] == better_environment.id
    assert {item["id"] for item in plan["providers"]} == better_ids
    assert not plan["ready"]


def test_public_artifact_reference_is_not_local_execution_ready(research_tree):
    catalog = load_catalog(research_tree)
    study = first_study(catalog)
    artifact = catalog.get(study.requires.artifacts[0])
    artifact.availability = "public"
    artifact.uri = "https://example.invalid/checkpoint"
    artifact.digest = "sha256:" + "a" * 64
    plan = resolve(catalog, study.id, study.profile_ids[0])
    assert not plan["ready"]
    assert any("needs a local path" in blocker for blocker in plan["blockers"])
    assert not plan["publicly_reproducible"]


def test_bad_profile_reference_reports_validation_error(research_tree):
    catalog = load_catalog(research_tree)
    study = first_study(catalog)
    path = catalog.paths[study.id]
    value = read_yaml(path)
    value["profile_ids"] = [new_id("DAWN", "PROFILE")]
    value["declared_readiness"] = "local"
    write_yaml(path, value)
    errors = validate_catalog(load_catalog(research_tree))
    assert any("missing ResourceProfile" in error for error in errors)
    assert any("cannot resolve profile" in error for error in errors)


def test_public_readiness_cannot_be_declared_from_unvalidated_infrastructure(research_tree):
    catalog = load_catalog(research_tree)
    study = first_study(catalog)
    path = catalog.paths[study.id]
    value = read_yaml(path)
    value["declared_readiness"] = "public"
    write_yaml(path, value)
    assert any(
        "declared public with missing dependencies" in error
        for error in validate_catalog(load_catalog(research_tree))
    )


def test_zero_shot_seed_requirements_are_preserved(research_tree):
    catalog = load_catalog(research_tree)
    study = first_study(catalog)
    assert set(study.requires.capabilities) == {
        "model.dawn_srw@1",
        "checkpoint.load@1",
        "evaluation.zero_shot@1",
        "runtime.jax@1",
        "runtime.tpu@1",
    }
    assert {catalog.get(method_id).title for method_id in study.method_ids} == {
        "Frozen stock zero-shot evaluation",
    }
    assert catalog.get(study.entrypoint_method_id).title == "Frozen stock zero-shot evaluation"


def test_generation_uses_a_separate_single_method_study(research_tree):
    catalog = load_catalog(research_tree)
    study = next(item for item in catalog.of_type(Study) if item.title == "Autoregressive generation validation")
    assert len(study.method_ids) == 1
    assert catalog.get(study.method_ids[0]).title == "Autoregressive generation sampling"
    assert study.entrypoint is None
    assert study.entrypoint_method_id is None
