from pathlib import Path
import json

import pytest
from pydantic import ValidationError

from open_research.ids import new_id, validate_id
from open_research.models import (
    Claim,
    DIRECTORIES,
    Method,
    Question,
    Relation,
    Result,
    Run,
    Source,
    Study,
    Program,
)
from open_research.store import load_catalog, validate_catalog
from conftest import SOURCE_ROOT, read_yaml, write_yaml


COMMON = {
    "created_by": "github:test",
    "created_at": "2026-09-26T00:00:00Z",
}


def only(root: Path, directory: str):
    return next((root / directory).glob("*.yaml"))


def executable_study(catalog):
    return next(
        study
        for study in catalog.of_type(Study)
        if any(plan.entrypoint for plan in study.execution.plans)
    )


def write_relation(research_tree, source_id, target_id, relation_type, *, accepted=False):
    relation = Relation(
        id=new_id("DAWN", "REL"),
        source_id=source_id,
        target_id=target_id,
        relation_class="semantic",
        relation_type=relation_type,
        status="accepted" if accepted else "proposed",
        asserted_by="github:test",
        asserted_at="2026-09-26T00:00:00Z",
        rationale="Bounded fixture relationship.",
        reviewers=["github:reviewer"] if accepted else [],
        **COMMON,
    )
    write_yaml(
        research_tree / "graph" / "relations" / f"{relation.id}.yaml",
        relation.model_dump(mode="json"),
    )
    return relation


def write_result(research_tree, grounding_id):
    result = Result(
        id=new_id("DAWN", "RES"),
        title="Grounded fixture result",
        statement="A bounded outcome occurred.",
        scope="Fixture scope.",
        limitations="Fixture only.",
        grounding_ids=[grounding_id],
        authors=["github:test"],
        **COMMON,
    )
    write_yaml(
        research_tree / "graph" / "results" / f"{result.id}.yaml",
        result.model_dump(mode="json"),
    )
    return result


def test_offline_ids_are_unique_and_namespace_specific():
    ids = {new_id("OTHER", "ST") for _ in range(300)}
    assert len(ids) == 300
    assert all(validate_id(value, "OTHER", "ST") == "ST" for value in ids)
    with pytest.raises(ValueError):
        validate_id(next(iter(ids)), "DAWN", "ST")
    with pytest.raises(ValueError):
        new_id("DAWN", "UNKNOWN")


def test_generated_schemas_match_canonical_models():
    classes = {model.__name__: model for _, model in DIRECTORIES.values()}
    classes["Program"] = Program
    expected_names = {f"{name}.schema.json" for name in classes}
    actual_names = {path.name for path in (SOURCE_ROOT / "schemas").glob("*.schema.json")}
    assert actual_names == expected_names
    for name, model in classes.items():
        path = SOURCE_ROOT / "schemas" / f"{name}.schema.json"
        assert json.loads(path.read_text(encoding="utf-8")) == model.model_json_schema()


def test_question_requires_inquiry_rationale_scope_and_valid_status():
    question = Question(
        id=new_id("DAWN", "Q"),
        title="Open target",
        question="What remains unknown?",
        rationale="The answer changes which analysis is relevant.",
        scope="One bounded fixture.",
        status="open",
        **COMMON,
    )
    assert question.status == "open"
    for missing in ("question", "rationale", "scope"):
        value = question.model_dump(mode="json")
        value.pop(missing)
        with pytest.raises(ValidationError):
            Question.model_validate(value)
    with pytest.raises(ValidationError):
        Question.model_validate({**question.model_dump(mode="json"), "status": "proposed"})


@pytest.mark.parametrize("claim_type", ["proposition", "interpretation", "definition"])
def test_claim_types_validate_independently_from_status(claim_type):
    claim = Claim(
        id=new_id("DAWN", "C"),
        title=claim_type.title(),
        statement=f"A bounded {claim_type}.",
        claim_type=claim_type,
        scope="Fixture scope.",
        status="tentative",
        **COMMON,
    )
    assert claim.claim_type == claim_type
    assert claim.status == "tentative"


def test_method_validates_without_a_run():
    method = Method(
        id=new_id("DAWN", "M"),
        title="Fixture analysis",
        description="Analyze one bounded fixture.",
        protocol="Apply the specified analysis and retain its outputs.",
        status="specified",
        **COMMON,
    )
    assert method.status == "specified"


def test_study_can_start_without_question_or_claim_and_with_method_only():
    method_id = new_id("DAWN", "M")
    study = Study(
        id=new_id("DAWN", "ST"),
        title="Exploratory method study",
        lifecycle="planned",
        goal="Apply a reusable method before a Question is known.",
        motivation="Method-first work can expose a later inquiry.",
        method_ids=[method_id],
        completion_criteria="Review what the Method reveals.",
        execution={"plans": []},
        **COMMON,
    )
    assert study.question_ids == []
    assert study.claim_ids == []
    assert study.method_ids == [method_id]


