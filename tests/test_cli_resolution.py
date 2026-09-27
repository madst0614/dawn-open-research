import json

import pytest

from open_research.cli import main
from open_research.ids import new_id
from open_research.models import InfrastructureProvider, Study
from open_research.resolver import readiness, resolve
from open_research.store import load_catalog, validate_catalog
from conftest import read_yaml, write_yaml


def executable_study(catalog):
    return next(
        study
        for study in catalog.of_type(Study)
        if any(plan.entrypoint for plan in study.execution.plans)
    )


def zero_shot_plan(study):
    return next(plan for plan in study.execution.plans if plan.entrypoint)


def test_status_show_studies_and_resolve(research_tree, capsys):
    catalog = load_catalog(research_tree)
    study = executable_study(catalog)
    plan_config = zero_shot_plan(study)
    profile = catalog.get(plan_config.profile_ids[0])

    assert main(["--root", str(research_tree), "status", "--json"]) == 0
    status = json.loads(capsys.readouterr().out)
    assert len(status["studies"]) == 7
    assert status["recent_runs"] == []
    assert status["claims_by_status"] == {"proposed": 4}
    assert len(status["open_questions"]) == 7
    blocked = next(row for row in status["studies"] if row["id"] == study.id)
    assert blocked["readiness"] == "blocked"
    assert any("artifact" in item for item in blocked["blockers"])

    assert main(["--root", str(research_tree), "show", study.question_ids[0], "--json"]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["object"]["id"] == study.question_ids[0]
    assert shown["inbound_connections"]

    assert main(
        ["--root", str(research_tree), "studies", "Reference checkpoint", "--json"]
    ) == 0
    matches = json.loads(capsys.readouterr().out)
    assert len(matches) == 1 and matches[0]["id"] == study.id

    assert main(
        ["--root", str(research_tree), "resolve", study.id, "--profile", profile.name, "--json"]
    ) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["study_id"] == study.id
    assert plan["method_id"] == plan_config.method_id
    assert not plan["ready"]
    assert plan["providers"]
    assert all(
        provider["revision"] == catalog.get(provider["repository_id"]).revision
        for provider in plan["providers"]
    )
    assert any("lockfile and digest" in item for item in plan["blockers"])


def test_resolver_requires_method_when_executable_plans_are_ambiguous(research_tree, capsys):
    catalog = load_catalog(research_tree)
    study = executable_study(catalog)
    path = catalog.paths[study.id]
    value = read_yaml(path)
    value["execution"]["plans"][1]["entrypoint"] = "fixture.generation@1"
    write_yaml(path, value)
    catalog = load_catalog(research_tree)
    profile = catalog.get(catalog.get(study.id, Study).execution.plans[0].profile_ids[0])

    with pytest.raises(ValueError, match="ambiguous executable Methods"):
        resolve(catalog, study.id, profile.id)
    assert main(
        ["--root", str(research_tree), "resolve", study.id, "--profile", profile.id]
    ) == 1
    assert "pass --method" in capsys.readouterr().err

    selected = catalog.get(study.id, Study).execution.plans[1]
    resolved = resolve(
        catalog,
        study.id,
        profile.id,
        method_id=selected.method_id,
    )
    assert resolved["method_id"] == selected.method_id
    assert resolved["entrypoint"] == "fixture.generation@1"


def test_explicit_non_executable_method_reports_blocker(research_tree):
    catalog = load_catalog(research_tree)
    study = executable_study(catalog)
    generation = next(plan for plan in study.execution.plans if not plan.entrypoint)
    plan = resolve(
        catalog,
        study.id,
        generation.profile_ids[0],
        method_id=generation.method_id,
    )
    assert not plan["ready"]
    assert any("no execution entrypoint" in item for item in plan["blockers"])


def test_unsupported_capability_resolution(research_tree):
    catalog = load_catalog(research_tree)
    study = executable_study(catalog)
    path = catalog.paths[study.id]
    value = read_yaml(path)
    value["execution"]["plans"][0]["requires"]["capabilities"].append("nonexistent.kernel@1")
    write_yaml(path, value)
    catalog = load_catalog(research_tree)
    plan_config = zero_shot_plan(catalog.get(study.id, Study))
    plan = resolve(
        catalog,
        study.id,
        plan_config.profile_ids[0],
        method_id=plan_config.method_id,
    )
    assert "missing compatible capability: nonexistent.kernel@1" in plan["blockers"]


def test_profile_environment_incompatibility(research_tree):
    catalog = load_catalog(research_tree)
    study = executable_study(catalog)
    plan_config = zero_shot_plan(study)
    provider = next(
        obj
        for obj in catalog.objects.values()
        if getattr(obj, "capabilities", None) and "model.dawn_srw@1" in obj.capabilities
    )
    value = read_yaml(catalog.paths[provider.id])
    value["profile_ids"] = []
    write_yaml(catalog.paths[provider.id], value)
    catalog = load_catalog(research_tree)
    plan = resolve(
        catalog,
        study.id,
        plan_config.profile_ids[0],
        method_id=plan_config.method_id,
    )
    assert not plan["ready"]
    assert "missing compatible capability: model.dawn_srw@1" in plan["blockers"]


def test_draft_and_blocked_readiness_are_derived(research_tree):
    catalog = load_catalog(research_tree)
    states = {item.title: readiness(catalog, item)[0] for item in catalog.of_type(Study)}
    assert states["Random versus structured organization"] == "draft"
    assert states["Physical sparse execution"] == "blocked"
    assert states["Reference checkpoint language validation"] == "blocked"


def test_best_provider_plan_is_chosen_across_environments(research_tree):
    catalog = load_catalog(research_tree)
    study = executable_study(catalog)
    plan_config = zero_shot_plan(study)
    profile = catalog.get(plan_config.profile_ids[0])
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
    plan = resolve(
        catalog,
        study.id,
        profile.id,
        method_id=plan_config.method_id,
    )
    assert plan["environment_id"] == better_environment.id
    assert {item["id"] for item in plan["providers"]} == better_ids
    assert not plan["ready"]


def test_public_artifact_reference_is_not_local_execution_ready(research_tree):
    catalog = load_catalog(research_tree)
    study = executable_study(catalog)
    plan_config = zero_shot_plan(study)
    artifact = catalog.get(plan_config.requires.artifacts[0])
    artifact.availability = "public"
    artifact.uri = "https://example.invalid/checkpoint"
    artifact.digest = "sha256:" + "a" * 64
    plan = resolve(
        catalog,
        study.id,
        plan_config.profile_ids[0],
        method_id=plan_config.method_id,
    )
    assert not plan["ready"]
    assert any("needs a local path" in blocker for blocker in plan["blockers"])
    assert not plan["publicly_reproducible"]


def test_bad_profile_reference_reports_validation_error(research_tree):
    catalog = load_catalog(research_tree)
    study = executable_study(catalog)
    path = catalog.paths[study.id]
    value = read_yaml(path)
    value["execution"]["plans"][0]["profile_ids"] = [new_id("DAWN", "PROFILE")]
    value["execution"]["plans"][0]["declared_readiness"] = "local"
    write_yaml(path, value)
    errors = validate_catalog(load_catalog(research_tree))
    assert any("missing ResourceProfile" in error for error in errors)
    assert any("cannot resolve Method" in error for error in errors)


def test_public_readiness_cannot_be_declared_from_unvalidated_infrastructure(research_tree):
    catalog = load_catalog(research_tree)
    study = executable_study(catalog)
    path = catalog.paths[study.id]
    value = read_yaml(path)
    value["execution"]["plans"][0]["declared_readiness"] = "public"
    write_yaml(path, value)
    assert any(
        "declared public with missing dependencies" in error
        for error in validate_catalog(load_catalog(research_tree))
    )


def test_legacy_language_validation_is_one_multi_method_study(research_tree):
    catalog = load_catalog(research_tree)
    study = executable_study(catalog)
    assert len(study.method_ids) == 2
    assert {catalog.get(method_id).title for method_id in study.method_ids} == {
        "Frozen stock zero-shot evaluation",
        "Autoregressive generation sampling",
    }
    plans = {plan.method_id: plan for plan in study.execution.plans}
    assert set(plans) == set(study.method_ids)
    zero_shot = zero_shot_plan(study)
    assert set(zero_shot.requires.capabilities) == {
        "model.dawn_srw@1",
        "checkpoint.load@1",
        "evaluation.zero_shot@1",
        "runtime.jax@1",
        "runtime.tpu@1",
    }
    generation = next(plan for plan in study.execution.plans if not plan.entrypoint)
    assert "generation.autoregressive@1" in generation.requires.capabilities
    assert generation.blockers
