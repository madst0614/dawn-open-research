from pathlib import Path

import pytest
from pydantic import ValidationError

from open_research.ids import new_id, validate_id
from open_research.models import Claim, Method, Question, Result, Run, Source, Study
from open_research.store import load_catalog, validate_catalog
from conftest import read_yaml, write_yaml


def only(root: Path, directory: str):
    return next((root / directory).glob("*.yaml"))


def test_offline_ids_are_unique_and_namespace_specific():
    ids = {new_id("OTHER", "ST") for _ in range(300)}
    assert len(ids) == 300
    assert all(validate_id(value, "OTHER", "ST") == "ST" for value in ids)
    with pytest.raises(ValueError):
        validate_id(next(iter(ids)), "DAWN", "ST")
    with pytest.raises(ValueError):
        new_id("DAWN", "UNKNOWN")


def test_question_claim_types_and_method_validate():
    common = {
        "created_by": "github:test",
        "created_at": "2026-09-26T00:00:00Z",
    }
    question = Question(
        id=new_id("DAWN", "Q"),
        title="Open target",
        question="What remains unknown?",
        status="open",
        **common,
    )
    proposition = Claim(
        id=new_id("DAWN", "C"),
        title="Proposition",
        statement="A bounded proposition.",
        claim_type="proposition",
        scope="Fixture scope.",
        status="proposed",
        **common,
    )
    interpretation = Claim(
        id=new_id("DAWN", "C"),
        title="Interpretation",
        statement="A reusable interpretation.",
        claim_type="interpretation",
        scope="Fixture scope.",
        status="tentative",
        **common,
    )
    method = Method(
        id=new_id("DAWN", "M"),
        title="Fixture analysis",
        description="Analyze one bounded fixture.",
        protocol="Apply the specified analysis and retain its outputs.",
        status="specified",
        **common,
    )
    assert question.status == "open"
    assert proposition.claim_type == "proposition"
    assert interpretation.claim_type == "interpretation"
    assert method.status == "specified"


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


def test_supported_claim_requires_reviewed_result_connection(research_tree):
    path = only(research_tree, "graph/claims")
    value = read_yaml(path)
    value["status"] = "supported"
    write_yaml(path, value)
    assert any(
        "requires accepted supporting Result" in error
        for error in validate_catalog(load_catalog(research_tree))
    )


def test_result_requires_real_provenance():
    with pytest.raises(ValidationError, match="requires a Run or Source"):
        Result(
            id=new_id("DAWN", "RES"),
            created_by="github:test",
            created_at="2026-09-26T00:00:00Z",
            title="Observation",
            statement="Measured value.",
            scope="One setting.",
            limitations="Small sample.",
            authors=["github:test"],
        )


def test_result_does_not_change_claim_status(research_tree):
    catalog = load_catalog(research_tree)
    claim = catalog.of_type(Claim)[0]
    source = catalog.of_type(Source)[0]
    result = Result(
        id=new_id("DAWN", "RES"),
        created_by="github:test",
        created_at="2026-09-26T00:00:00Z",
        title="Independent fixture result",
        statement="A bounded outcome was recorded.",
        scope="Fixture only.",
        limitations="Not connected to a Claim.",
        source_ids=[source.id],
        authors=["github:test"],
    )
    write_yaml(
        research_tree / "graph" / "results" / f"{result.id}.yaml",
        result.model_dump(mode="json"),
    )
    reloaded = load_catalog(research_tree)
    assert validate_catalog(reloaded) == []
    assert reloaded.get(claim.id, Claim).status == "proposed"


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


def test_study_explicit_references_must_resolve(research_tree):
    path = only(research_tree, "studies")
    value = read_yaml(path)
    value["question_ids"] = [new_id("DAWN", "Q")]
    write_yaml(path, value)
    assert any("missing Question" in error for error in validate_catalog(load_catalog(research_tree)))


def test_dangling_and_invalid_relation_endpoints(research_tree):
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


def test_invalid_artifact_reference_and_readiness_claim(research_tree):
    study_path = next(
        path for path in (research_tree / "studies").glob("*.yaml") if read_yaml(path).get("entrypoint")
    )
    value = read_yaml(study_path)
    value["requires"]["artifacts"] = [new_id("DAWN", "ART")]
    value["declared_readiness"] = "local"
    write_yaml(study_path, value)
    errors = validate_catalog(load_catalog(research_tree))
    assert any("missing Artifact" in error for error in errors)


def test_readiness_claim_rejected_with_missing_dependency(research_tree):
    study_path = next(
        path for path in (research_tree / "studies").glob("*.yaml") if read_yaml(path).get("entrypoint")
    )
    value = read_yaml(study_path)
    value["declared_readiness"] = "local"
    write_yaml(study_path, value)
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