def test_study_accepts_multiple_method_specific_execution_plans():
    first = new_id("DAWN", "M")
    second = new_id("DAWN", "M")
    study = Study(
        id=new_id("DAWN", "ST"),
        title="Multi-method study",
        lifecycle="planned",
        goal="Compare two bounded procedures.",
        motivation="The procedures answer different parts of the same inquiry.",
        method_ids=[first, second],
        completion_criteria="Review both procedures.",
        execution={
            "plans": [
                {"method_id": first, "entrypoint": "fixture.first@1"},
                {"method_id": second, "entrypoint": "fixture.second@1"},
            ]
        },
        **COMMON,
    )
    assert {plan.method_id for plan in study.execution.plans} == {first, second}


def test_duplicate_id_detected(research_tree):
    path = only(research_tree, "graph/claims")
    (path.parent / "duplicate.yaml").write_bytes(path.read_bytes())
    assert any("duplicate ID" in error for error in load_catalog(research_tree).errors)


def test_invalid_claim_status_is_rejected(research_tree):
    path = only(research_tree, "graph/claims")
    value = read_yaml(path)
    value["status"] = "proven"
    write_yaml(path, value)
    assert any("status" in error for error in load_catalog(research_tree).errors)


def test_supported_claim_requires_reviewed_scholarly_support(research_tree):
    path = only(research_tree, "graph/claims")
    value = read_yaml(path)
    value["status"] = "supported"
    write_yaml(path, value)
    assert any(
        "requires an accepted supporting scholarly Relation" in error
        for error in validate_catalog(load_catalog(research_tree))
    )


def test_result_requires_grounding_and_prediction_field_is_rejected():
    base = {
        "id": new_id("DAWN", "RES"),
        "title": "Observation",
        "statement": "Measured value.",
        "scope": "One setting.",
        "limitations": "Small sample.",
        "authors": ["github:test"],
        **COMMON,
    }
    with pytest.raises(ValidationError):
        Result.model_validate(base)
    with pytest.raises(ValidationError, match="prediction"):
        Result.model_validate(
            {
                **base,
                "grounding_ids": [new_id("DAWN", "SRC")],
                "prediction": "An expected future outcome.",
            }
        )


def test_result_grounding_allows_source_and_artifact_but_rejects_other_types(research_tree):
    catalog = load_catalog(research_tree)
    source = catalog.of_type(Source)[0]
    artifact = next(obj for obj in catalog.objects.values() if obj.id.startswith("DAWN-ART-"))
    for grounding in (source.id, artifact.id):
        result = write_result(research_tree, grounding)
        assert validate_catalog(load_catalog(research_tree)) == []
        (research_tree / "graph" / "results" / f"{result.id}.yaml").unlink()

    result = write_result(research_tree, catalog.of_type(Claim)[0].id)
    assert any(
        "invalid Result grounding type" in error
        for error in validate_catalog(load_catalog(research_tree))
    )


def test_result_does_not_change_claim_status(research_tree):
    catalog = load_catalog(research_tree)
    claim = catalog.of_type(Claim)[0]
    source = catalog.of_type(Source)[0]
    write_result(research_tree, source.id)
    reloaded = load_catalog(research_tree)
    assert validate_catalog(reloaded) == []
    assert reloaded.get(claim.id, Claim).status == "proposed"


@pytest.mark.parametrize("support_kind", ["result", "source", "claim"])
def test_accepted_scholarly_support_can_ground_supported_claim(research_tree, support_kind):
    catalog = load_catalog(research_tree)
    target = sorted(catalog.of_type(Claim), key=lambda item: item.id)[0]
    target_path = catalog.paths[target.id]
    target_value = read_yaml(target_path)
    target_value["status"] = "supported"
    write_yaml(target_path, target_value)

    if support_kind == "result":
        source_id = write_result(research_tree, catalog.of_type(Source)[0].id).id
    elif support_kind == "source":
        source_id = catalog.of_type(Source)[0].id
    else:
        source_id = next(item.id for item in catalog.of_type(Claim) if item.id != target.id)
    write_relation(research_tree, source_id, target.id, "supports", accepted=True)
    assert validate_catalog(load_catalog(research_tree)) == []


def test_run_requires_implementation_and_environment():
    base = {
        "id": new_id("DAWN", "RUN"),
        "created_by": "github:test",
        "created_at": "2026-09-26T00:00:00Z",
        "study_id": new_id("DAWN", "ST"),
        "method_id": new_id("DAWN", "M"),
        "research_revision": "a" * 40,
        "research_dirty": False,
        "implementations": [],
        "profile_id": new_id("DAWN", "PROFILE"),
        "hardware_class": "CPU",
        "input_artifacts": [],
        "config_digest": "sha256:" + "a" * 64,
        "config_path": "config.json",
        "command": ["python"],
        "executor": "github:test",
        "started_at": "2026-09-26T00:00:00Z",
        "status": "created",
    }
    with pytest.raises(ValidationError) as exc:
        Run.model_validate(base)
    message = str(exc.value)
    assert "implementations" in message
    assert "environment_id" in message
    assert "environment_lock_digest" in message


def test_study_explicit_references_and_execution_artifacts_must_resolve(research_tree):
    path = only(research_tree, "studies")
    value = read_yaml(path)
    value["question_ids"] = [new_id("DAWN", "Q")]
    write_yaml(path, value)
    assert any("missing Question" in error for error in validate_catalog(load_catalog(research_tree)))

    catalog = load_catalog(research_tree)
    study = executable_study(catalog)
    path = catalog.paths[study.id]
    value = read_yaml(path)
    missing = new_id("DAWN", "ART")
    value["execution"]["plans"][0]["requires"]["artifacts"] = [missing]
    write_yaml(path, value)
    errors = validate_catalog(load_catalog(research_tree))
    assert any("missing Artifact" in error for error in errors)
    assert any("not listed in artifact_ids" in error for error in errors)


@pytest.mark.parametrize(
    ("source_kind", "relation_type", "target_kind"),
    [
        ("C", "raises", "Q"),
        ("RES", "raises", "Q"),
        ("SRC", "motivates", "Q"),
        ("M", "enables", "Q"),
        ("ART", "enables", "Q"),
        ("Q", "refines", "Q"),
    ],
)
def test_question_history_relations_are_representable(
    research_tree, source_kind, relation_type, target_kind
):
    catalog = load_catalog(research_tree)
    target = next(item for item in catalog.objects if validate_id(item, "DAWN") == target_kind)
    if source_kind == "RES":
        source = write_result(research_tree, catalog.of_type(Source)[0].id).id
    else:
        source = next(
            item
            for item in catalog.objects
            if validate_id(item, "DAWN") == source_kind and item != target
        )
    write_relation(research_tree, source, target, relation_type)
    assert validate_catalog(load_catalog(research_tree)) == []


def test_dangling_invalid_and_plumbing_relation_types_fail(research_tree):
    relation = only(research_tree, "graph/relations")
    value = read_yaml(relation)
    value["target_id"] = new_id("DAWN", "Q")
    write_yaml(relation, value)
    assert any("missing object" in error for error in validate_catalog(load_catalog(research_tree)))

    value["source_id"] = only(research_tree, "graph/sources").stem
    value["target_id"] = only(research_tree, "graph/claims").stem
    value["relation_type"] = "tests"
    write_yaml(relation, value)
    assert any("invalid endpoints" in error for error in validate_catalog(load_catalog(research_tree)))

    value["relation_type"] = "uses"
    write_yaml(relation, value)
    assert any(
        "invalid semantic relation type uses" in error
        for error in validate_catalog(load_catalog(research_tree))
    )


def test_semantic_and_provenance_relation_types_remain_distinct(research_tree):
    path = only(research_tree, "graph/relations")
    value = read_yaml(path)
    value["relation_class"] = "provenance"
    value["relation_type"] = "supports"
    write_yaml(path, value)
    assert any(
        "invalid provenance relation type" in error
        for error in validate_catalog(load_catalog(research_tree))
    )
    value["relation_type"] = "derived_from"
    write_yaml(path, value)
    assert validate_catalog(load_catalog(research_tree)) == []


def test_accepted_relation_requires_explicit_review():
    with pytest.raises(ValidationError, match="requires a reviewer"):
        Relation(
            id=new_id("DAWN", "REL"),
            source_id=new_id("DAWN", "C"),
            target_id=new_id("DAWN", "C"),
            relation_class="semantic",
            relation_type="supports",
            status="accepted",
            asserted_by="github:test",
            asserted_at="2026-09-26T00:00:00Z",
            rationale="Fixture.",
            **COMMON,
        )


def test_readiness_claim_rejected_with_missing_dependency(research_tree):
    catalog = load_catalog(research_tree)
    study = executable_study(catalog)
    path = catalog.paths[study.id]
    value = read_yaml(path)
    value["execution"]["plans"][0]["declared_readiness"] = "local"
    write_yaml(path, value)
    assert any(
        "declared local with missing dependencies" in error
        for error in validate_catalog(load_catalog(research_tree))
    )


def test_validated_provider_requires_completed_verification_run(research_tree):
    path = only(research_tree, "infra/providers")
    value = read_yaml(path)
    value["status"] = "validated"
    write_yaml(path, value)
    assert any(
        "validated provider needs verification Run" in error
        for error in validate_catalog(load_catalog(research_tree))
    )
